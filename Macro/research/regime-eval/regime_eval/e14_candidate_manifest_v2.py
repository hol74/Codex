from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "GENERATED_V2_NOT_TRANSFORMED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED"
SOURCE_LIFECYCLE = "readiness-planned-not-generated-not-fit"
GENERATED_LIFECYCLE = "research-generated-not-fit"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]


def write_e14_candidate_manifest_v2(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    foundation_path: str | Path,
    foundation_lock_path: str | Path,
    readiness_roster_path: str | Path,
    readiness_audit_path: str | Path,
    candidate_protocol_path: str | Path,
    protocol_audit_path: str | Path,
    manifest_schema_path: str | Path,
    manifest_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    labels = (
        "manifest contract v2", "taxonomy v5", "foundation v2", "foundation lock v2",
        "readiness roster v2", "readiness audit v2", "candidate protocol v2",
        "protocol readiness audit v2", "manifest schema v2",
    )
    paths = (
        contract_path, taxonomy_path, foundation_path, foundation_lock_path,
        readiness_roster_path, readiness_audit_path, candidate_protocol_path,
        protocol_audit_path, manifest_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract), (taxonomy_file, taxonomy_raw, taxonomy),
     (foundation_file, foundation_raw, foundation), (lock_file, lock_raw, lock),
     (roster_file, roster_raw, roster), (readiness_audit_file, readiness_audit_raw, readiness_audit),
     (protocol_file, protocol_raw, protocol), (protocol_audit_file, protocol_audit_raw, protocol_audit),
     (schema_file, schema_raw, schema)) = artifacts

    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "featureFoundationV2Sha256": _sha(foundation_raw),
        "featureFoundationLockV2Sha256": _sha(lock_raw),
        "readinessRosterV2Sha256": _sha(roster_raw),
        "readinessAuditV2Sha256": _sha(readiness_audit_raw),
        "candidateProtocolV2Sha256": _sha(protocol_raw),
        "protocolReadinessAuditV2Sha256": _sha(protocol_audit_raw),
        "manifestSchemaV2Sha256": _sha(schema_raw),
    }
    _validate_governance(contract, taxonomy, foundation, lock, roster, readiness_audit,
                         protocol, protocol_audit, schema, hashes)

    outputs = [Path(manifest_output_path).resolve(), Path(audit_output_path).resolve()]
    if any(path.exists() for path in outputs):
        raise DatasetValidationError("Immutable E14 candidate-manifest v2 output already exists.")

    roster_candidates = roster["candidates"]
    generated_candidates = []
    for source in roster_candidates:
        generated = copy.deepcopy(source)
        generated["lifecycleStatus"] = GENERATED_LIFECYCLE
        restored = copy.deepcopy(generated)
        restored["lifecycleStatus"] = SOURCE_LIFECYCLE
        if _canonical_bytes(restored) != _canonical_bytes(source):
            raise DatasetValidationError("E14 manifest v2 candidate mutation exceeds lifecycle transition.")
        generated_candidates.append(generated)

    candidate_ids = [item["candidateId"] for item in generated_candidates]
    counts = dict(Counter(item["mechanism"] for item in generated_candidates))
    generation_seed = {
        "inputHashes": hashes,
        "candidateIds": candidate_ids,
        "lifecycleTransition": [SOURCE_LIFECYCLE, GENERATED_LIFECYCLE],
    }
    generation_id = hashlib.sha256(_canonical_bytes(generation_seed)).hexdigest()[:24]
    authorizations = contract["authorizationPolicy"]
    input_artifacts = {
        "manifestContractV2": _artifact(contract_file, contract_raw),
        "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
        "featureFoundationV2": _artifact(foundation_file, foundation_raw),
        "featureFoundationLockV2": _artifact(lock_file, lock_raw),
        "readinessRosterV2": _artifact(roster_file, roster_raw),
        "readinessAuditV2": _artifact(readiness_audit_file, readiness_audit_raw),
        "candidateProtocolV2": _artifact(protocol_file, protocol_raw),
        "protocolReadinessAuditV2": _artifact(protocol_audit_file, protocol_audit_raw),
        "manifestSchemaV2": _artifact(schema_file, schema_raw),
    }
    manifest = {
        "schemaVersion": 2,
        "artifactType": "E14FourDetectorGeneratedCandidateManifest",
        "manifestId": "e14-generated-four-detector-candidates-v2",
        "immutable": True,
        "status": STATUS,
        "generationId": generation_id,
        "inputs": input_artifacts,
        "candidateCount": len(generated_candidates),
        "candidateCountByMechanism": counts,
        "candidateIds": candidate_ids,
        "researchBoundary": protocol["researchBoundary"],
        "fundingBoundarySensitivity": protocol["fundingBoundarySensitivity"],
        "retiredCandidateIds": roster["retiredCandidateIds"],
        "authorizations": authorizations,
        "candidates": generated_candidates,
        "implementation": {
            "module": "regime_eval.e14_candidate_manifest_v2",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    manifest_raw = _json_bytes(manifest)
    audit = {
        "schemaVersion": 2,
        "artifactType": "E14FourDetectorCandidateManifestAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "outputs": {"candidateManifestV2": _artifact(outputs[0], manifest_raw)},
        "inventory": {
            "candidateCount": len(generated_candidates),
            "candidateCountByMechanism": counts,
            "retiredCandidateIdCount": len(roster["retiredCandidateIds"]),
        },
        "checks": {
            "allInputHashesExact": True,
            "candidateIdsEqualRosterAndProtocolInOrder": candidate_ids == protocol["candidateIds"],
            "candidateIdRecomputationAbsent": True,
            "onlyLifecycleStatusChanged": True,
            "profilesCopiedVerbatim": True,
            "featureBindingsCopiedVerbatim": True,
            "persistenceCopiedVerbatim": True,
            "eligibilityCopiedVerbatim": True,
            "retiredCandidateIdsDisjoint": not set(candidate_ids) & set(roster["retiredCandidateIds"]),
            "featureTransformationAbsent": True,
            "candidateFittingAbsent": True,
            "candidateEvaluationAbsent": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "candidateManifestGenerated": True,
            "featureRowsTransformed": 0,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "candidateRanked": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "decision": {
            "candidateManifestV2Materialized": True,
            **authorizations,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": manifest["implementation"],
    }
    return (
        _write_new_bytes(outputs[0], manifest_raw, "candidate manifest v2"),
        _write_new_bytes(outputs[1], _json_bytes(audit), "candidate manifest audit v2"),
    )


def _validate_governance(
    contract: dict[str, Any], taxonomy: dict[str, Any], foundation: dict[str, Any],
    lock: dict[str, Any], roster: dict[str, Any], readiness_audit: dict[str, Any],
    protocol: dict[str, Any], protocol_audit: dict[str, Any], schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    expected_auth = {
        "candidateManifestMaterializationAuthorized": True,
        "featureTransformationAuthorized": False,
        "candidateFittingAuthorized": False,
        "candidateEvaluationAuthorized": False,
        "candidateRankingAuthorized": False,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    roster_ids = [item.get("candidateId") for item in roster.get("candidates", [])]
    counts = dict(Counter(item.get("mechanism") for item in roster.get("candidates", [])))
    if (
        contract.get("contractId") != "e14-four-detector-candidate-manifest-contract-v2"
        or contract.get("inputHashes") != hashes
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v2"
        or lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v2"
        or lock.get("foundation", {}).get("sha256") != hashes["featureFoundationV2Sha256"]
        or roster.get("rosterId") != "e14-four-detector-readiness-roster-v2"
        or roster.get("candidateCount") != 28
        or counts != contract.get("expectedCandidateCounts")
        or len(roster_ids) != len(set(roster_ids))
        or protocol.get("protocolId") != "e14-four-detector-candidate-generation-protocol-v2"
        or protocol.get("candidateIds") != roster_ids
        or protocol.get("candidateBudget") != 28
        or readiness_audit.get("decision", {}).get("candidateManifestGenerationAuthorized") is not False
        or protocol_audit.get("decision", {}).get("candidateManifestGenerationAuthorized") is not True
        or protocol_audit.get("decision", {}).get("candidateFittingAuthorized") is not False
        or protocol_audit.get("decision", {}).get("outerOosAuthorized") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-candidate-manifest-v2.json"
        or set(roster_ids) & set(roster.get("retiredCandidateIds", []))
    ):
        raise DatasetValidationError("E14 candidate-manifest v2 inputs or governance are invalid.")
    identity = contract.get("identityPolicy", {})
    if (
        identity.get("sourceLifecycleStatus") != SOURCE_LIFECYCLE
        or identity.get("generatedLifecycleStatus") != GENERATED_LIFECYCLE
        or not all(value is True for key, value in identity.items() if key not in {"sourceLifecycleStatus", "generatedLifecycleStatus"})
        or any(item.get("lifecycleStatus") != SOURCE_LIFECYCLE for item in roster["candidates"])
    ):
        raise DatasetValidationError("E14 candidate-manifest v2 identity policy is invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid E14 {label} JSON '{source}'.") from exc


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


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
