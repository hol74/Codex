from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_ARCHIVE_QUARTER_MAP_MATERIALIZED_INDEPENDENT_REVIEW_REQUIRED"
UNRESOLVED_STATE = "unresolved-no-hash-bound-local-evidence"
UNRESOLVED_REASON = "archive-record-not-established-by-hash-bound-local-evidence"
HASH_KEYS = (
    "requestCatalogV1Sha256",
    "blockedReviewV1Sha256",
    "mapPlanV1Sha256",
    "mapSchemaV1Sha256",
    "auditSchemaV1Sha256",
)


def write_e14_fdic_archive_quarter_map(
    contract_path: str | Path,
    request_catalog_path: str | Path,
    blocked_review_path: str | Path,
    map_plan_path: str | Path,
    map_schema_path: str | Path,
    audit_schema_path: str | Path,
    repository_root: str | Path,
    map_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    inputs = tuple(
        _read_json(path, label)
        for path, label in (
            (contract_path, "contract"),
            (request_catalog_path, "request catalog"),
            (blocked_review_path, "blocked independent review"),
            (map_plan_path, "map plan"),
            (map_schema_path, "map schema"),
            (audit_schema_path, "audit schema"),
        )
    )
    contract, catalog, review, plan, map_schema, audit_schema = (item[2] for item in inputs)
    hashes = {
        key: _sha(inputs[index][1])
        for index, key in enumerate(HASH_KEYS, start=1)
    }
    _validate_inputs(contract, catalog, review, plan, map_schema, audit_schema, hashes)

    root = Path(repository_root).resolve()
    map_output = Path(map_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    forbidden_catalog = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
    snapshot_v2 = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
    if forbidden_catalog.exists() or snapshot_v2.exists():
        raise DatasetValidationError("E14.7ae catalog v3 or snapshot v2 already exists; fail closed.")
    if map_output == audit_output or map_output.exists() or audit_output.exists():
        raise DatasetValidationError("Immutable E14.7ae output already exists or output paths collide.")

    entries = _build_entries(catalog)
    artifact = {
        "schemaVersion": 1,
        "artifactType": "E14FdicArchiveQuarterMap",
        "mapId": "e14-fdic-archive-quarter-map-v1",
        "status": STATUS,
        "sourceCatalog": _artifact(inputs[1][0], inputs[1][1]),
        "entries": entries,
        "authorizationPolicy": {
            "networkRequestsAuthorized": False,
            "archiveTraversalAuthorized": False,
            "independentReviewRequired": True,
            "replacementExecutionGateAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
        },
    }
    _validate_schema_value(artifact, map_schema, map_schema, "$")
    map_raw = _json_bytes(artifact)

    audit = {
        "schemaVersion": 1,
        "artifactType": "E14FdicArchiveQuarterMapAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(inputs[0][0], inputs[0][1]),
            "requestCatalog": _artifact(inputs[1][0], inputs[1][1]),
            "blockedIndependentReview": _artifact(inputs[2][0], inputs[2][1]),
            "mapPlan": _artifact(inputs[3][0], inputs[3][1]),
            "mapSchema": _artifact(inputs[4][0], inputs[4][1]),
            "auditSchema": _artifact(inputs[5][0], inputs[5][1]),
        },
        "outputs": {"archiveQuarterMap": _artifact(map_output, map_raw)},
        "checks": {
            "allInputHashesExact": True,
            "blockedReviewRequiresRemediation": True,
            "quarterRosterExact": True,
            "sourceCatalogRosterPreserved": True,
            "archiveExpansionsFrozen": True,
            "inventedArchiveRecordIdsAbsent": True,
            "runtimeArchiveDiscoveryForbidden": True,
            "catalogV3Absent": True,
            "snapshotV2Absent": True,
        },
        "inventory": {
            "entryCount": len(entries),
            "resolvedEntryCount": 0,
            "unresolvedEntryCount": len(entries),
            "firstQuarter": entries[0]["quarterId"],
            "lastQuarter": entries[-1]["quarterId"],
        },
        "protocol": {
            "networkRequestsMade": 0,
            "archivePagesTraversed": 0,
            "archiveRecordIdsInvented": 0,
            "metadataRowsCollected": 0,
        },
        "decision": {
            "archiveQuarterMapMaterialized": True,
            "independentReviewAuthorized": True,
            "metadataNetworkCollectionAuthorized": False,
            "replacementExecutionGateAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_fdic_archive_quarter_map",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_schema_value(audit, audit_schema, audit_schema, "$")
    audit_raw = _json_bytes(audit)
    map_output.parent.mkdir(parents=True, exist_ok=True)
    audit_output.parent.mkdir(parents=True, exist_ok=True)
    map_output.write_bytes(map_raw)
    audit_output.write_bytes(audit_raw)
    return map_output, audit_output


def _build_entries(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    requests = catalog.get("quarterRequests", [])
    expected = [
        f"{year}Q{quarter}"
        for year in range(2006, 2026)
        for quarter in range(1, 5)
        if not (year == 2025 and quarter == 4)
    ]
    actual = [item.get("quarterId") for item in requests]
    if actual != expected or len(set(actual)) != 79:
        raise DatasetValidationError("E14.7ae source quarter roster is not exact and ordered.")
    entries = []
    for item in requests:
        url = item.get("providerPrimaryUrl")
        if not isinstance(url, str) or not url.startswith("https://www.fdic.gov/"):
            raise DatasetValidationError(f"E14.7ae invalid provider-primary URL for {item.get('quarterId')}.")
        entries.append(
            {
                "quarterId": item["quarterId"],
                "providerPrimaryUrl": url,
                "resolutionState": UNRESOLVED_STATE,
                "unresolvedReason": UNRESOLVED_REASON,
                "runtimeDiscoveryAuthorized": False,
            }
        )
    return entries


def _validate_inputs(
    contract: dict[str, Any],
    catalog: dict[str, Any],
    review: dict[str, Any],
    plan: dict[str, Any],
    map_schema: dict[str, Any],
    audit_schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    invalid = (
        contract.get("contractId") != "e14-fdic-archive-quarter-map-contract-v1"
        or contract.get("inputHashes") != hashes
        or catalog.get("requestCatalogId") != "e14-fdic-publication-metadata-requests-v1"
        or review.get("decision") != "needs_changes"
        or review.get("assessments", {}).get("archiveExpansionValuesFrozen") is not False
        or review.get("assessments", {}).get("replacementExecutionGateAuthorized") is not False
        or plan.get("planId") != "e14-fdic-archive-quarter-map-plan-v1"
        or plan.get("derivationPolicy", {}).get("requiredQuarterCount") != 79
        or plan.get("derivationPolicy", {}).get("runtimeArchiveDiscoveryForbidden") is not True
        or map_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-quarter-map-v1.json"
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-quarter-map-audit-v1.json"
    )
    if invalid:
        raise DatasetValidationError("E14.7ae archive quarter-map inputs are invalid.")


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7ae {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
