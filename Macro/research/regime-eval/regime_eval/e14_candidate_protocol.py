from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "RESEARCH_CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED"
REQUIRED_METRICS = [
    "episode-hit-rate",
    "episode-recall",
    "worst-episode-recall",
    "onset-delay-months",
    "recovery-lag-months",
    "hard-negative-alert-rate",
    "unlabeled-alert-count-reported-not-scored",
]


def write_e14_candidate_protocol_readiness(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    foundation_path: str | Path,
    foundation_lock_path: str | Path,
    foundation_audit_path: str | Path,
    mechanism_contract_path: str | Path,
    protocol_path: str | Path,
    protocol_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_raw, contract = _read(contract_path, "readiness contract")
    taxonomy_file, taxonomy_raw, taxonomy = _read(taxonomy_path, "taxonomy v5")
    foundation_file, foundation_raw, foundation = _read(foundation_path, "feature foundation")
    lock_file, lock_raw, lock = _read(foundation_lock_path, "feature foundation lock")
    audit_file, audit_raw, audit = _read(foundation_audit_path, "feature foundation audit")
    mechanism_file, mechanism_raw, mechanism = _read(mechanism_contract_path, "mechanism contract")
    protocol_file, protocol_raw, protocol = _read(protocol_path, "candidate protocol")
    schema_file, schema_raw, schema = _read(protocol_schema_path, "candidate protocol schema")
    _validate_inputs(
        contract, taxonomy, foundation, lock, audit, mechanism, protocol, schema,
        taxonomy_raw, foundation_raw, lock_raw, audit_raw, mechanism_raw,
        protocol_raw, schema_raw,
    )

    required = contract["requiredMechanisms"]
    binding_series: dict[str, set[str]] = {item: set() for item in required}
    for binding in foundation["detectorBindings"]:
        binding_series[binding["mechanism"]].add(binding["seriesId"])
    detector_ids = {item["mechanism"]: item["detectorId"] for item in mechanism["detectors"]}
    persistence_count = (
        len(protocol["persistence"]["entryPersistenceMonths"])
        * len(protocol["persistence"]["recoveryPersistenceMonths"])
    )
    derived_counts: dict[str, int] = {}
    grammar_checks = []
    for name in required:
        grammar = protocol["detectors"][name]
        profile_series = {
            series_id
            for profile in grammar["profiles"]
            for series_id in profile["seriesIds"]
        }
        count = len(grammar["profiles"]) * persistence_count
        derived_counts[name] = count
        grammar_checks.append(
            grammar["detectorId"] == detector_ids[name]
            and profile_series == binding_series[name]
            and all(set(profile["seriesIds"]).issubset(binding_series[name]) for profile in grammar["profiles"])
            and len({profile["profileId"] for profile in grammar["profiles"]}) == len(grammar["profiles"])
            and grammar["candidateCount"] == count
        )
    total_budget = sum(derived_counts.values())
    checks = {
        "taxonomyV5HashBound": protocol["taxonomyV5Sha256"] == hashlib.sha256(taxonomy_raw).hexdigest(),
        "featureFoundationHashBound": protocol["featureFoundationSha256"] == hashlib.sha256(foundation_raw).hexdigest(),
        "featureFoundationLockHashBound": protocol["featureFoundationLockSha256"] == hashlib.sha256(lock_raw).hexdigest(),
        "featureFoundationMaterialized": audit["decision"]["featureFoundationMaterialized"] is True,
        "allDetectorBindingsPopulated": audit["decision"]["allDetectorBindingsPopulated"] is True,
        "fourIndependentMechanismGrammars": all(grammar_checks),
        "candidateCountsDerivedExactly": derived_counts == contract["expectedCandidateCounts"],
        "finiteCandidateBudget": total_budget == protocol["candidateBudget"] == 40,
        "thresholdSelectionInnerOnly": protocol["thresholdSelection"]["scope"]
        == "inner-train-within-leave-one-episode-out",
        "causalTrainOnlyTransforms": protocol["constraints"]["causalFeaturesOnly"] is True
        and protocol["constraints"]["trainOnlyTransforms"] is True,
        "missingnessExplicitAndNoZeroImputation": protocol["constraints"]["missingValuesRemainExplicit"] is True
        and protocol["constraints"]["zeroImputationForbidden"] is True,
        "methodologySplicingForbidden": protocol["constraints"]["crossMethodologySplicingForbidden"] is True,
        "positiveAndHardNegativeEvaluationRequired": protocol["evaluationPolicy"]["positiveAndHardNegativeRequiredPerMechanism"] is True,
        "unlabeledMonthsAreNotNegatives": protocol["evaluationPolicy"]["unlabeledMonthsAreNotNegatives"] is True,
        "requiredMetricsComplete": protocol["evaluationPolicy"]["requiredMetrics"] == REQUIRED_METRICS,
        "crossMechanismFusionClosed": protocol["constraints"]["crossMechanismFusion"] is False
        and protocol["compositionPolicy"]["compositionAuthorized"] is False,
        "outerOosClosed": "Forbidden" in protocol["selectionPolicy"]["outerOos"],
        "vintageRiskResearchOnly": protocol["vintageRiskPolicy"]["currentHistorySnapshotsAcceptedForResearchGeneration"] is True
        and protocol["vintageRiskPolicy"]["strictVintageReady"] is False
        and protocol["vintageRiskPolicy"]["revisionSensitivityGateRequiredBeforePromotion"] is True
        and protocol["vintageRiskPolicy"]["operationalPromotionFromThisProtocolForbidden"] is True,
    }
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise DatasetValidationError(f"E14 four-detector protocol is not ready: {', '.join(failed)}")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FourDetectorProtocolReadinessAudit",
        "status": STATUS,
        "inputs": {
            "readinessContract": _artifact(contract_file, contract_raw),
            "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
            "featureFoundation": _artifact(foundation_file, foundation_raw),
            "featureFoundationLock": _artifact(lock_file, lock_raw),
            "featureFoundationAudit": _artifact(audit_file, audit_raw),
            "mechanismContract": _artifact(mechanism_file, mechanism_raw),
            "candidateProtocol": _artifact(protocol_file, protocol_raw),
            "candidateProtocolSchema": _artifact(schema_file, schema_raw),
        },
        "inventory": {
            "mechanismCount": len(required),
            "uniqueSeriesCount": len(foundation["series"]),
            "detectorBindingCount": len(foundation["detectorBindings"]),
            "profileCount": sum(len(item["profiles"]) for item in protocol["detectors"].values()),
            "persistenceCombinationCount": persistence_count,
            "candidateBudget": total_budget,
            "candidateCountByMechanism": derived_counts,
        },
        "checks": checks,
        "reusedE13Controls": [
            "deterministic-enumeration",
            "causal-features-only",
            "train-only-transforms",
            "missingness-explicit",
            "leave-one-episode-out-inner-selection",
            "outer-oos-forbidden",
        ],
        "replacedE13Dependencies": [
            "e12-foundation-lock-replaced-by-e14-feature-foundation-lock",
            "two-task-grammar-replaced-by-four-independent-mechanism-grammars",
            "aggregate-task-metrics-replaced-by-mechanism-episode-and-month-metrics",
        ],
        "protocol": {
            "candidateGenerated": False,
            "candidateEvaluated": False,
            "outerFeatureRowCountUsed": 0,
            "crossMechanismCompositionPerformed": False,
            "promotionPerformed": False,
            "taxonomyMutated": False,
        },
        "decision": {
            "protocolFrozen": True,
            "researchCandidateGenerationReady": True,
            "researchCandidateGenerationAuthorized": True,
            "candidateEvaluationAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "strictVintageReady": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_candidate_protocol",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new(output_path, payload)


def _validate_inputs(
    contract: Any, taxonomy: Any, foundation: Any, lock: Any, audit: Any,
    mechanism: Any, protocol: Any, schema: Any, taxonomy_raw: bytes,
    foundation_raw: bytes, lock_raw: bytes, audit_raw: bytes, mechanism_raw: bytes,
    protocol_raw: bytes, schema_raw: bytes,
) -> None:
    hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "featureFoundationSha256": hashlib.sha256(foundation_raw).hexdigest(),
        "featureFoundationLockSha256": hashlib.sha256(lock_raw).hexdigest(),
        "featureFoundationAuditSha256": hashlib.sha256(audit_raw).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_raw).hexdigest(),
        "candidateProtocolSha256": hashlib.sha256(protocol_raw).hexdigest(),
        "candidateProtocolSchemaSha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    expected_policy = {
        "taxonomyV5HashBound": True,
        "featureFoundationAndLockHashBound": True,
        "allDetectorBindingsRequired": True,
        "oneIndependentGrammarPerMechanism": True,
        "finiteCandidateBudgetRequired": True,
        "thresholdsSelectedInnerOnly": True,
        "causalTrainOnlyTransformsRequired": True,
        "missingnessExplicitRequired": True,
        "methodologySplicingForbidden": True,
        "positiveAndHardNegativeEvaluationRequired": True,
        "unlabeledMonthsAreNotNegatives": True,
        "compositionClosedUntilIndependentGates": True,
        "vintageLimitationsAcceptedForResearchOnly": True,
        "revisionSensitivityRequiredBeforePromotion": True,
    }
    expected_auth = {
        "protocolFreezeAuthorized": True,
        "researchCandidateGenerationAuthorizedOnPass": True,
        "candidateEvaluationAuthorized": False,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
        "taxonomyMutationAuthorized": False,
    }
    if (
        contract.get("contractId") != "e14-four-detector-protocol-readiness-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("readinessPolicy") != expected_policy
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v1"
        or lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v1"
        or lock.get("foundation", {}).get("sha256") != hashes["featureFoundationSha256"]
        or lock.get("taxonomyV5", {}).get("sha256") != hashes["taxonomyV5Sha256"]
        or lock.get("candidateGenerationAuthorized") is not False
        or audit.get("status") != "FEATURE_FOUNDATION_MATERIALIZED_WITH_VINTAGE_LIMITATIONS"
        or audit.get("decision", {}).get("taxonomyV5ProtocolDesignAuthorized") is not True
        or mechanism.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or protocol.get("protocolId") != "e14-four-detector-candidate-generation-protocol-v1"
        or set(protocol.get("detectors", {})) != set(contract.get("requiredMechanisms", []))
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-candidate-protocol-v1.json"
    ):
        raise DatasetValidationError("E14 candidate-protocol inputs or contract are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E14 candidate-protocol audit already exists: '{destination}'.") from exc
    return destination
