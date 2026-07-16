from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_PUBLICATION_METADATA_COLLECTION_PREFLIGHT_BLOCKED_REQUEST_CATALOG_REQUIRED"
CONTRACT_SHA256 = "066ade723630a5e831256be99d851242b6818b6b196500b78e7de80eca04df78"
HASH_KEYS = (
    "executionGateContractV1Sha256",
    "executionGateAuditV1Sha256",
    "executionPlanV1Sha256",
    "preflightSchemaV1Sha256",
)


def write_e14_fdic_publication_metadata_collection_preflight(
    contract_path: str | Path,
    execution_gate_contract_path: str | Path,
    execution_gate_audit_path: str | Path,
    execution_plan_path: str | Path,
    preflight_schema_path: str | Path,
    repository_root: str | Path,
    output_path: str | Path,
) -> Path:
    labels = ("preflight contract", "execution gate contract", "execution gate audit", "execution plan", "preflight schema")
    paths = (contract_path, execution_gate_contract_path, execution_gate_audit_path, execution_plan_path, preflight_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, gate_contract, gate_audit, plan, schema = (item[2] for item in artifacts)
    if _sha(artifacts[0][1]) != CONTRACT_SHA256:
        raise DatasetValidationError("E14.7ab preflight contract hash is not canonical.")
    hashes = {key: _sha(artifacts[index][1]) for index, key in enumerate(HASH_KEYS, start=1)}
    _validate_inputs(contract, gate_contract, gate_audit, plan, schema, hashes)

    root = Path(repository_root).resolve()
    output = Path(output_path).resolve()
    snapshot_root = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
    catalog_v3 = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
    if output.is_relative_to(snapshot_root):
        raise DatasetValidationError("E14.7ab preflight output cannot be inside snapshot v2.")
    if catalog_v3.exists() or snapshot_root.exists():
        raise DatasetValidationError("E14.7ab catalog v3 or snapshot v2 already exists; fail closed.")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FdicPublicationMetadataCollectionPreflightAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(*artifacts[0][:2]),
            "executionGateContract": _artifact(*artifacts[1][:2]),
            "executionGateAudit": _artifact(*artifacts[2][:2]),
            "executionPlan": _artifact(*artifacts[3][:2]),
            "preflightSchema": _artifact(*artifacts[4][:2]),
        },
        "blockers": ["EXACT_SEED_URLS_NOT_FROZEN", "REQUEST_TEMPLATES_NOT_HASH_BOUND"],
        "checks": {
            "allInputHashesExact": True,
            "executionGatePassed": True,
            "networkBoundsFrozen": True,
            "exactSeedUrlsFrozen": False,
            "requestTemplatesHashBound": False,
            "catalogV3Absent": True,
            "snapshotV2Absent": True,
        },
        "protocol": {
            "networkRequestsMade": 0,
            "metadataRowsCollected": 0,
            "rawArtifactsWritten": 0,
            "ledgersPublished": 0,
            "requestCatalogsMaterialized": 0,
        },
        "decision": {
            "metadataNetworkCollectionAuthorized": False,
            "requestCatalogRemediationAuthorized": True,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_fdic_publication_metadata_collection_preflight",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_schema_value(payload, schema, schema, "$")
    if output.exists():
        raise DatasetValidationError("Immutable E14.7ab preflight output already exists.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return output


def _validate_inputs(contract: dict[str, Any], gate_contract: dict[str, Any], gate_audit: dict[str, Any], plan: dict[str, Any], schema: dict[str, Any], hashes: dict[str, str]) -> None:
    invalid = (
        contract.get("contractId") != "e14-fdic-publication-metadata-collection-preflight-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("requiredExecutionInputs") != ["exactSeedUrls", "hashBoundRequestTemplates"]
        or contract.get("failurePolicy") != {
            "missingExecutionInputBlocksBeforeNetwork": True,
            "partialLedgerPublicationForbidden": True,
            "requestCatalogV3MaterializationForbidden": True,
            "sourceAcquisitionForbidden": True,
        }
        or gate_contract.get("contractId") != "e14-fdic-publication-metadata-execution-gate-contract-v1"
        or gate_audit.get("status") != "FDIC_PUBLICATION_METADATA_EXECUTION_GATE_PASSED_COLLECTION_SEPARATELY_AUTHORIZED"
        or gate_audit.get("decision", {}).get("metadataNetworkCollectionAuthorized") is not True
        or plan.get("planId") != "e14-fdic-publication-metadata-execution-plan-v1"
        or "exactSeedUrls" in plan
        or "requestTemplates" in plan
        or plan.get("networkPolicy", {}).get("allowedHosts") != ["www.fdic.gov"]
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-publication-metadata-collection-preflight-audit-v1.json"
    )
    if invalid:
        raise DatasetValidationError("E14.7ab collection preflight inputs or expected blocker are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7ab {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
