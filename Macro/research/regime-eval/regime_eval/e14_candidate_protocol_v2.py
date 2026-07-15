from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "RESEARCH_CANDIDATE_PROTOCOL_V2_READY_MANIFEST_GENERATION_AUTHORIZED_FITTING_CLOSED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]


def write_e14_candidate_protocol_v2(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    foundation_path: str | Path,
    foundation_lock_path: str | Path,
    foundation_audit_path: str | Path,
    readiness_roster_path: str | Path,
    readiness_audit_path: str | Path,
    readiness_policy_path: str | Path,
    protocol_plan_path: str | Path,
    protocol_schema_path: str | Path,
    protocol_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_raw, contract = _read(contract_path, "protocol readiness contract v2")
    taxonomy_file, taxonomy_raw, taxonomy = _read(taxonomy_path, "taxonomy v5")
    foundation_file, foundation_raw, foundation = _read(foundation_path, "foundation v2")
    lock_file, lock_raw, lock = _read(foundation_lock_path, "foundation lock v2")
    foundation_audit_file, foundation_audit_raw, foundation_audit = _read(
        foundation_audit_path, "foundation audit v2"
    )
    roster_file, roster_raw, roster = _read(readiness_roster_path, "readiness roster v2")
    readiness_audit_file, readiness_audit_raw, readiness_audit = _read(
        readiness_audit_path, "readiness audit v2"
    )
    policy_file, policy_raw, policy = _read(readiness_policy_path, "readiness policy v2")
    plan_file, plan_raw, plan = _read(protocol_plan_path, "candidate protocol plan v2")
    schema_file, schema_raw, schema = _read(protocol_schema_path, "candidate protocol schema v2")
    _validate_inputs(
        contract, taxonomy, foundation, lock, foundation_audit, roster,
        readiness_audit, policy, plan, schema, taxonomy_raw, foundation_raw,
        lock_raw, foundation_audit_raw, roster_raw, readiness_audit_raw,
        policy_raw, plan_raw, schema_raw,
    )

    outputs = [Path(protocol_output_path).resolve(), Path(audit_output_path).resolve()]
    if any(path.exists() for path in outputs):
        raise DatasetValidationError("Immutable E14 candidate-protocol v2 output already exists.")

    bindings = {
        (item["mechanism"], item["seriesId"]): item
        for item in foundation["detectorBindings"]
    }
    detectors: dict[str, Any] = {}
    counts = {mechanism: 0 for mechanism in MECHANISMS}
    profile_counts = {mechanism: 0 for mechanism in MECHANISMS}
    for mechanism in MECHANISMS:
        candidates = [item for item in roster["candidates"] if item["mechanism"] == mechanism]
        if not candidates:
            raise DatasetValidationError("E14 protocol v2 roster mechanism is empty.")
        detector_ids = {item["detectorId"] for item in candidates}
        if len(detector_ids) != 1:
            raise DatasetValidationError("E14 protocol v2 detector identity is inconsistent.")
        groups: dict[bytes, list[dict[str, Any]]] = defaultdict(list)
        for candidate in candidates:
            groups[_canonical_bytes(candidate["profile"])].append(candidate)
        profiles = []
        for key in sorted(groups):
            group = groups[key]
            profile = group[0]["profile"]
            expected_combinations = {(1, 1), (1, 2), (2, 1), (2, 2)}
            actual_combinations = {
                (
                    item["persistence"]["entryPersistenceMonths"],
                    item["persistence"]["recoveryPersistenceMonths"],
                )
                for item in group
            }
            feature_bindings = group[0]["featureBindings"]
            if (
                actual_combinations != expected_combinations
                or len(group) != 4
                or any(item["featureBindings"] != feature_bindings for item in group)
                or any(item["profile"] != profile for item in group)
            ):
                raise DatasetValidationError("E14 protocol v2 profile grammar is inconsistent.")
            for feature in feature_bindings:
                binding = bindings.get((mechanism, feature["seriesId"]))
                if binding is None or any(
                    feature[field] != binding[field]
                    for field in ("seriesId", "sourceId", "transform", "fitScope")
                ):
                    raise DatasetValidationError("E14 protocol v2 feature binding does not resolve exactly.")
            profiles.append({
                **profile,
                "featureBindings": feature_bindings,
                "candidateIds": [item["candidateId"] for item in group],
                "persistenceCombinations": [
                    {
                        "entryPersistenceMonths": item["persistence"]["entryPersistenceMonths"],
                        "recoveryPersistenceMonths": item["persistence"]["recoveryPersistenceMonths"],
                        "hysteresisRequired": item["persistence"]["hysteresisRequired"],
                    }
                    for item in group
                ],
            })
        counts[mechanism] = len(candidates)
        profile_counts[mechanism] = len(profiles)
        detectors[mechanism] = {
            "detectorId": next(iter(detector_ids)),
            "candidateCount": len(candidates),
            "profileCount": len(profiles),
            "profiles": profiles,
        }

    if counts != contract["expectedCandidateCounts"] or profile_counts != contract["expectedProfileCounts"]:
        raise DatasetValidationError("E14 protocol v2 detector budget differs from contract.")

    roster_ids = [item["candidateId"] for item in roster["candidates"]]
    preserved = sum(
        item["identityPolicy"] == "preserved-exactly-from-candidate-manifest-v1"
        for item in roster["candidates"]
    )
    new_v2 = sum("-v2-" in item["candidateId"] for item in roster["candidates"])
    if (
        len(roster_ids) != len(set(roster_ids)) == 28
        or preserved != contract["identityPolicy"]["preservedBroadCandidateIdCount"]
        or new_v2 != contract["identityPolicy"]["newV2CandidateIdCount"]
        or len(roster["retiredCandidateIds"]) != contract["identityPolicy"]["retiredV1CandidateIdCount"]
        or set(roster_ids) & set(roster["retiredCandidateIds"])
    ):
        raise DatasetValidationError("E14 protocol v2 identity transition is invalid.")

    input_hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "featureFoundationV2Sha256": hashlib.sha256(foundation_raw).hexdigest(),
        "featureFoundationLockV2Sha256": hashlib.sha256(lock_raw).hexdigest(),
        "featureFoundationAuditV2Sha256": hashlib.sha256(foundation_audit_raw).hexdigest(),
        "readinessRosterV2Sha256": hashlib.sha256(roster_raw).hexdigest(),
        "readinessAuditV2Sha256": hashlib.sha256(readiness_audit_raw).hexdigest(),
        "readinessPolicyV2Sha256": hashlib.sha256(policy_raw).hexdigest(),
        "protocolPlanV2Sha256": hashlib.sha256(plan_raw).hexdigest(),
        "protocolSchemaV2Sha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    protocol = {
        "schemaVersion": 2,
        "protocolId": "e14-four-detector-candidate-generation-protocol-v2",
        "frozenAt": plan["frozenAt"],
        "inputHashes": input_hashes,
        "researchBoundary": plan["researchBoundary"],
        "candidateBudget": plan["candidateBudget"],
        "candidateIds": roster_ids,
        "detectors": detectors,
        "thresholdSelection": plan["thresholdSelection"],
        "persistence": plan["persistence"],
        "availabilityPolicy": plan["availabilityPolicy"],
        "evaluationPolicy": plan["evaluationPolicy"],
        "fundingBoundarySensitivity": policy["fundingBoundarySensitivity"],
        "identityTransitionPolicy": {
            **plan["identityTransitionPolicy"],
            "retiredCandidateIds": roster["retiredCandidateIds"],
        },
        "generationPolicy": plan["generationPolicy"],
        "vintageRiskPolicy": plan["vintageRiskPolicy"],
        "constraints": plan["constraints"],
        "compositionPolicy": plan["compositionPolicy"],
        "authorizations": plan["authorizationPolicy"],
    }
    protocol_raw = _json_bytes(protocol)
    input_artifacts = {
        "readinessContractV2": _artifact(contract_file, contract_raw),
        "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
        "featureFoundationV2": _artifact(foundation_file, foundation_raw),
        "featureFoundationLockV2": _artifact(lock_file, lock_raw),
        "featureFoundationAuditV2": _artifact(foundation_audit_file, foundation_audit_raw),
        "readinessRosterV2": _artifact(roster_file, roster_raw),
        "readinessAuditV2": _artifact(readiness_audit_file, readiness_audit_raw),
        "readinessPolicyV2": _artifact(policy_file, policy_raw),
        "protocolPlanV2": _artifact(plan_file, plan_raw),
        "protocolSchemaV2": _artifact(schema_file, schema_raw),
    }
    audit = {
        "schemaVersion": 2,
        "artifactType": "E14FourDetectorCandidateProtocolReadinessAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "outputs": {"candidateProtocolV2": _artifact(outputs[0], protocol_raw)},
        "inventory": {
            "candidateCount": len(roster_ids),
            "candidateCountByMechanism": counts,
            "profileCount": sum(profile_counts.values()),
            "profileCountByMechanism": profile_counts,
            "preservedBroadCandidateIdCount": preserved,
            "newV2CandidateIdCount": new_v2,
            "retiredV1CandidateIdCount": len(roster["retiredCandidateIds"]),
        },
        "checks": {
            "allInputHashesExact": True,
            "candidateIdsEqualRosterInOrder": protocol["candidateIds"] == roster_ids,
            "candidateIdRecomputationAbsent": True,
            "allProfilesCopiedFromRoster": True,
            "allPersistenceCombinationsExact": True,
            "allFeatureBindingsResolveExactly": True,
            "availabilityAndAsOfPolicyFrozen": plan["availabilityPolicy"]["asOfSemanticsRequired"],
            "fundingSensitivityMatchesReadinessPolicy": protocol["fundingBoundarySensitivity"] == policy["fundingBoundarySensitivity"],
            "strictVintageReady": False,
            "candidateManifestNotGenerated": True,
            "candidateFittingClosed": True,
            "candidateEvaluationClosed": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "candidateProtocolV2Frozen": True,
            "candidateManifestGenerated": False,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "candidateRanked": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "decision": {
            "candidateProtocolV2Ready": True,
            "candidateManifestGenerationAuthorized": True,
            "featureTransformationAuthorized": False,
            "candidateFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "candidateRankingAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_candidate_protocol_v2",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return (
        _write_new_bytes(outputs[0], protocol_raw, "candidate protocol v2"),
        _write_new_bytes(outputs[1], _json_bytes(audit), "candidate protocol readiness audit v2"),
    )


def _validate_inputs(
    contract: dict[str, Any], taxonomy: dict[str, Any], foundation: dict[str, Any],
    lock: dict[str, Any], foundation_audit: dict[str, Any], roster: dict[str, Any],
    readiness_audit: dict[str, Any], policy: dict[str, Any], plan: dict[str, Any],
    schema: dict[str, Any], taxonomy_raw: bytes, foundation_raw: bytes,
    lock_raw: bytes, foundation_audit_raw: bytes, roster_raw: bytes,
    readiness_audit_raw: bytes, policy_raw: bytes, plan_raw: bytes,
    schema_raw: bytes,
) -> None:
    hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "featureFoundationV2Sha256": hashlib.sha256(foundation_raw).hexdigest(),
        "featureFoundationLockV2Sha256": hashlib.sha256(lock_raw).hexdigest(),
        "featureFoundationAuditV2Sha256": hashlib.sha256(foundation_audit_raw).hexdigest(),
        "readinessRosterV2Sha256": hashlib.sha256(roster_raw).hexdigest(),
        "readinessAuditV2Sha256": hashlib.sha256(readiness_audit_raw).hexdigest(),
        "readinessPolicyV2Sha256": hashlib.sha256(policy_raw).hexdigest(),
        "protocolPlanV2Sha256": hashlib.sha256(plan_raw).hexdigest(),
        "protocolSchemaV2Sha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    expected_auth = {
        "protocolFreezeAuthorized": True,
        "candidateManifestGenerationAuthorizedOnPass": True,
        "featureTransformationAuthorized": False,
        "candidateFittingAuthorized": False,
        "candidateEvaluationAuthorized": False,
        "candidateRankingAuthorized": False,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    expected_identity = {
        "candidateIdsMustEqualRosterInOrder": True,
        "candidateIdRecomputationForbidden": True,
        "preservedBroadCandidateIdCount": 16,
        "newV2CandidateIdCount": 12,
        "retiredV1CandidateIdCount": 24,
        "retiredIdReuseForbidden": True,
    }
    if (
        contract.get("contractId") != "e14-four-detector-protocol-readiness-contract-v2"
        or contract.get("inputHashes") != hashes
        or contract.get("identityPolicy") != expected_identity
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v2"
        or lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v2"
        or lock.get("foundation", {}).get("sha256") != hashes["featureFoundationV2Sha256"]
        or foundation_audit.get("decision", {}).get("structuralCoverageRepaired") is not True
        or roster.get("rosterId") != "e14-four-detector-readiness-roster-v2"
        or roster.get("candidateCount") != 28
        or readiness_audit.get("status") != "FOUR_DETECTOR_READINESS_V2_PASSED_PROTOCOL_V2_DESIGN_AUTHORIZED_FITTING_CLOSED"
        or readiness_audit.get("decision", {}).get("protocolV2DesignAuthorized") is not True
        or readiness_audit.get("decision", {}).get("candidateManifestGenerationAuthorized") is not False
        or policy.get("policyId") != "e14-four-detector-readiness-policy-v2"
        or plan.get("planId") != "e14-four-detector-candidate-protocol-plan-v2"
        or plan.get("candidateBudget") != 28
        or plan.get("authorizationPolicy") != expected_auth
        or plan.get("fundingBoundarySensitivityPolicy", {}).get("mustMatchReadinessPolicyExactly") is not True
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-candidate-generation-protocol-v2.json"
    ):
        raise DatasetValidationError("E14 candidate-protocol v2 inputs or governance are invalid.")
    if any(
        item.get("lifecycleStatus") != "readiness-planned-not-generated-not-fit"
        or item.get("eligibility", {}).get("structurallyEligible") is not True
        for item in roster.get("candidates", [])
    ):
        raise DatasetValidationError("E14 candidate-protocol v2 roster contains non-ready entries.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid E14 {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


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
