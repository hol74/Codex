from __future__ import annotations

import calendar
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = (
    "FEATURE_FOUNDATION_V2_MATERIALIZED_RESEARCH_ONLY_REVISION_LIMITATIONS_"
    "CANDIDATE_GENERATION_CLOSED"
)
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]
ACTIVE_SERIES = {
    "banking-credit": ["e14-fdic-failed-assisted-assets-monthly"],
    "broad-market-repricing": [
        "e14-vix-monthly-maximum",
        "e14-baa10y-monthly-maximum",
    ],
    "cross-border-growth": ["e14-twexbmth-monthly-absolute-change"],
    "funding-liquidity": ["e14-fedfunds-minus-tbill-monthly"],
}


def write_e14_feature_foundation_v2(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    foundation_v1_path: str | Path,
    foundation_lock_v1_path: str | Path,
    repair_plan_path: str | Path,
    repair_audit_path: str | Path,
    foundation_schema_v2_path: str | Path,
    raw_dir: str | Path,
    foundation_output_path: str | Path,
    lock_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path, Path]:
    contract_file, contract_raw, contract = _read(contract_path, "foundation v2 contract")
    taxonomy_file, taxonomy_raw, taxonomy = _read(taxonomy_path, "taxonomy v5")
    base_file, base_raw, base = _read(foundation_v1_path, "feature foundation v1")
    base_lock_file, base_lock_raw, base_lock = _read(
        foundation_lock_v1_path, "feature foundation lock v1"
    )
    plan_file, plan_raw, plan = _read(repair_plan_path, "coverage repair plan")
    repair_file, repair_raw, repair = _read(repair_audit_path, "coverage repair audit")
    schema_file, schema_raw, schema = _read(
        foundation_schema_v2_path, "feature foundation schema v2"
    )
    raw_root = Path(raw_dir).resolve()
    raw_files = {name: raw_root / name for name in contract.get("rawSnapshotHashes", {})}
    _validate_inputs(
        contract,
        taxonomy,
        base,
        base_lock,
        plan,
        repair,
        schema,
        taxonomy_raw,
        base_raw,
        base_lock_raw,
        plan_raw,
        repair_raw,
        schema_raw,
        raw_files,
    )

    outputs = [
        Path(foundation_output_path).resolve(),
        Path(lock_output_path).resolve(),
        Path(audit_output_path).resolve(),
    ]
    if any(path.exists() for path in outputs):
        raise DatasetValidationError("Immutable E14 feature-foundation v2 output already exists.")

    cutoff = date.fromisoformat(contract["cutoffDate"])
    fdic_observations, fdic_diagnostic = _fdic_monthly_assets(
        raw_files["fdic-failures-assistance.json"], cutoff
    )
    twex_observations, twex_diagnostic = _fred_absolute_monthly_change(
        raw_files["fred-twexbmth.csv"], "TWEXBMTH", cutoff
    )
    funding_observations, funding_diagnostic = _fred_negated_monthly(
        raw_files["fred-tb3smffm.csv"], "TB3SMFFM", cutoff
    )

    base_by_id = {item["seriesId"]: item for item in base["series"]}
    carried_ids = ["e14-vix-monthly-maximum", "e14-baa10y-monthly-maximum"]
    series = [deepcopy(base_by_id[item]) for item in carried_ids]
    for item in series:
        item["missingObservationCount"] = sum(
            observation.get("value") is None for observation in item["observations"]
        )
    series.extend([
        _series(
            "e14-fdic-failed-assisted-assets-monthly",
            "fdic-bank-failures-and-assistance",
            "USD thousands",
            "monthly-sum-qbfasset-by-faildate-with-explicit-missing-months",
            "current-complete-registry-snapshot",
            fdic_observations,
            "Resolution transactions are lagging outcomes; 69 calendar months containing at least one transaction with missing QBFASSET remain missing, never zero.",
        ),
        _series(
            "e14-twexbmth-monthly-absolute-change",
            "fred-twexbmth",
            "Index points",
            "absolute-month-over-month-change",
            "current-history-snapshot",
            twex_observations,
            "TWEXBMTH ends in December 2019 and is not spliced to a successor series.",
        ),
        _series(
            "e14-fedfunds-minus-tbill-monthly",
            "fred-tb3smffm",
            "Percentage points",
            "negate-treasury-bill-minus-effective-federal-funds-rate",
            "current-history-snapshot",
            funding_observations,
            "This is not a TED substitute; the Treasury input source changed in 2019 and the boundary remains explicit.",
        ),
    ])
    counts = {item["seriesId"]: item["observationCount"] for item in series}
    missing_counts = {item["seriesId"]: item["missingObservationCount"] for item in series}
    if counts != contract["expectedObservationCounts"]:
        raise DatasetValidationError("E14 foundation v2 observation counts differ from contract.")
    if missing_counts != contract["expectedMissingObservationCounts"]:
        raise DatasetValidationError("E14 foundation v2 missingness differs from contract.")

    active_bindings = [
        _binding("e14-broad-market-repricing-detector", "broad-market-repricing", "cboe-vix-history", "e14-vix-monthly-maximum", "causal-rolling-percentile", "carried-forward-hash-bound"),
        _binding("e14-broad-market-repricing-detector", "broad-market-repricing", "fred-baa10y", "e14-baa10y-monthly-maximum", "causal-rolling-percentile", "carried-forward-hash-bound"),
        _binding("e14-banking-credit-detector-v2", "banking-credit", "fdic-bank-failures-and-assistance", "e14-fdic-failed-assisted-assets-monthly", "causal-rolling-percentile", "populated-manifested-v2"),
        _binding("e14-cross-border-growth-detector-v2", "cross-border-growth", "fred-twexbmth", "e14-twexbmth-monthly-absolute-change", "causal-rolling-percentile", "populated-manifested-v2"),
        _binding("e14-funding-liquidity-detector-v2", "funding-liquidity", "fred-tb3smffm", "e14-fedfunds-minus-tbill-monthly", "causal-rolling-percentile", "populated-manifested-v2"),
    ]
    retired = [
        {
            **deepcopy(item),
            "status": "retired-structural-coverage-v1",
            "retirementReason": "replaced-by-preregistered-standalone-v2-series",
        }
        for item in base["detectorBindings"]
        if item["mechanism"] != "broad-market-repricing"
    ]

    structural = _structural_coverage(taxonomy, series, contract["materializationPolicy"]["minimumHistoryMonths"])
    actual_coverage = {
        mechanism: {
            "positive": item["observablePositiveEpisodeCount"],
            "hardNegative": item["observableHardNegativeEpisodeCount"],
        }
        for mechanism, item in structural.items()
    }
    if actual_coverage != contract["expectedStructuralCoverage"]:
        raise DatasetValidationError("E14 foundation v2 structural coverage differs from contract.")

    diagnostics = {
        "fdicRegistry": fdic_diagnostic,
        "twexbmthMethodologyEnd": twex_diagnostic,
        "tb3smffm2019Boundary": funding_diagnostic,
        "revisionSensitivity": {
            "snapshotClass": "current-history-not-point-in-time-vintage",
            "historicalVintageComparisonAvailable": False,
            "researchMaterializationPassed": True,
            "strictVintageReady": False,
            "candidateGenerationPassed": False,
            "reason": "No hash-bound prior official vintages are available in the preregistered inputs; revision risk is explicit and must remain in the next readiness gate.",
        },
        "structuralCoverage": structural,
    }
    raw_snapshots = [
        {
            **_artifact(raw_files[name], raw_files[name].read_bytes()),
            "sourceUrl": contract["sourceSnapshotUrls"][name],
            "retrievedOn": contract["frozenAt"],
        }
        for name in sorted(raw_files)
    ]
    foundation = {
        "schemaVersion": 2,
        "artifactType": "E14MechanismFeatureFoundation",
        "foundationId": "e14-mechanism-feature-foundation-v2",
        "status": "materialized-research-only-with-revision-limitations",
        "cutoffDate": contract["cutoffDate"],
        "baseFoundation": _artifact(base_file, base_raw),
        "taxonomy": _artifact(taxonomy_file, taxonomy_raw),
        "rawSnapshots": raw_snapshots,
        "series": series,
        "detectorBindings": active_bindings,
        "retiredDetectorBindings": retired,
        "missingnessPolicy": {
            "missingValuesRemainAbsent": True,
            "zeroImputationForbidden": True,
            "fdicObservedZero": "only when the complete API inventory contains no transaction in the calendar month",
            "fdicMissingQbfasset": "month-remains-missing-even-if-other-transactions-have-assets",
            "twexbmthAfter2019December": "not-applicable-methodology-regime",
            "preCoveragePeriods": "unavailable-not-zero",
        },
        "diagnostics": diagnostics,
        "limitations": [
            "Foundation v1 remains immutable; only its two broad-market series are carried forward by exact content.",
            "All three replacement sources are current-history snapshots, not point-in-time vintage archives.",
            "FDIC failed/assisted assets are a lagging resolution outcome and 69 months have explicit source-value missingness.",
            "TWEXBMTH is not extended after December 2019 and TB3SMFFM retains an explicit 2019 source boundary.",
            "Materialization repairs structural episode coverage but does not authorize candidate generation, fitting, evaluation or outer OOS.",
        ],
    }
    foundation_raw = _json_bytes(foundation)
    lock = {
        "schemaVersion": 2,
        "artifactType": "E14MechanismFeatureFoundationLock",
        "lockId": "e14-mechanism-feature-foundation-lock-v2",
        "status": STATUS,
        "cutoffDate": contract["cutoffDate"],
        "foundation": _artifact(outputs[0], foundation_raw),
        "baseFoundationV1": _artifact(base_file, base_raw),
        "baseFoundationLockV1": _artifact(base_lock_file, base_lock_raw),
        "rawSnapshotHashes": contract["rawSnapshotHashes"],
        "seriesObservationCounts": counts,
        "seriesMissingObservationCounts": missing_counts,
        "structuralCoverage": actual_coverage,
        "activeDetectorBindingCount": len(active_bindings),
        "retiredDetectorBindingCount": len(retired),
        "strictVintageReady": False,
        "structuralCoverageReady": True,
        "researchFoundationReady": True,
        "candidateGenerationAuthorized": False,
        "candidateFittingAuthorized": False,
        "outerOosAuthorized": False,
    }
    lock_raw = _json_bytes(lock)
    audit = {
        "schemaVersion": 2,
        "artifactType": "E14MechanismFeatureFoundationAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(contract_file, contract_raw),
            "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
            "featureFoundationV1": _artifact(base_file, base_raw),
            "featureFoundationLockV1": _artifact(base_lock_file, base_lock_raw),
            "coverageRepairPlan": _artifact(plan_file, plan_raw),
            "coverageRepairAudit": _artifact(repair_file, repair_raw),
            "foundationSchemaV2": _artifact(schema_file, schema_raw),
            "rawSnapshots": raw_snapshots,
        },
        "outputs": {
            "foundationV2": _artifact(outputs[0], foundation_raw),
            "foundationLockV2": _artifact(outputs[1], lock_raw),
        },
        "inventory": {
            "activeSeriesCount": len(series),
            "activeDetectorBindingCount": len(active_bindings),
            "retiredDetectorBindingCount": len(retired),
            "totalObservationCount": sum(counts.values()),
            "totalMissingObservationCount": sum(missing_counts.values()),
            "seriesObservationCounts": counts,
            "seriesMissingObservationCounts": missing_counts,
            "observationsAfterCutoff": 0,
        },
        "diagnostics": diagnostics,
        "checks": {
            "allInputAndRawHashesExact": True,
            "foundationV1UnmodifiedAndHashBound": True,
            "onlyBroadSeriesCarriedForward": True,
            "threeReplacementSeriesMaterialized": True,
            "fdicApiInventoryComplete": fdic_diagnostic["apiInventoryComplete"],
            "fdicMissingAssetsExplicit": fdic_diagnostic["missingAssetMonths"] == 69,
            "fdicObservedZerosValidated": fdic_diagnostic["observedZeroPolicyPassed"],
            "twexbmthNotSpliced": twex_diagnostic["notSpliced"],
            "tb3smffmBoundaryExplicit": funding_diagnostic["boundaryDiagnosticPassed"],
            "actualStructuralCoverageReady": all(item["structurallyReady"] for item in structural.values()),
            "strictVintageReady": False,
            "candidateGenerationClosed": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "candidateGenerated": False,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "candidateRanked": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "decision": {
            "featureFoundationV2Materialized": True,
            "foundationV1Mutated": False,
            "structuralCoverageRepaired": True,
            "revisionRiskClearedForStrictVintageUse": False,
            "researchFoundationReady": True,
            "candidateGenerationAuthorized": False,
            "candidateFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_feature_foundation_v2",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return (
        _write_new_bytes(outputs[0], foundation_raw, "feature foundation v2"),
        _write_new_bytes(outputs[1], lock_raw, "feature foundation lock v2"),
        _write_new_bytes(outputs[2], _json_bytes(audit), "feature foundation audit v2"),
    )


def _validate_inputs(
    contract: dict[str, Any], taxonomy: dict[str, Any], base: dict[str, Any],
    base_lock: dict[str, Any], plan: dict[str, Any], repair: dict[str, Any],
    schema: dict[str, Any], taxonomy_raw: bytes, base_raw: bytes,
    base_lock_raw: bytes, plan_raw: bytes, repair_raw: bytes, schema_raw: bytes,
    raw_files: dict[str, Path],
) -> None:
    hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "featureFoundationV1Sha256": hashlib.sha256(base_raw).hexdigest(),
        "featureFoundationLockV1Sha256": hashlib.sha256(base_lock_raw).hexdigest(),
        "coverageRepairPlanSha256": hashlib.sha256(plan_raw).hexdigest(),
        "coverageRepairAuditSha256": hashlib.sha256(repair_raw).hexdigest(),
        "foundationSchemaV2Sha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    raw_hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in raw_files.items() if path.is_file()
    }
    expected_auth = {
        "featureFoundationV2MaterializationAuthorized": True,
        "foundationV1MutationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "candidateFittingAuthorized": False,
        "candidateEvaluationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    policy = contract.get("materializationPolicy", {})
    required_policy = {
        "rawSnapshotsHashBound": True,
        "outputsWriteOnce": True,
        "foundationV1HashBoundAndImmutable": True,
        "carryForwardOnlyBroadSeries": True,
        "observationsAfterCutoffForbidden": True,
        "missingValuesRemainAbsent": True,
        "zeroImputationForbidden": True,
        "fdicObservedZeroRequiresCompleteApiInventoryAndNoTransactionInMonth": True,
        "fdicMissingAssetTransactionMakesCalendarMonthMissing": True,
        "crossMethodologySplicingForbidden": True,
        "twexbmthAggregation": "absolute-month-over-month-change",
        "tb3smffmAggregation": "negate-monthly-level",
        "minimumHistoryMonths": 60,
        "currentHistoryRevisionRiskExplicit": True,
        "revisionComparisonUnavailableKeepsStrictVintageFalse": True,
        "tb3smffm2019BoundaryDiagnosticRequired": True,
    }
    if (
        contract.get("contractId") != "e14-mechanism-feature-foundation-contract-v2"
        or contract.get("inputHashes") != hashes
        or contract.get("rawSnapshotHashes") != raw_hashes
        or policy != required_policy
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or base.get("foundationId") != "e14-mechanism-feature-foundation-v1"
        or base_lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v1"
        or base_lock.get("foundation", {}).get("sha256") != hashes["featureFoundationV1Sha256"]
        or plan.get("planId") != "e14-structural-coverage-repair-plan-v1"
        or repair.get("status") != "STRUCTURAL_COVERAGE_REPAIR_PREREGISTERED_MATERIALIZATION_REQUIRED"
        or repair.get("decision", {}).get("sourceMaterializationAuthorized") is not True
        or repair.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-mechanism-feature-foundation-v2.json"
    ):
        raise DatasetValidationError("E14 feature-foundation v2 inputs or contract are invalid.")


def _fdic_monthly_assets(path: Path, cutoff: date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        payload = json.loads(path.read_bytes())
        rows = [item["data"] for item in payload["data"]]
        meta = payload["meta"]
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError("FDIC failure snapshot is invalid.") from exc
    total = int(meta.get("total", -1))
    limit = int(meta.get("parameters", {}).get("limit", 0))
    ids = [str(item.get("ID")) for item in rows]
    inventory_complete = total == len(rows) and limit >= total and len(ids) == len(set(ids))
    if not inventory_complete:
        raise DatasetValidationError("FDIC API inventory is incomplete or duplicated.")

    parsed: list[tuple[date, dict[str, Any]]] = []
    for row in rows:
        try:
            day = datetime.strptime(row["FAILDATE"], "%m/%d/%Y").date()
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError("FDIC failure date is invalid.") from exc
        parsed.append((day, row))
    eligible = [(day, row) for day, row in parsed if day <= cutoff]
    buckets: dict[str, list[tuple[date, dict[str, Any]]]] = defaultdict(list)
    for day, row in eligible:
        buckets[day.strftime("%Y-%m-01")].append((day, row))

    observations = []
    current = date(1934, 1, 1)
    end = cutoff.replace(day=1)
    while current <= end:
        period = current.isoformat()
        transactions = buckets.get(period, [])
        missing = [item for _, item in transactions if item.get("QBFASSET") is None]
        month_end = date(current.year, current.month, calendar.monthrange(current.year, current.month)[1])
        if missing:
            value = None
            status = "missing-source-value"
        elif transactions:
            value = round(sum(float(item["QBFASSET"]) for _, item in transactions), 8)
            status = "observed-transaction-sum"
        else:
            value = 0.0
            status = "observed-zero-complete-registry"
        observations.append({
            "period": period,
            "observationDate": month_end.isoformat(),
            "availableOn": month_end.isoformat(),
            "value": value,
            "observationStatus": status,
            "transactionCount": len(transactions),
            "missingAssetTransactionCount": len(missing),
        })
        current = _add_months(current, 1)

    missing_rows = [(day, row) for day, row in eligible if row.get("QBFASSET") is None]
    missing_months = sum(item["value"] is None for item in observations)
    return observations, {
        "apiReportedTotal": total,
        "downloadedRecordCount": len(rows),
        "recordsOnOrBeforeCutoff": len(eligible),
        "recordsAfterCutoffExcluded": len(rows) - len(eligible),
        "duplicateIdCount": len(ids) - len(set(ids)),
        "apiIndexName": meta.get("index", {}).get("name"),
        "apiIndexCreateTimestamp": meta.get("index", {}).get("createTimestamp"),
        "apiInventoryComplete": True,
        "missingAssetTransactionCount": len(missing_rows),
        "missingAssetMonths": missing_months,
        "lastMissingAssetTransactionDate": max(day for day, _ in missing_rows).isoformat(),
        "observedZeroMonthCount": sum(item["observationStatus"] == "observed-zero-complete-registry" for item in observations),
        "observedZeroPolicyPassed": True,
        "laggingOutcomeRiskExplicit": True,
    }


def _fred_absolute_monthly_change(
    path: Path, field: str, cutoff: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    levels = _fred_monthly_levels(path, field, cutoff)
    _require_consecutive(levels, field)
    observations = []
    for previous, current in zip(levels, levels[1:]):
        period, value = current
        observations.append(_monthly_observation(period, abs(value - previous[1])))
    return observations, {
        "rawLevelCount": len(levels),
        "derivedObservationCount": len(observations),
        "coverageFrom": observations[0]["period"],
        "coverageTo": observations[-1]["period"],
        "missingMonthCount": 0,
        "methodologyEnd": "2019-12-01",
        "notSpliced": observations[-1]["period"] == "2019-12-01",
        "boundaryDiagnosticPassed": observations[-1]["period"] == "2019-12-01",
    }


def _fred_negated_monthly(
    path: Path, field: str, cutoff: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    levels = _fred_monthly_levels(path, field, cutoff)
    _require_consecutive(levels, field)
    observations = [_monthly_observation(period, -value) for period, value in levels]
    pre = [item["value"] for item in observations if item["period"] < "2019-01-01"]
    post = [item["value"] for item in observations if item["period"] >= "2019-01-01"]
    return observations, {
        "coverageFrom": observations[0]["period"],
        "coverageTo": observations[-1]["period"],
        "missingMonthCount": 0,
        "boundaryMonth": "2019-01-01",
        "preBoundary": _summary(pre),
        "postBoundary": _summary(post),
        "minimumSegmentMonths": min(len(pre), len(post)),
        "boundaryDiagnosticPassed": min(len(pre), len(post)) >= 24,
        "distributionEquivalenceClaimed": False,
        "sensitivityRequirement": "future inner evaluation must report results with and without post-2018 observations",
    }


def _fred_monthly_levels(path: Path, field: str, cutoff: date) -> list[tuple[date, float]]:
    output = []
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                day = date.fromisoformat(row["observation_date"])
                raw = row[field]
                if day <= cutoff and raw not in ("", ".", "NA"):
                    output.append((day.replace(day=1), float(raw)))
    except (OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"FRED monthly snapshot '{field}' is invalid.") from exc
    if not output:
        raise DatasetValidationError(f"FRED monthly snapshot '{field}' is empty.")
    return sorted(output)


def _require_consecutive(values: list[tuple[date, float]], field: str) -> None:
    if any(_add_months(left[0], 1) != right[0] for left, right in zip(values, values[1:])):
        raise DatasetValidationError(f"FRED monthly snapshot '{field}' has gaps.")


def _monthly_observation(period: date, value: float) -> dict[str, Any]:
    return {
        "period": period.isoformat(),
        "observationDate": period.isoformat(),
        "availableOn": _add_months(period, 1).isoformat(),
        "value": round(value, 8),
        "observationStatus": "observed-current-history",
    }


def _summary(values: list[float]) -> dict[str, Any]:
    ordered = sorted(values)
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 8),
        "median": round(statistics.median(values), 8),
        "populationStdDev": round(statistics.pstdev(values), 8),
        "p10": round(ordered[max(0, int(len(ordered) * 0.10) - 1)], 8),
        "p90": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.90))], 8),
    }


def _series(
    series_id: str, source_id: str, unit: str, aggregation: str,
    as_of_class: str, observations: list[dict[str, Any]], limitation: str,
) -> dict[str, Any]:
    return {
        "seriesId": series_id,
        "sourceId": source_id,
        "frequency": "monthly",
        "unit": unit,
        "aggregation": aggregation,
        "asOfClass": as_of_class,
        "coverageFrom": observations[0]["period"],
        "coverageTo": observations[-1]["period"],
        "observationCount": len(observations),
        "missingObservationCount": sum(item.get("value") is None for item in observations),
        "limitation": limitation,
        "observations": observations,
    }


def _binding(
    detector_id: str, mechanism: str, source_id: str, series_id: str,
    transform: str, status: str,
) -> dict[str, str]:
    return {
        "detectorId": detector_id,
        "mechanism": mechanism,
        "sourceId": source_id,
        "seriesId": series_id,
        "transform": transform,
        "status": status,
        "fitScope": "inner-only",
    }


def _structural_coverage(
    taxonomy: dict[str, Any], series: list[dict[str, Any]], history_months: int,
) -> dict[str, Any]:
    by_id = {item["seriesId"]: item for item in series}
    observed = {
        series_id: {item["period"] for item in value["observations"] if item.get("value") is not None}
        for series_id, value in by_id.items()
    }
    result = {}
    for mechanism in MECHANISMS:
        ids = ACTIVE_SERIES[mechanism]
        mature = max(_add_months(_period_month(by_id[item]["coverageFrom"]), history_months) for item in ids)
        end = min(_period_month(by_id[item]["coverageTo"]) for item in ids)
        positive = _observable_episode_ids(taxonomy["episodes"], mechanism, "positive", ids, observed, mature, end)
        negative = _observable_episode_ids(taxonomy["hardNegativeEpisodes"], mechanism, "hard-negative", ids, observed, mature, end)
        result[mechanism] = {
            "seriesIds": ids,
            "matureFrom": mature.isoformat(),
            "coverageTo": end.isoformat(),
            "observablePositiveEpisodeIds": positive,
            "observablePositiveEpisodeCount": len(positive),
            "observableHardNegativeEpisodeIds": negative,
            "observableHardNegativeEpisodeCount": len(negative),
            "structurallyReady": len(positive) >= 3 and len(negative) >= 2,
        }
    return result


def _observable_episode_ids(
    episodes: list[dict[str, Any]], mechanism: str, state: str,
    series_ids: list[str], observed: dict[str, set[str]], mature: date, end: date,
) -> list[str]:
    output = []
    for item in episodes:
        if item.get("financialState") != state or mechanism not in item.get("mechanisms", []):
            continue
        start = max(date.fromisoformat(item["firstMonth"]), mature)
        stop = min(date.fromisoformat(item["lastMonth"]), end)
        if start > stop:
            continue
        months = []
        current = start.replace(day=1)
        while current <= stop:
            months.append(current.isoformat())
            current = _add_months(current, 1)
        if any(all(month in observed[series_id] for series_id in series_ids) for month in months):
            output.append(item["independentEventId"])
    return sorted(set(output))


def _period_month(value: str) -> date:
    if "Q" in value:
        year, quarter = value.split("Q", 1)
        return date(int(year), (int(quarter) - 1) * 3 + 1, 1)
    return date.fromisoformat(value).replace(day=1)


def _add_months(value: date, months: int) -> date:
    offset = value.year * 12 + value.month - 1 + months
    return date(offset // 12, offset % 12 + 1, 1)


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid E14 {label} JSON '{source}'.") from exc


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
