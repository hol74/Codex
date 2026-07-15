from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "VINTAGE_POLICY_POST_2005_SCOPE_SELECTED_BANKING_CONTROLS_REQUIRED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]
FORBIDDEN_AUTHORIZATIONS = [
    "sourceAcquisitionAuthorized",
    "historicalArchiveAcquisitionAuthorized",
    "featureFoundationMaterializationAuthorized",
    "taxonomyMutationAuthorized",
    "candidateGenerationAuthorized",
    "candidateFittingAuthorized",
    "candidateEvaluationAuthorized",
    "candidateRankingAuthorized",
    "crossMechanismCompositionAuthorized",
    "outerOosAuthorized",
    "promotionAuthorized",
]


def write_e14_vintage_policy_decision_audit(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    hypothesis_plan_path: str | Path,
    replacement_feasibility_contract_path: str | Path,
    replacement_feasibility_audit_path: str | Path,
    decision_plan_path: str | Path,
    decision_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "vintage-policy contract", "taxonomy v5", "hypothesis plan",
        "replacement-feasibility contract", "replacement-feasibility audit",
        "vintage-policy plan", "vintage-policy schema",
    )
    paths = (
        contract_path, taxonomy_path, hypothesis_plan_path,
        replacement_feasibility_contract_path, replacement_feasibility_audit_path,
        decision_plan_path, decision_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract), (taxonomy_file, taxonomy_raw, taxonomy),
     (hypothesis_plan_file, hypothesis_plan_raw, hypothesis_plan),
     (feasibility_contract_file, feasibility_contract_raw, feasibility_contract),
     (feasibility_audit_file, feasibility_audit_raw, feasibility_audit),
     (decision_plan_file, decision_plan_raw, decision_plan),
     (decision_schema_file, decision_schema_raw, decision_schema)) = artifacts
    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "hypothesisPlanV1Sha256": _sha(hypothesis_plan_raw),
        "replacementFeasibilityContractV1Sha256": _sha(feasibility_contract_raw),
        "replacementFeasibilityAuditV1Sha256": _sha(feasibility_audit_raw),
        "vintagePolicyPlanV1Sha256": _sha(decision_plan_raw),
        "vintagePolicySchemaV1Sha256": _sha(decision_schema_raw),
    }
    _validate_governance(
        contract, taxonomy, hypothesis_plan, feasibility_contract,
        feasibility_audit, decision_plan, decision_schema, hashes,
    )

    alternatives = decision_plan["alternatives"]
    alternative_ids = [item["alternativeId"] for item in alternatives]
    if len(alternatives) != contract["expectedAlternativeCount"] or len(set(alternative_ids)) != len(alternative_ids):
        raise DatasetValidationError("E14.7d alternative roster is invalid.")
    selected = [item for item in alternatives if item["decision"] == "selected-conditionally"]
    if (
        len(selected) != 1
        or selected[0]["alternativeId"] != contract["expectedSelectedPolicy"]
        or decision_plan["selectedPolicy"] != contract["expectedSelectedPolicy"]
        or selected[0]["preservesEventTimeStandard"] is not True
        or selected[0]["requiresHistoricalObservationAcquisition"] is not False
    ):
        raise DatasetValidationError("E14.7d selected policy differs from the frozen decision.")

    scope = decision_plan["post2005Scope"]
    cutoff = date.fromisoformat(scope["cutoffInclusive"])
    if scope["cutoffInclusive"] != contract["expectedCutoffInclusive"]:
        raise DatasetValidationError("E14.7d cutoff differs from the frozen availability boundary.")
    episode_dates = _episode_dates(taxonomy)
    positive_by_mechanism = {}
    for mechanism in hypothesis_plan["mechanisms"]:
        name = mechanism["mechanism"]
        positive_by_mechanism[name] = sorted(
            signature["episodeId"] for signature in mechanism["episodeSignatures"]
            if episode_dates[signature["episodeId"]] >= cutoff
        )
    hard_negative_by_mechanism = {mechanism: [] for mechanism in MECHANISMS}
    for episode in taxonomy["hardNegativeEpisodes"]:
        if date.fromisoformat(episode["firstMonth"]) < cutoff:
            continue
        for mechanism in episode["mechanisms"]:
            hard_negative_by_mechanism[mechanism].append(episode["independentEventId"])
    hard_negative_by_mechanism = {
        mechanism: sorted(set(ids)) for mechanism, ids in hard_negative_by_mechanism.items()
    }

    positive_counts = {mechanism: len(positive_by_mechanism[mechanism]) for mechanism in MECHANISMS}
    hard_negative_counts = {
        mechanism: len(hard_negative_by_mechanism[mechanism]) for mechanism in MECHANISMS
    }
    unique_positive = sorted({item for ids in positive_by_mechanism.values() for item in ids})
    unique_hard_negative = sorted({item for ids in hard_negative_by_mechanism.values() for item in ids})
    positive_assignments = sum(positive_counts.values())
    hard_negative_assignments = sum(hard_negative_counts.values())
    if (
        positive_counts != contract["expectedPositiveEpisodeCounts"]
        or hard_negative_counts != contract["expectedHardNegativeEpisodeCounts"]
        or positive_counts != scope["expectedPositiveEpisodeCounts"]
        or hard_negative_counts != scope["expectedHardNegativeEpisodeCounts"]
        or len(unique_positive) != contract["expectedUniquePositiveEpisodeCount"]
        or positive_assignments != contract["expectedPositiveMechanismAssignmentCount"]
        or len(unique_hard_negative) != contract["expectedUniqueHardNegativeEpisodeCount"]
        or hard_negative_assignments != contract["expectedHardNegativeMechanismAssignmentCount"]
    ):
        raise DatasetValidationError("E14.7d post-2005 episode inventory differs from contract.")

    min_positive = scope["minimumPositiveEpisodesPerMechanism"]
    min_hard_negative = scope["minimumHardNegativeEpisodesPerMechanism"]
    positive_gaps = {
        mechanism: max(0, min_positive - positive_counts[mechanism]) for mechanism in MECHANISMS
    }
    hard_negative_gaps = {
        mechanism: max(0, min_hard_negative - hard_negative_counts[mechanism])
        for mechanism in MECHANISMS
    }
    if (
        any(positive_gaps.values())
        or hard_negative_gaps != {
            "banking-credit": scope["requiredBankingHardNegativeAdditions"],
            "broad-market-repricing": 0,
            "cross-border-growth": 0,
            "funding-liquidity": 0,
        }
        or scope["positiveIdentifiabilitySatisfied"] is not True
        or scope["hardNegativeIdentifiabilitySatisfied"] is not False
        or scope["scopeActivationStatus"] != "blocked-pending-banking-hard-negative-feasibility"
    ):
        raise DatasetValidationError("E14.7d identifiability decision is invalid.")

    output = Path(output_path).resolve()
    input_artifacts = {
        name: _artifact(file, raw) for name, (file, raw, _) in zip((
            "vintagePolicyContract", "taxonomyV5", "hypothesisPlanV1",
            "replacementFeasibilityContractV1", "replacementFeasibilityAuditV1",
            "vintagePolicyPlanV1", "vintagePolicySchemaV1",
        ), artifacts)
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14VintagePolicyDecisionAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "alternativeAssessments": alternatives,
        "selectedPolicy": {
            "policyId": decision_plan["selectedPolicy"],
            "selectionStatus": "selected-conditionally",
            "legacyE14Reopened": False,
            "post2005ScopeActivated": False,
        },
        "post2005ScopeAssessment": {
            "scopeId": scope["scopeId"],
            "cutoffInclusive": scope["cutoffInclusive"],
            "positiveEpisodeIdsByMechanism": positive_by_mechanism,
            "hardNegativeEpisodeIdsByMechanism": hard_negative_by_mechanism,
            "positiveEpisodeCounts": positive_counts,
            "hardNegativeEpisodeCounts": hard_negative_counts,
            "uniquePositiveEpisodeCount": len(unique_positive),
            "positiveMechanismAssignmentCount": positive_assignments,
            "uniqueHardNegativeEpisodeCount": len(unique_hard_negative),
            "hardNegativeMechanismAssignmentCount": hard_negative_assignments,
            "positiveIdentifiabilityGaps": positive_gaps,
            "hardNegativeIdentifiabilityGaps": hard_negative_gaps,
            "requiredBankingHardNegativeAdditions": hard_negative_gaps["banking-credit"],
            "scopeActivationStatus": scope["scopeActivationStatus"],
        },
        "checks": {
            "allInputHashesExact": True,
            "threeAlternativesAssessedExactlyOnce": True,
            "selectionUsesNoSeriesObservations": True,
            "selectionUsesNoLoeoScores": True,
            "selectionUsesNoOuterOos": True,
            "legacyE14RemainsClosed": True,
            "eventTimeStandardUnchanged": True,
            "cutoffBoundToAvailabilityEvidence": True,
            "minimumPositiveEpisodesSatisfiedPerMechanism": True,
            "bankingHardNegativeGapDetected": True,
            "taxonomyMutationStillClosed": True,
            "sourceAcquisitionStillClosed": True,
        },
        "decision": {
            "vintagePolicyPreregistered": True,
            "selectedPolicy": decision_plan["selectedPolicy"],
            "post2005ScopeFeasibilityDesignAuthorized": True,
            "bankingHardNegativeFeasibilityDesignAuthorized": True,
            "post2005ScopeActivationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "historicalArchiveAcquisitionAuthorized": False,
            "taxonomyMutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "protocol": {
            "metadataOnly": True,
            "seriesObservationDownloaded": False,
            "datasetRead": False,
            "loeoScoreRead": False,
            "outerFeatureRowCountUsed": 0,
            "taxonomyMutated": False,
            "candidateGenerated": False,
            "candidateEvaluated": False,
            "promotionPerformed": False,
        },
        "implementation": {
            "module": "regime_eval.e14_vintage_policy_decision",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output, payload)


def _episode_dates(taxonomy: dict[str, Any]) -> dict[str, date]:
    output = {}
    for episode in taxonomy["episodes"]:
        episode_id = episode["independentEventId"]
        value = date.fromisoformat(episode["firstMonth"])
        if episode_id in output and output[episode_id] != value:
            raise DatasetValidationError("E14.7d taxonomy has inconsistent episode dates.")
        output[episode_id] = value
    return output


def _validate_governance(
    contract: dict[str, Any], taxonomy: dict[str, Any], hypothesis_plan: dict[str, Any],
    feasibility_contract: dict[str, Any], feasibility_audit: dict[str, Any],
    decision_plan: dict[str, Any], decision_schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    auth = contract.get("authorizationPolicy", {})
    plan_auth = decision_plan.get("authorizations", {})
    governance = decision_plan.get("governance", {})
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-vintage-policy-decision-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or auth.get("vintagePolicyDecisionPreregistrationAuthorized") is not True
        or auth.get("post2005ScopeFeasibilityDesignAuthorized") is not True
        or auth.get("bankingHardNegativeFeasibilityDesignAuthorized") is not True
        or any(auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or taxonomy.get("schemaVersion") != 5
        or hypothesis_plan.get("planId") != "e14-new-information-hypothesis-plan-v1"
        or feasibility_contract.get("contractId")
        != "e14-replacement-source-feasibility-contract-v1"
        or feasibility_audit.get("status")
        != "REPLACEMENT_SOURCE_FEASIBILITY_BLOCKED_VINTAGE_POLICY_DECISION_REQUIRED"
        or feasibility_audit.get("decision", {}).get("sourceAcquisitionAuthorized") is not False
        or feasibility_audit.get("decision", {}).get("vintagePolicyDecisionPreregistrationAuthorized") is not True
        or decision_plan.get("planId") != "e14-vintage-policy-decision-plan-v1"
        or decision_schema.get("$id") != "e14-vintage-policy-decision-schema-v1"
        or plan_auth.get("post2005ScopeFeasibilityDesignAuthorized") is not True
        or plan_auth.get("bankingHardNegativeFeasibilityDesignAuthorized") is not True
        or any(plan_auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or governance.get("legacyE14ClosedAndImmutable") is not True
        or governance.get("legacyTaxonomyV5Unchanged") is not True
        or governance.get("selectedUsingSeriesObservations") is not False
        or governance.get("selectedUsingLoeoScores") is not False
        or governance.get("selectedUsingOuterOos") is not False
        or governance.get("observationDateCannotReplacePublicationAvailability") is not True
        or governance.get("cutoffCannotBeRetunedAfterEvaluation") is not True
        or governance.get("post2005ScopeMustUseNewVersionIdentifiers") is not True
        or governance.get("bankingHardNegativeGapMustBlockTaxonomyProposal") is not True
    )
    if invalid:
        raise DatasetValidationError("E14.7d inputs or governance are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    if not file.exists():
        raise DatasetValidationError(f"E14.7d {label} does not exist: {file}")
    raw = file.read_bytes()
    try:
        return file, raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7d {label} is not valid UTF-8 JSON.") from error


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write_new(path: Path, payload: dict[str, Any]) -> Path:
    if path.exists():
        raise DatasetValidationError("Immutable E14.7d vintage-policy audit output already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return path
