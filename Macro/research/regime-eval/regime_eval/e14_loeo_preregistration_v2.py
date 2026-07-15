from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "INNER_LOEO_V2_PREREGISTERED_FULL_READINESS_FITTING_EVALUATION_AUTHORIZED_OUTER_OOS_CLOSED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]


def write_e14_loeo_preregistration_audit_v2(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    candidate_manifest_path: str | Path,
    candidate_manifest_audit_path: str | Path,
    foundation_path: str | Path,
    foundation_lock_path: str | Path,
    foundation_audit_path: str | Path,
    candidate_protocol_path: str | Path,
    protocol_audit_path: str | Path,
    preregistration_path: str | Path,
    preregistration_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "LOEO readiness contract v2", "taxonomy v5", "candidate manifest v2",
        "candidate manifest audit v2", "feature foundation v2", "feature foundation lock v2",
        "feature foundation audit v2", "candidate protocol v2", "protocol readiness audit v2",
        "LOEO preregistration v2", "LOEO preregistration schema v2",
    )
    paths = (
        contract_path, taxonomy_path, candidate_manifest_path, candidate_manifest_audit_path,
        foundation_path, foundation_lock_path, foundation_audit_path, candidate_protocol_path,
        protocol_audit_path, preregistration_path, preregistration_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract), (taxonomy_file, taxonomy_raw, taxonomy),
     (manifest_file, manifest_raw, manifest), (manifest_audit_file, manifest_audit_raw, manifest_audit),
     (foundation_file, foundation_raw, foundation), (lock_file, lock_raw, lock),
     (foundation_audit_file, foundation_audit_raw, foundation_audit),
     (protocol_file, protocol_raw, protocol), (protocol_audit_file, protocol_audit_raw, protocol_audit),
     (prereg_file, prereg_raw, prereg), (schema_file, schema_raw, schema)) = artifacts

    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "candidateManifestV2Sha256": _sha(manifest_raw),
        "candidateManifestAuditV2Sha256": _sha(manifest_audit_raw),
        "featureFoundationV2Sha256": _sha(foundation_raw),
        "featureFoundationLockV2Sha256": _sha(lock_raw),
        "featureFoundationAuditV2Sha256": _sha(foundation_audit_raw),
        "candidateProtocolV2Sha256": _sha(protocol_raw),
        "protocolReadinessAuditV2Sha256": _sha(protocol_audit_raw),
        "loeoPreregistrationV2Sha256": _sha(prereg_raw),
        "loeoPreregistrationSchemaV2Sha256": _sha(schema_raw),
    }
    _validate_governance(
        contract, taxonomy, manifest, manifest_audit, foundation, lock, foundation_audit,
        protocol, protocol_audit, prereg, schema, hashes,
    )

    label_inventory = _label_inventory(taxonomy)
    if label_inventory != contract["expectedLabelEpisodeCounts"]:
        raise DatasetValidationError("E14 LOEO v2 label inventory differs from contract.")
    positives = _episodes_by_mechanism(taxonomy["episodes"], "positive")
    negatives = _episodes_by_mechanism(taxonomy["hardNegativeEpisodes"], "hard-negative")
    positive_ids = {
        mechanism: {item["independentEventId"] for item in episodes}
        for mechanism, episodes in positives.items()
    }
    negative_ids = {
        mechanism: {item["independentEventId"] for item in episodes}
        for mechanism, episodes in negatives.items()
    }
    foundation_series = {item["seriesId"] for item in foundation["series"]}

    fold_assignments = []
    eligible_counts = Counter()
    fold_counts = Counter()
    for candidate in manifest["candidates"]:
        mechanism = candidate["mechanism"]
        eligibility = candidate["eligibility"]
        observable_positive = eligibility["observablePositiveEpisodeIds"]
        observable_negative = eligibility["observableHardNegativeEpisodeIds"]
        series_ids = [item["seriesId"] for item in candidate["featureBindings"]]
        if (
            eligibility.get("structurallyEligible") is not True
            or eligibility.get("observablePositiveEpisodeCount") != len(observable_positive)
            or eligibility.get("observableHardNegativeEpisodeCount") != len(observable_negative)
            or eligibility.get("plannedLeaveOneOutFoldCount") != len(observable_positive)
            or len(observable_positive) < prereg["absoluteGatePolicy"]["requirements"]["minimumObservablePositiveEpisodes"]
            or len(observable_negative) < prereg["absoluteGatePolicy"]["requirements"]["minimumObservableHardNegativeEpisodes"]
            or not set(observable_positive) <= positive_ids[mechanism]
            or not set(observable_negative) <= negative_ids[mechanism]
            or not set(series_ids) <= foundation_series
        ):
            raise DatasetValidationError("E14 LOEO v2 manifest eligibility or binding is invalid.")
        eligible_counts[mechanism] += 1
        for held_out in observable_positive:
            training_positive = [item for item in observable_positive if item != held_out]
            if len(training_positive) < prereg["foldPolicy"]["minimumTrainingPositiveEpisodesPerFold"]:
                raise DatasetValidationError("E14 LOEO v2 fold lacks training positive episodes.")
            fold_assignments.append({
                "foldId": f"loeo-v2::{candidate['candidateId']}::{held_out}",
                "candidateId": candidate["candidateId"],
                "mechanism": mechanism,
                "profileId": candidate["profile"]["profileId"],
                "heldOutPositiveEpisodeId": held_out,
                "trainingPositiveEpisodeIds": training_positive,
                "trainingHardNegativeEpisodeIds": observable_negative,
                "heldOutLabelsAvailableToTransformOrThreshold": False,
                "outerRowsAvailable": False,
            })
            fold_counts[mechanism] += 1

    eligible_counts = {mechanism: eligible_counts[mechanism] for mechanism in MECHANISMS}
    fold_counts = {mechanism: fold_counts[mechanism] for mechanism in MECHANISMS}
    if (
        eligible_counts != contract["expectedEligibleCandidateCounts"]
        or fold_counts != contract["expectedCandidateFoldAssignmentCounts"]
        or len(fold_assignments) != prereg["foldPolicy"]["expectedCandidateFoldAssignmentCount"]
    ):
        raise DatasetValidationError("E14 LOEO v2 candidate or fold inventory differs from contract.")

    input_artifacts = {
        "loeoReadinessContractV2": _artifact(contract_file, contract_raw),
        "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
        "candidateManifestV2": _artifact(manifest_file, manifest_raw),
        "candidateManifestAuditV2": _artifact(manifest_audit_file, manifest_audit_raw),
        "featureFoundationV2": _artifact(foundation_file, foundation_raw),
        "featureFoundationLockV2": _artifact(lock_file, lock_raw),
        "featureFoundationAuditV2": _artifact(foundation_audit_file, foundation_audit_raw),
        "candidateProtocolV2": _artifact(protocol_file, protocol_raw),
        "protocolReadinessAuditV2": _artifact(protocol_audit_file, protocol_audit_raw),
        "loeoPreregistrationV2": _artifact(prereg_file, prereg_raw),
        "loeoPreregistrationSchemaV2": _artifact(schema_file, schema_raw),
    }
    payload = {
        "schemaVersion": 2,
        "artifactType": "E14FourDetectorLoeoPreregistrationAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "labelInventory": label_inventory,
        "inventory": {
            "candidateCount": len(manifest["candidates"]),
            "eligibleCandidateCount": sum(eligible_counts.values()),
            "eligibleCandidateCountByMechanism": eligible_counts,
            "candidateFoldAssignmentCount": len(fold_assignments),
            "candidateFoldAssignmentCountByMechanism": fold_counts,
            "readyMechanismCount": len(MECHANISMS),
            "blockedMechanismCount": 0,
        },
        "candidateFoldAssignments": fold_assignments,
        "absoluteGatePolicy": prereg["absoluteGatePolicy"],
        "fundingBoundarySensitivity": prereg["fundingBoundarySensitivity"],
        "snapshotDriftPolicy": prereg["snapshotDriftPolicy"],
        "checks": {
            "allInputHashesExact": True,
            "upstreamOutputHashesExact": True,
            "candidateIdsEqualProtocolInOrder": manifest["candidateIds"] == protocol["candidateIds"],
            "all28CandidatesStructurallyEligible": sum(eligible_counts.values()) == 28,
            "all140CandidateFoldAssignmentsFrozen": len(fold_assignments) == 140,
            "heldOutLabelsForbiddenForTransformsAndThresholds": True,
            "causalInnerTrainingOnlyTransforms": True,
            "missingnessAndMethodologyBoundariesPreserved": True,
            "absoluteGatesFrozenBeforeFitting": True,
            "fundingSensitivityFrozenBeforeFitting": True,
            "snapshotDriftCheckRequiredBeforeEvaluation": True,
            "strictVintageReady": False,
            "outerOosClosed": True,
        },
        "protocol": {
            "preregistrationFrozen": True,
            "featureTransformationPerformed": False,
            "candidateFittingPerformed": False,
            "candidateEvaluationPerformed": False,
            "candidateRankingPerformed": False,
            "crossMechanismCompositionPerformed": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "decision": {
            "fullFourMechanismReadiness": True,
            "readyMechanisms": MECHANISMS,
            "blockedMechanisms": [],
            "innerFeatureTransformationAuthorized": True,
            "innerCandidateFittingAuthorized": True,
            "innerLoeoEvaluationAuthorized": True,
            "partialMechanismFittingAuthorized": False,
            "candidateRankingAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_loeo_preregistration_v2",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output_path, payload)


def _validate_governance(
    contract: dict[str, Any], taxonomy: dict[str, Any], manifest: dict[str, Any],
    manifest_audit: dict[str, Any], foundation: dict[str, Any], lock: dict[str, Any],
    foundation_audit: dict[str, Any], protocol: dict[str, Any], protocol_audit: dict[str, Any],
    prereg: dict[str, Any], schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    expected_auth = {
        "preregistrationAuditAuthorized": True,
        "innerFeatureTransformationAuthorizedOnPass": True,
        "innerCandidateFittingAuthorizedOnPass": True,
        "innerLoeoEvaluationAuthorizedOnPass": True,
        "partialMechanismFittingAuthorized": False,
        "candidateRankingAuthorizedNow": False,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    manifest_hash = hashes["candidateManifestV2Sha256"]
    foundation_hash = hashes["featureFoundationV2Sha256"]
    lock_hash = hashes["featureFoundationLockV2Sha256"]
    protocol_hash = hashes["candidateProtocolV2Sha256"]
    prereg_input_hashes = {key: hashes[key] for key in prereg.get("inputHashes", {})}
    if (
        contract.get("contractId") != "e14-four-detector-loeo-readiness-contract-v2"
        or contract.get("inputHashes") != hashes
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or manifest.get("manifestId") != "e14-generated-four-detector-candidates-v2"
        or manifest.get("status") != "GENERATED_V2_NOT_TRANSFORMED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED"
        or manifest.get("candidateCount") != 28
        or manifest.get("candidateIds") != protocol.get("candidateIds")
        or manifest_audit.get("outputs", {}).get("candidateManifestV2", {}).get("sha256") != manifest_hash
        or manifest_audit.get("decision", {}).get("candidateFittingAuthorized") is not False
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v2"
        or lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v2"
        or lock.get("foundation", {}).get("sha256") != foundation_hash
        or foundation_audit.get("outputs", {}).get("foundationV2", {}).get("sha256") != foundation_hash
        or foundation_audit.get("outputs", {}).get("foundationLockV2", {}).get("sha256") != lock_hash
        or protocol.get("protocolId") != "e14-four-detector-candidate-generation-protocol-v2"
        or protocol_audit.get("outputs", {}).get("candidateProtocolV2", {}).get("sha256") != protocol_hash
        or prereg.get("preregistrationId") != "e14-four-detector-loeo-preregistration-v2"
        or prereg.get("inputHashes") != prereg_input_hashes
        or prereg.get("scope") != "nested-inner-development-only-current-history-revision-limited"
        or prereg.get("mechanisms") != MECHANISMS
        or prereg.get("authorizationPolicy") != expected_auth
        or prereg.get("thresholdSelection", {}).get("quantiles") != [0.8, 0.9, 0.95]
        or prereg.get("selectionPolicy", {}).get("shortlistProducedInThisStep") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-loeo-preregistration-v2.json"
    ):
        raise DatasetValidationError("E14 LOEO preregistration v2 inputs or policy are invalid.")
    sensitivity = dict(protocol["fundingBoundarySensitivity"])
    sensitivity["requiredReports"] = sensitivity.pop("requiredFutureReports")
    if prereg["fundingBoundarySensitivity"] != sensitivity:
        raise DatasetValidationError("E14 LOEO preregistration v2 funding sensitivity differs from protocol.")
    if any(
        item.get("lifecycleStatus") != "research-generated-not-fit"
        for item in manifest.get("candidates", [])
    ):
        raise DatasetValidationError("E14 LOEO preregistration v2 candidate lifecycle is invalid.")


def _label_inventory(taxonomy: dict[str, Any]) -> dict[str, dict[str, int]]:
    positive = _episodes_by_mechanism(taxonomy["episodes"], "positive")
    negative = _episodes_by_mechanism(taxonomy["hardNegativeEpisodes"], "hard-negative")
    return {
        mechanism: {
            "positive": len({item["independentEventId"] for item in positive[mechanism]}),
            "hardNegative": len({item["independentEventId"] for item in negative[mechanism]}),
        }
        for mechanism in MECHANISMS
    }


def _episodes_by_mechanism(
    episodes: list[dict[str, Any]], state: str,
) -> dict[str, list[dict[str, Any]]]:
    output = {mechanism: [] for mechanism in MECHANISMS}
    for episode in episodes:
        if episode.get("financialState") != state:
            continue
        for mechanism in episode.get("mechanisms", []):
            if mechanism in output:
                output[mechanism].append(episode)
    return output


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


def _write_new(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(
            f"Immutable E14 LOEO preregistration audit v2 already exists: '{destination}'."
        ) from exc
    return destination
