from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "POST_2005_SCOPE_FEASIBLE_TAXONOMY_PROPOSAL_PREREGISTRATION_AUTHORIZED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]
FORBIDDEN_AUTHORIZATIONS = [
    "sourceAcquisitionAuthorized",
    "featureFoundationMaterializationAuthorized",
    "taxonomyMutationAuthorized",
    "candidateGenerationAuthorized",
    "candidateFittingAuthorized",
    "candidateEvaluationAuthorized",
    "outerOosAuthorized",
    "promotionAuthorized",
]


def write_e14_post2005_scope_feasibility_audit(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    vintage_policy_contract_path: str | Path,
    vintage_policy_plan_path: str | Path,
    vintage_policy_audit_path: str | Path,
    scope_plan_path: str | Path,
    source_evidence_path: str | Path,
    scope_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "scope-feasibility contract",
        "taxonomy v5",
        "vintage-policy contract",
        "vintage-policy plan",
        "vintage-policy audit",
        "post-2005 scope plan",
        "post-2005 source evidence",
        "post-2005 scope schema",
    )
    paths = (
        contract_path,
        taxonomy_path,
        vintage_policy_contract_path,
        vintage_policy_plan_path,
        vintage_policy_audit_path,
        scope_plan_path,
        source_evidence_path,
        scope_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (
        (contract_file, contract_raw, contract),
        (taxonomy_file, taxonomy_raw, taxonomy),
        (vintage_contract_file, vintage_contract_raw, vintage_contract),
        (vintage_plan_file, vintage_plan_raw, vintage_plan),
        (vintage_audit_file, vintage_audit_raw, vintage_audit),
        (scope_plan_file, scope_plan_raw, scope_plan),
        (evidence_file, evidence_raw, evidence),
        (scope_schema_file, scope_schema_raw, scope_schema),
    ) = artifacts
    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "vintagePolicyContractV1Sha256": _sha(vintage_contract_raw),
        "vintagePolicyPlanV1Sha256": _sha(vintage_plan_raw),
        "vintagePolicyAuditV1Sha256": _sha(vintage_audit_raw),
        "scopePlanV1Sha256": _sha(scope_plan_raw),
        "sourceEvidenceV1Sha256": _sha(evidence_raw),
        "scopeSchemaV1Sha256": _sha(scope_schema_raw),
    }
    _validate_governance(
        contract,
        taxonomy,
        vintage_contract,
        vintage_plan,
        vintage_audit,
        scope_plan,
        evidence,
        scope_schema,
        hashes,
    )

    cutoff = date.fromisoformat(scope_plan["cutoffInclusive"])
    positives = {
        item["independentEventId"]: item
        for item in taxonomy["episodes"]
        if item.get("financialState") == "positive"
        and date.fromisoformat(item["firstMonth"]) >= cutoff
    }
    documentary = {item["sourceId"]: item for item in evidence["documentaryEvidence"]}
    sources = {item["sourceId"]: item for item in evidence["sources"]}
    if len(documentary) != len(evidence["documentaryEvidence"]) or len(sources) != len(evidence["sources"]):
        raise DatasetValidationError("E14.7e evidence source IDs must be unique.")

    candidate_assessments = []
    candidate_ids = []
    for candidate in scope_plan["bankingHardNegativeCandidates"]:
        candidate_id = candidate["independentEventId"]
        candidate_ids.append(candidate_id)
        first = date.fromisoformat(candidate["firstMonth"])
        last = date.fromisoformat(candidate["lastMonth"])
        if first < cutoff or last < first or candidate["mechanism"] != "banking-credit":
            raise DatasetValidationError("E14.7e banking hard-negative candidate boundary is invalid.")
        overlaps = sorted(
            episode_id
            for episode_id, episode in positives.items()
            if _overlaps(
                first,
                last,
                date.fromisoformat(episode["firstMonth"]),
                date.fromisoformat(episode["lastMonth"]),
            )
        )
        event_sources = candidate["eventEvidenceSourceIds"]
        containment_sources = candidate["containmentEvidenceSourceIds"]
        referenced = set(event_sources + containment_sources)
        if any(source_id not in documentary and source_id not in sources for source_id in referenced):
            raise DatasetValidationError("E14.7e candidate references unknown documentary evidence.")
        event_ready = bool(event_sources) and all(
            documentary.get(source_id, {}).get("providerPrimary") is True
            and documentary.get(source_id, {}).get("eventIdentityVerified") is True
            for source_id in event_sources
        )
        containment_ready = bool(containment_sources) and any(
            documentary.get(source_id, {}).get("providerPrimary") is True
            and documentary.get(source_id, {}).get("systemContainmentEvidence") is True
            for source_id in containment_sources
        )
        ready = event_ready and containment_ready and not overlaps
        candidate_assessments.append(
            {
                "candidateId": candidate["candidateId"],
                "independentEventId": candidate_id,
                "firstMonth": candidate["firstMonth"],
                "lastMonth": candidate["lastMonth"],
                "positiveWindowOverlapIds": overlaps,
                "providerPrimaryEventEvidenceReady": event_ready,
                "independentSystemContainmentEvidenceReady": containment_ready,
                "documentaryFeasibilityStatus": "ready" if ready else "blocked",
            }
        )
    if (
        len(candidate_ids) != contract["expectedNewBankingHardNegativeCandidateCount"]
        or len(set(candidate_ids)) != len(candidate_ids)
        or sorted(candidate_ids) != sorted(contract["expectedBankingHardNegativeCandidateIds"])
        or any(item["documentaryFeasibilityStatus"] != "ready" for item in candidate_assessments)
    ):
        raise DatasetValidationError("E14.7e banking hard-negative candidates are not feasible.")

    source_assessments = []
    ready_source_ids = set()
    for source_id, item in sources.items():
        ready = (
            item["providerPrimaryPageReachable"] is True
            and item["licensingCleared"] is True
            and item["componentCoverageVerified"] is True
            and item["releaseProofComplete"] is True
            and item["vintageProofComplete"] is True
            and item["methodologyManifestFeasible"] is True
            and item["blockingReasons"] == []
        )
        if ready:
            ready_source_ids.add(source_id)
        source_assessments.append(
            {
                "sourceId": source_id,
                "coverageFrom": item["coverageFrom"],
                "status": "ready" if ready else "blocked",
                "blockingReasons": item["blockingReasons"],
            }
        )

    family_assessments = []
    ready_by_mechanism = Counter()
    for family in scope_plan["post2005FeatureFamilies"]:
        mechanism = family["mechanism"]
        if mechanism not in MECHANISMS or any(source_id not in sources for source_id in family["sourceIds"]):
            raise DatasetValidationError("E14.7e feature-family roster is invalid.")
        applicable_ids = family["applicablePositiveEpisodeIds"]
        if not applicable_ids or any(episode_id not in positives for episode_id in applicable_ids):
            raise DatasetValidationError("E14.7e family references a non-scope positive episode.")
        earliest = min(date.fromisoformat(positives[item]["firstMonth"]) for item in applicable_ids)
        latest_start = max(date.fromisoformat(sources[item]["coverageFrom"]) for item in family["sourceIds"])
        available_history = _whole_months(latest_start, earliest)
        ready = (
            all(source_id in ready_source_ids for source_id in family["sourceIds"])
            and available_history >= family["minimumHistoryMonths"]
        )
        if ready:
            ready_by_mechanism[mechanism] += 1
        family_assessments.append(
            {
                "familyId": family["familyId"],
                "mechanism": mechanism,
                "sourceIds": family["sourceIds"],
                "availableHistoryMonthsBeforeEarliestPositive": available_history,
                "minimumHistoryMonths": family["minimumHistoryMonths"],
                "status": "ready" if ready else "blocked",
            }
        )

    minimum_families = scope_plan["feasibilityCriteria"]["minimumReadyFeatureFamiliesPerMechanism"]
    family_counts = {mechanism: ready_by_mechanism[mechanism] for mechanism in MECHANISMS}
    if family_counts != contract["expectedReadyFeatureFamilyCounts"] or any(
        count < minimum_families for count in family_counts.values()
    ):
        raise DatasetValidationError("E14.7e post-2005 source/family feasibility gate failed.")

    prior_scope = vintage_audit["post2005ScopeAssessment"]
    positive_counts = prior_scope["positiveEpisodeCounts"]
    hard_negative_counts = dict(prior_scope["hardNegativeEpisodeCounts"])
    hard_negative_counts["banking-credit"] += len(candidate_ids)
    minimum_controls = scope_plan["feasibilityCriteria"]["minimumHardNegativeEpisodesPerMechanism"]
    if (
        positive_counts != contract["expectedPositiveEpisodeCounts"]
        or hard_negative_counts != contract["expectedHardNegativeEpisodeCountsAfterCandidates"]
        or any(value < minimum_controls for value in hard_negative_counts.values())
    ):
        raise DatasetValidationError("E14.7e post-2005 episode identifiability gate failed.")

    output = Path(output_path).resolve()
    input_names = (
        "scopeFeasibilityContract",
        "taxonomyV5",
        "vintagePolicyContractV1",
        "vintagePolicyPlanV1",
        "vintagePolicyAuditV1",
        "scopePlanV1",
        "sourceEvidenceV1",
        "scopeSchemaV1",
    )
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005ScopeFeasibilityAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(input_names, artifacts)
        },
        "scopeAssessment": {
            "scopeId": scope_plan["scopeId"],
            "cutoffInclusive": scope_plan["cutoffInclusive"],
            "positiveEpisodeCounts": positive_counts,
            "hardNegativeEpisodeCountsAfterCandidates": hard_negative_counts,
            "positiveIdentifiabilitySatisfied": True,
            "hardNegativeIdentifiabilitySatisfied": True,
            "sourceFeasibilitySatisfied": True,
        },
        "bankingHardNegativeCandidateAssessments": candidate_assessments,
        "sourceAssessments": source_assessments,
        "featureFamilyAssessments": family_assessments,
        "readyFeatureFamilyCounts": family_counts,
        "checks": {
            "allInputHashesExact": True,
            "candidateEventsIndependent": True,
            "candidateWindowsDoNotOverlapPositiveWindows": True,
            "providerPrimaryEventEvidenceComplete": True,
            "independentContainmentEvidenceComplete": True,
            "minimumControlsSatisfiedPerMechanism": True,
            "minimumReadyFamilySatisfiedPerMechanism": True,
            "blockedLegacyFamiliesNotAutomaticallyInherited": True,
            "legacyE14RemainsClosed": True,
            "taxonomyV5Unchanged": True,
        },
        "decision": {
            "post2005ScopeFeasible": True,
            "bankingHardNegativeDocumentaryFeasibilitySatisfied": True,
            "taxonomyProposalPreregistrationAuthorized": True,
            "post2005ScopeActivated": False,
            "sourceAcquisitionAuthorized": False,
            "featureFoundationMaterializationAuthorized": False,
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
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_scope_feasibility",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output, payload)


def _validate_governance(
    contract: dict[str, Any],
    taxonomy: dict[str, Any],
    vintage_contract: dict[str, Any],
    vintage_plan: dict[str, Any],
    vintage_audit: dict[str, Any],
    scope_plan: dict[str, Any],
    evidence: dict[str, Any],
    scope_schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    auth = contract.get("authorizationPolicy", {})
    plan_auth = scope_plan.get("authorizations", {})
    governance = scope_plan.get("governance", {})
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-post2005-scope-feasibility-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or auth.get("post2005ScopeFeasibilityAuditAuthorized") is not True
        or auth.get("taxonomyProposalPreregistrationAuthorized") is not True
        or any(auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or taxonomy.get("schemaVersion") != 5
        or vintage_contract.get("contractId") != "e14-vintage-policy-decision-contract-v1"
        or vintage_plan.get("selectedPolicy") != "separately-versioned-post-2005-research-scope"
        or vintage_audit.get("status")
        != "VINTAGE_POLICY_POST_2005_SCOPE_SELECTED_BANKING_CONTROLS_REQUIRED"
        or vintage_audit.get("decision", {}).get("post2005ScopeFeasibilityDesignAuthorized") is not True
        or scope_plan.get("planId") != "e14-post2005-scope-feasibility-plan-v1"
        or scope_plan.get("scopeId") != "e14-post-2005-research-scope-proposal-v1"
        or scope_plan.get("cutoffInclusive") != "2006-01-01"
        or scope_schema.get("$id") != "e14-post2005-scope-feasibility-schema-v1"
        or evidence.get("evidencePackId") != "e14-post2005-source-feasibility-evidence-v1"
        or evidence.get("networkPolicy") != "provider-metadata-only-no-series-observation-download"
        or plan_auth.get("post2005ScopeFeasibilityAuditAuthorized") is not True
        or plan_auth.get("taxonomyProposalPreregistrationAuthorized") is not True
        or any(plan_auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or governance.get("legacyE14ClosedAndImmutable") is not True
        or governance.get("legacyTaxonomyV5Unchanged") is not True
        or governance.get("blockedE14cFamiliesNotAutomaticallyInherited") is not True
        or governance.get("feasibilityDoesNotConstituteLabelAcceptance") is not True
        or governance.get("independentReviewRequiredBeforeTaxonomyProposalAcceptance") is not True
    )
    if invalid:
        raise DatasetValidationError("E14.7e inputs or governance are invalid.")


def _overlaps(first_a: date, last_a: date, first_b: date, last_b: date) -> bool:
    return first_a <= last_b and first_b <= last_a


def _whole_months(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + end.month - start.month


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    if not file.exists():
        raise DatasetValidationError(f"E14.7e {label} does not exist: {file}")
    raw = file.read_bytes()
    try:
        return file, raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7e {label} is not valid UTF-8 JSON.") from error


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write_new(path: Path, payload: dict[str, Any]) -> Path:
    if path.exists():
        raise DatasetValidationError("Immutable E14.7e scope-feasibility audit output already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return path
