from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_ARCHIVE_PROVIDER_EVIDENCE_COLLECTION_PREREGISTERED_REVIEW_REQUIRED"
HASH_KEYS = (
    "blockedReviewV1Sha256",
    "mapV1Sha256",
    "mapAuditV1Sha256",
    "collectionPlanV1Sha256",
    "mapSchemaV2Sha256",
    "mapAuditSchemaV2Sha256",
    "preregistrationAuditSchemaV1Sha256",
)
FORBIDDEN_AUTHORIZATIONS = (
    "networkCollectionAuthorized",
    "providerDiscoveryRequestCatalogAuthorized",
    "replacementExecutionGateAuthorized",
    "requestCatalogV3MaterializationAuthorized",
    "sourceAcquisitionAuthorized",
    "featureTransformationAuthorized",
    "candidateGenerationAuthorized",
    "evaluationAuthorized",
    "outerOosAuthorized",
)


def write_e14_fdic_archive_evidence_preregistration(
    contract_path: str | Path,
    blocked_review_path: str | Path,
    map_v1_path: str | Path,
    map_audit_v1_path: str | Path,
    collection_plan_path: str | Path,
    map_schema_v2_path: str | Path,
    map_audit_schema_v2_path: str | Path,
    preregistration_audit_schema_path: str | Path,
    repository_root: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "contract",
        "blocked review",
        "map v1",
        "map audit v1",
        "collection plan",
        "map schema v2",
        "map audit schema v2",
        "preregistration audit schema",
    )
    paths = (
        contract_path,
        blocked_review_path,
        map_v1_path,
        map_audit_v1_path,
        collection_plan_path,
        map_schema_v2_path,
        map_audit_schema_v2_path,
        preregistration_audit_schema_path,
    )
    artifacts = tuple(_read(path, label) for path, label in zip(paths, labels))
    contract, review, map_v1, map_audit_v1, plan, map_schema_v2, map_audit_schema_v2, audit_schema = (
        item[2] for item in artifacts
    )
    hashes = {
        key: _sha(artifacts[index][1])
        for index, key in enumerate(HASH_KEYS, start=1)
    }
    _validate_inputs(
        contract,
        review,
        map_v1,
        map_audit_v1,
        plan,
        map_schema_v2,
        map_audit_schema_v2,
        audit_schema,
        hashes,
    )

    root = Path(repository_root).resolve()
    output = Path(output_path).resolve()
    snapshot_v2 = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
    catalog_v3 = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
    discovery_catalog = root / "data/historical-real-v12-2008-2025/challengers/e14-fdic-archive-provider-discovery-requests-v1.json"
    map_v2 = root / "data/historical-real-v12-2008-2025/challengers/e14-fdic-archive-quarter-map-v2.json"
    if output.is_relative_to(snapshot_v2):
        raise DatasetValidationError("E14.7ag output cannot be written inside snapshot v2.")
    if catalog_v3.exists() or snapshot_v2.exists() or discovery_catalog.exists() or map_v2.exists():
        raise DatasetValidationError("E14.7ag forbidden catalog, snapshot, discovery requests, or map v2 already exists; fail closed.")
    if output.exists():
        raise DatasetValidationError("Immutable E14.7ag preregistration output already exists.")

    entries = map_v1["entries"]
    quarter_ids = [entry["quarterId"] for entry in entries]
    expected = _quarter_ids()
    if quarter_ids != expected or len(set(quarter_ids)) != 79:
        raise DatasetValidationError("E14.7ag source quarter roster is not exactly ordered 79/79.")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FdicArchiveEvidencePreregistrationAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(*artifacts[0][:2]),
            "blockedReview": _artifact(*artifacts[1][:2]),
            "mapV1": _artifact(*artifacts[2][:2]),
            "mapAuditV1": _artifact(*artifacts[3][:2]),
            "collectionPlan": _artifact(*artifacts[4][:2]),
            "mapSchemaV2": _artifact(*artifacts[5][:2]),
            "mapAuditSchemaV2": _artifact(*artifacts[6][:2]),
            "preregistrationAuditSchema": _artifact(*artifacts[7][:2]),
        },
        "inventory": {
            "requiredQuarterCount": 79,
            "currentlyResolvedCount": 0,
            "currentlyConfirmedAbsentCount": 0,
            "pendingProviderEvidenceCount": 79,
            "firstQuarter": "2006Q1",
            "lastQuarter": "2025Q3",
        },
        "checks": {
            "allInputHashesExact": True,
            "blockedReviewRequiresProviderEvidence": True,
            "quarterRosterExact": True,
            "twoOutcomeModelDefined": True,
            "resolvedOutcomeRepresentable": True,
            "confirmedAbsentOutcomeRepresentable": True,
            "auditSchemaClosed": True,
            "partialPublicationForbidden": True,
            "catalogV3Absent": True,
            "snapshotV2Absent": True,
        },
        "protocol": {
            "networkRequestsMade": 0,
            "evidenceRowsCollected": 0,
            "rawArtifactsWritten": 0,
            "mapV2Materialized": False,
            "requestCatalogsMaterialized": 0,
            "featuresTransformed": 0,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "providerEvidenceCollectionPreregistered": True,
            "independentDesignReviewAuthorized": True,
            "networkCollectionAuthorized": False,
            "providerDiscoveryRequestCatalogAuthorized": False,
            "replacementExecutionGateAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_fdic_archive_evidence_preregistration",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_schema_value(payload, audit_schema, audit_schema, "$")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return output


def _validate_inputs(
    contract: dict[str, Any],
    review: dict[str, Any],
    map_v1: dict[str, Any],
    map_audit_v1: dict[str, Any],
    plan: dict[str, Any],
    map_schema_v2: dict[str, Any],
    map_audit_schema_v2: dict[str, Any],
    audit_schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    auth = contract.get("authorizationPolicy", {})
    review_assessments = review.get("assessments", {})
    execution = plan.get("executionPolicy", {})
    completion = plan.get("completionPolicy", {})
    map_properties = map_schema_v2.get("properties", {})
    audit_defs = map_audit_schema_v2.get("$defs", {})
    invalid = (
        contract.get("contractId") != "e14-fdic-archive-evidence-preregistration-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedQuarterCount") != 79
        or auth.get("providerEvidenceCollectionPreregistrationAuthorized") is not True
        or auth.get("independentDesignReviewAuthorized") is not True
        or any(auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or review.get("decision") != "needs_changes"
        or review_assessments.get("unresolvedClaimsEvidenceBound") is not False
        or review_assessments.get("archiveMappingOperationallyComplete") is not False
        or review_assessments.get("replacementExecutionGateAuthorized") is not False
        or len(review.get("blockingFindings", [])) != 4
        or map_v1.get("mapId") != "e14-fdic-archive-quarter-map-v1"
        or len(map_v1.get("entries", [])) != 79
        or map_audit_v1.get("inventory", {}).get("unresolvedEntryCount") != 79
        or plan.get("planId") != "e14-fdic-archive-evidence-collection-plan-v1"
        or set(plan.get("admissibleOutcomes", [])) != {"resolved-provider-archive-record", "confirmed-absent-provider-primary"}
        or execution.get("thisStepMayUseNetwork") is not False
        or execution.get("thisStepMayCollectEvidence") is not False
        or execution.get("thisStepMayMaterializeMapV2") is not False
        or execution.get("providerDiscoveryRequestCatalogStillRequired") is not True
        or completion.get("all79QuartersMustHaveExactlyOneOutcome") is not True
        or completion.get("partialPublicationForbidden") is not True
        or map_schema_v2.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-quarter-map-v2.json"
        or not {"resolvedEntries", "confirmedAbsentEntries"}.issubset(map_properties)
        or map_audit_schema_v2.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-quarter-map-audit-v2.json"
        or not {"checks", "inventory", "protocol", "decision"}.issubset(audit_defs)
        or any(audit_defs[name].get("additionalProperties") is not False for name in ("checks", "inventory", "protocol", "decision"))
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-evidence-preregistration-audit-v1.json"
    )
    if invalid:
        raise DatasetValidationError("E14.7ag provider-evidence preregistration inputs or governance are invalid.")


def _quarter_ids() -> list[str]:
    return [
        f"{year}Q{quarter}"
        for year in range(2006, 2026)
        for quarter in range(1, 5)
        if not (year == 2025 and quarter == 4)
    ]


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7ag {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
