from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .dataset import DatasetValidationError


_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
STATUS = "FEATURE_FOUNDATION_MATERIALIZED_WITH_VINTAGE_LIMITATIONS"


def write_e14_feature_foundation(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    readiness_audit_path: str | Path,
    mechanism_contract_path: str | Path,
    source_catalog_path: str | Path,
    foundation_schema_path: str | Path,
    raw_dir: str | Path,
    foundation_output_path: str | Path,
    lock_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path, Path]:
    contract_file, contract_raw, contract = _read_json(contract_path, "foundation contract")
    taxonomy_file, taxonomy_raw, taxonomy = _read_json(taxonomy_path, "taxonomy v5")
    readiness_file, readiness_raw, readiness = _read_json(readiness_audit_path, "readiness audit")
    mechanism_file, mechanism_raw, mechanism = _read_json(mechanism_contract_path, "mechanism contract")
    catalog_file, catalog_raw, catalog = _read_json(source_catalog_path, "source catalog")
    schema_file, schema_raw, schema = _read_json(foundation_schema_path, "foundation schema")
    raw_root = Path(raw_dir).resolve()
    raw_files = {name: raw_root / name for name in contract.get("rawSnapshotHashes", {})}
    _validate_inputs(
        contract, taxonomy, readiness, mechanism, catalog, schema,
        taxonomy_raw, readiness_raw, mechanism_raw, catalog_raw, schema_raw, raw_files,
    )

    outputs = [
        Path(foundation_output_path).resolve(),
        Path(lock_output_path).resolve(),
        Path(audit_output_path).resolve(),
    ]
    if any(path.exists() for path in outputs):
        raise DatasetValidationError("Immutable E14 feature-foundation output already exists.")

    cutoff = date.fromisoformat(contract["cutoffDate"])
    series = [
        _series(
            "e14-vix-monthly-maximum", "cboe-vix-history", "monthly", "Index",
            "monthly-maximum-daily-close", "event-time-observation",
            _monthly_max(raw_files["cboe-vix-history.csv"], "DATE", "CLOSE", "%m/%d/%Y", cutoff),
            "Current official Cboe history frozen by hash; corrections after event time remain possible.",
        ),
        _series(
            "e14-baa10y-monthly-maximum", "fred-baa10y", "monthly", "Percent",
            "monthly-maximum-daily-level", "event-time-observation",
            _monthly_max(raw_files["fred-baa10y.csv"], "observation_date", "BAA10Y", "%Y-%m-%d", cutoff),
            "Current FRED history frozen by hash; not an ALFRED vintage and subject to correction risk.",
        ),
        _series(
            "e14-tedrate-monthly-maximum", "fred-tedrate", "monthly", "Percent",
            "monthly-maximum-daily-level", "event-time-observation",
            _monthly_max(raw_files["fred-tedrate.csv"], "observation_date", "TEDRATE", "%Y-%m-%d", cutoff),
            "LIBOR-era series ends in January 2022; later months remain absent and are never SOFR-filled.",
        ),
        _series(
            "e14-dtwexb-monthly-maximum-absolute-change", "fred-dtwexb", "monthly",
            "Index points", "monthly-maximum-absolute-daily-change", "event-time-observation",
            _monthly_max_absolute_change(
                raw_files["fred-dtwexb.csv"], "observation_date", "DTWEXB", cutoff
            ),
            "Goods-only index ends in December 2019; the successor series is not silently spliced.",
        ),
        _series(
            "e14-fdic-noncurrent-loan-rate-quarterly", "fdic-quarterly-financials",
            "quarterly", "Percent", "all-insured-noncurrent-loan-rate",
            "release-archived-current-workbook",
            _fdic_noncurrent_rate(raw_files["fdic-qbp-timeseries-2025q4.xlsx"], cutoff),
            "Q4 2025 aggregate workbook is a refreshed current-history snapshot; availability uses a conservative 60-day lag and is not an exact vintage archive.",
        ),
    ]
    counts = {item["seriesId"]: item["observationCount"] for item in series}
    if counts != contract["expectedObservationCounts"]:
        raise DatasetValidationError("E14 feature observation counts differ from the frozen contract.")

    bindings = [
        _binding("e14-broad-market-repricing-detector", "broad-market-repricing", "cboe-vix-history", "e14-vix-monthly-maximum", "causal-rolling-percentile"),
        _binding("e14-broad-market-repricing-detector", "broad-market-repricing", "fred-baa10y", "e14-baa10y-monthly-maximum", "causal-rolling-percentile"),
        _binding("e14-funding-liquidity-detector", "funding-liquidity", "fred-tedrate", "e14-tedrate-monthly-maximum", "causal-robust-z-score"),
        _binding("e14-banking-credit-detector", "banking-credit", "fdic-quarterly-financials", "e14-fdic-noncurrent-loan-rate-quarterly", "causal-robust-z-score"),
        _binding("e14-banking-credit-detector", "banking-credit", "fred-baa10y", "e14-baa10y-monthly-maximum", "causal-rolling-percentile"),
        _binding("e14-cross-border-growth-detector", "cross-border-growth", "fred-dtwexb", "e14-dtwexb-monthly-maximum-absolute-change", "causal-rolling-percentile"),
    ]
    raw_snapshots = [
        {
            **_artifact(raw_files[name], raw_files[name].read_bytes()),
            "sourceUrl": _source_url(name),
            "retrievedOn": contract["frozenAt"],
        }
        for name in sorted(raw_files)
    ]
    foundation = {
        "schemaVersion": 1,
        "artifactType": "E14MechanismFeatureFoundation",
        "foundationId": "e14-mechanism-feature-foundation-v1",
        "status": "materialized-with-vintage-limitations",
        "cutoffDate": contract["cutoffDate"],
        "taxonomy": _artifact(taxonomy_file, taxonomy_raw),
        "rawSnapshots": raw_snapshots,
        "series": series,
        "detectorBindings": bindings,
        "missingnessPolicy": {
            "missingValuesRemainAbsent": True,
            "zeroImputationForbidden": True,
            "tedrateAfter2022January": "not-applicable-methodology-regime",
            "dtwexbAfter2019December": "not-applicable-methodology-regime",
            "preCoveragePeriods": "unavailable-not-zero",
            "fdicAvailability": "quarter-end-plus-conservative-60-day-release-lag",
        },
        "limitations": [
            "FRED daily financial histories are frozen current-history snapshots, not ALFRED point-in-time vintages.",
            "The FDIC workbook refreshes historical aggregates; the 60-day release lag prevents look-ahead but does not reconstruct exact historical revisions.",
            "TEDRATE and DTWEXB stop at their documented methodology boundaries and are not spliced to successor series.",
            "Materialization authorizes protocol design only; transforms remain inner-fit and no candidate is generated here.",
        ],
    }
    foundation_raw = _json_bytes(foundation)
    lock = {
        "schemaVersion": 1,
        "artifactType": "E14MechanismFeatureFoundationLock",
        "lockId": "e14-mechanism-feature-foundation-lock-v1",
        "status": STATUS,
        "cutoffDate": contract["cutoffDate"],
        "foundation": _artifact(outputs[0], foundation_raw),
        "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
        "rawSnapshotHashes": contract["rawSnapshotHashes"],
        "seriesObservationCounts": counts,
        "detectorBindingCount": len(bindings),
        "strictVintageReady": False,
        "researchProtocolDesignAuthorized": True,
        "candidateGenerationAuthorized": False,
        "outerOosAuthorized": False,
    }
    lock_raw = _json_bytes(lock)
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14MechanismFeatureFoundationAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(contract_file, contract_raw),
            "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
            "candidateReadinessAudit": _artifact(readiness_file, readiness_raw),
            "mechanismContract": _artifact(mechanism_file, mechanism_raw),
            "sourceCatalog": _artifact(catalog_file, catalog_raw),
            "foundationSchema": _artifact(schema_file, schema_raw),
            "rawSnapshots": raw_snapshots,
        },
        "outputs": {
            "foundation": _artifact(outputs[0], foundation_raw),
            "lock": _artifact(outputs[1], lock_raw),
        },
        "inventory": {
            "uniqueSeriesCount": len(series),
            "detectorBindingCount": len(bindings),
            "totalObservationCount": sum(counts.values()),
            "seriesObservationCounts": counts,
            "observationsAfterCutoff": 0,
        },
        "checks": {
            "allRawSnapshotsHashBound": True,
            "taxonomyV5HashBound": True,
            "allSixDetectorBindingsMaterialized": len(bindings) == 6,
            "allFourMechanismsCovered": {item["mechanism"] for item in bindings}
            == set(contract["requiredMechanisms"]),
            "missingnessExplicit": True,
            "zeroImputationAbsent": True,
            "tedrateNotSpliced": True,
            "dtwexbNotSpliced": True,
            "fdicReleaseLagApplied": True,
            "currentHistoryRevisionRiskExplicit": True,
            "candidateGenerationClosed": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "candidateGenerated": False,
            "outerFeatureRowCountUsed": 0,
            "taxonomyMutated": False,
            "promotionPerformed": False,
        },
        "decision": {
            "featureFoundationMaterialized": True,
            "allDetectorBindingsPopulated": True,
            "strictVintageReady": False,
            "taxonomyV5ProtocolDesignAuthorized": True,
            "candidateGenerationAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_feature_foundation",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return (
        _write_new_bytes(outputs[0], foundation_raw, "feature foundation"),
        _write_new_bytes(outputs[1], lock_raw, "feature foundation lock"),
        _write_new_bytes(outputs[2], _json_bytes(audit), "feature foundation audit"),
    )


def _validate_inputs(
    contract: Any, taxonomy: Any, readiness: Any, mechanism: Any, catalog: Any,
    schema: Any, taxonomy_raw: bytes, readiness_raw: bytes, mechanism_raw: bytes,
    catalog_raw: bytes, schema_raw: bytes, raw_files: dict[str, Path],
) -> None:
    input_hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "candidateReadinessAuditSha256": hashlib.sha256(readiness_raw).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_raw).hexdigest(),
        "sourceCatalogSha256": hashlib.sha256(catalog_raw).hexdigest(),
        "foundationSchemaSha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    raw_hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in raw_files.items() if path.is_file()
    }
    expected_policy = {
        "rawSnapshotsHashBound": True,
        "outputsWriteOnce": True,
        "observationsAfterCutoffForbidden": True,
        "missingValuesRemainAbsent": True,
        "zeroImputationForbidden": True,
        "crossMethodologySplicingForbidden": True,
        "dailyLevelAggregation": "monthly-maximum",
        "dtwexbAggregation": "monthly-maximum-absolute-daily-change",
        "fdicMetric": "Percent of Loans and Leases Noncurrent - All Insured Institutions",
        "fdicConservativeReleaseLagDays": 60,
        "currentHistoryRevisionRiskExplicit": True,
        "diagnosticCompositeInputsForbidden": True,
    }
    expected_auth = {
        "featureFoundationMaterializationAuthorized": True,
        "taxonomyV5ProtocolDesignAuthorized": True,
        "candidateGenerationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
        "taxonomyMutationAuthorized": False,
    }
    proposal_pairs = {
        (detector["mechanism"], feature["sourceId"])
        for detector in mechanism.get("detectors", [])
        for feature in detector.get("featureProposals", [])
    }
    required_pairs = {
        ("broad-market-repricing", "cboe-vix-history"),
        ("broad-market-repricing", "fred-baa10y"),
        ("funding-liquidity", "fred-tedrate"),
        ("banking-credit", "fdic-quarterly-financials"),
        ("banking-credit", "fred-baa10y"),
        ("cross-border-growth", "fred-dtwexb"),
    }
    if (
        contract.get("contractId") != "e14-mechanism-feature-foundation-contract-v1"
        or contract.get("inputHashes") != input_hashes
        or contract.get("rawSnapshotHashes") != raw_hashes
        or contract.get("materializationPolicy") != expected_policy
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or readiness.get("status") != "CANDIDATE_READINESS_BLOCKED_FOUNDATION_AND_PROTOCOL"
        or "FEATURE_FOUNDATION_NOT_MATERIALIZED" not in readiness.get("blockers", [])
        or readiness.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or mechanism.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or proposal_pairs != required_pairs
        or catalog.get("catalogId") != "e14-historical-source-catalog-v1"
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-mechanism-feature-foundation-v1.json"
    ):
        raise DatasetValidationError("E14 feature-foundation inputs or contract are invalid.")


def _series(
    series_id: str, source_id: str, frequency: str, unit: str, aggregation: str,
    as_of_class: str, observations: list[dict[str, Any]], limitation: str,
) -> dict[str, Any]:
    return {
        "seriesId": series_id,
        "sourceId": source_id,
        "frequency": frequency,
        "unit": unit,
        "aggregation": aggregation,
        "asOfClass": as_of_class,
        "coverageFrom": observations[0]["period"],
        "coverageTo": observations[-1]["period"],
        "observationCount": len(observations),
        "limitation": limitation,
        "observations": observations,
    }


def _binding(
    detector_id: str, mechanism: str, source_id: str, series_id: str, transform: str,
) -> dict[str, str]:
    return {
        "detectorId": detector_id,
        "mechanism": mechanism,
        "sourceId": source_id,
        "seriesId": series_id,
        "transform": transform,
        "status": "populated-manifested",
        "fitScope": "inner-only",
    }


def _source_url(name: str) -> str:
    return {
        "cboe-vix-history.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
        "fred-baa10y.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAA10Y",
        "fred-tedrate.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TEDRATE",
        "fred-dtwexb.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXB",
        "fdic-qbp-timeseries-2025q4.xlsx": "https://www.fdic.gov/quarterly-banking-profile/qbp-time-series-spreadsheet-fourth-quarter-2025.xlsx",
    }[name]


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _write_new_bytes(path: Path, raw: bytes, label: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E14 {label} already exists: '{path}'.") from exc
    return path


def _xlsx_rows(path: str | Path, sheet_name: str) -> list[dict[int, str | float]]:
    with zipfile.ZipFile(path) as archive:
        shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        shared = ["".join(item.itertext()) for item in shared_root.findall(f"{_XLSX_NS}si")]
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships
        }
        sheets = workbook.find(f"{_XLSX_NS}sheets", {})
        if sheets is None:
            raise DatasetValidationError("FDIC workbook sheet inventory is missing.")
        sheet = next(
            (item for item in sheets
             if item.attrib.get("name") == sheet_name),
            None,
        )
        if sheet is None:
            raise DatasetValidationError(f"FDIC workbook sheet is missing: '{sheet_name}'.")
        target = targets[sheet.attrib[f"{_REL_NS}id"]].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        root = ElementTree.fromstring(archive.read(target))

    rows: list[dict[int, str | float]] = []
    for row in root.findall(f".//{_XLSX_NS}row"):
        values: dict[int, str | float] = {}
        for cell in row.findall(f"{_XLSX_NS}c"):
            raw = cell.find(f"{_XLSX_NS}v")
            if raw is None or raw.text is None:
                continue
            column = _column_number(cell.attrib["r"])
            if cell.attrib.get("t") == "s":
                values[column] = shared[int(raw.text)]
            else:
                try:
                    values[column] = float(raw.text)
                except ValueError:
                    values[column] = raw.text
        rows.append(values)
    return rows


def _column_number(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference)
    if not letters:
        raise DatasetValidationError(f"Invalid XLSX cell reference '{reference}'.")
    result = 0
    for char in letters.group(0):
        result = result * 26 + ord(char) - ord("A") + 1
    return result


def _monthly_max(
    path: str | Path,
    date_field: str,
    value_field: str,
    date_format: str,
    cutoff: date,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[tuple[date, float]]] = defaultdict(list)
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            try:
                day = datetime.strptime(item[date_field], date_format).date()
                value = float(item[value_field])
            except (KeyError, TypeError, ValueError):
                continue
            if day <= cutoff:
                buckets[day.strftime("%Y-%m-01")].append((day, value))
    result = []
    for month, values in sorted(buckets.items()):
        observation_day, maximum = max(values, key=lambda item: (item[1], item[0]))
        result.append({
            "period": month,
            "observationDate": observation_day.isoformat(),
            "availableOn": observation_day.isoformat(),
            "value": round(maximum, 8),
        })
    return result


def _monthly_max_absolute_change(
    path: str | Path,
    date_field: str,
    value_field: str,
    cutoff: date,
) -> list[dict[str, Any]]:
    values: list[tuple[date, float]] = []
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            try:
                day = date.fromisoformat(item[date_field])
                value = float(item[value_field])
            except (KeyError, TypeError, ValueError):
                continue
            if day <= cutoff:
                values.append((day, value))
    buckets: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for previous, current in zip(values, values[1:]):
        day, value = current
        buckets[day.strftime("%Y-%m-01")].append((day, abs(value - previous[1])))
    result = []
    for month, changes in sorted(buckets.items()):
        observation_day, maximum = max(changes, key=lambda item: (item[1], item[0]))
        result.append({
            "period": month,
            "observationDate": observation_day.isoformat(),
            "availableOn": observation_day.isoformat(),
            "value": round(maximum, 8),
        })
    return result


def _fdic_noncurrent_rate(path: str | Path, cutoff: date) -> list[dict[str, Any]]:
    rows = _xlsx_rows(path, "Ratios by Asset Size Groups")
    section_index = next(
        (index for index, row in enumerate(rows)
         if row.get(2) == "Percent of Loans and Leases Noncurrent"),
        None,
    )
    if section_index is None:
        raise DatasetValidationError("FDIC noncurrent-loan section is missing.")
    header = next(
        (row for row in rows[section_index + 1:] if row.get(2) == "Asset Size Group"),
        None,
    )
    all_insured = next(
        (row for row in rows[section_index + 1:] if row.get(2) == "All Insured Institutions"),
        None,
    )
    if header is None or all_insured is None:
        raise DatasetValidationError("FDIC aggregate noncurrent-loan table is incomplete.")
    result = []
    for column, period in header.items():
        if column <= 2 or not isinstance(period, str) or not re.fullmatch(r"\d{4}Q[1-4]", period):
            continue
        value = all_insured.get(column)
        if not isinstance(value, float):
            continue
        year, quarter = int(period[:4]), int(period[-1])
        end_month = quarter * 3
        next_month = date(year + (end_month == 12), 1 if end_month == 12 else end_month + 1, 1)
        quarter_end = next_month - timedelta(days=1)
        available_on = quarter_end + timedelta(days=60)
        if available_on <= cutoff:
            result.append({
                "period": period,
                "observationDate": quarter_end.isoformat(),
                "availableOn": available_on.isoformat(),
                "value": round(value, 8),
            })
    return result
