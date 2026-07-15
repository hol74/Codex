from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "FEASIBILITY_REMEDIATION_PREREGISTERED_REAUDIT_REQUIRED"
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
    "candidateRankingAuthorized",
    "crossMechanismCompositionAuthorized",
    "outerOosAuthorized",
    "promotionAuthorized",
]


def write_e14_feasibility_remediation_audit(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    hypothesis_plan_path: str | Path,
    hypothesis_audit_path: str | Path,
    feasibility_contract_path: str | Path,
    feasibility_evidence_path: str | Path,
    feasibility_audit_path: str | Path,
    remediation_plan_path: str | Path,
    remediation_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "remediation contract", "taxonomy v5", "hypothesis plan",
        "hypothesis audit", "source-feasibility contract", "source-feasibility evidence",
        "source-feasibility audit", "remediation plan", "remediation schema",
    )
    paths = (
        contract_path, taxonomy_path, hypothesis_plan_path, hypothesis_audit_path,
        feasibility_contract_path, feasibility_evidence_path, feasibility_audit_path,
        remediation_plan_path, remediation_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract), (taxonomy_file, taxonomy_raw, taxonomy),
     (hypothesis_plan_file, hypothesis_plan_raw, hypothesis_plan),
     (hypothesis_audit_file, hypothesis_audit_raw, hypothesis_audit),
     (feasibility_contract_file, feasibility_contract_raw, feasibility_contract),
     (feasibility_evidence_file, feasibility_evidence_raw, feasibility_evidence),
     (feasibility_audit_file, feasibility_audit_raw, feasibility_audit),
     (remediation_plan_file, remediation_plan_raw, remediation_plan),
     (remediation_schema_file, remediation_schema_raw, remediation_schema)) = artifacts
    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "hypothesisPlanV1Sha256": _sha(hypothesis_plan_raw),
        "hypothesisAuditV1Sha256": _sha(hypothesis_audit_raw),
        "feasibilityContractV1Sha256": _sha(feasibility_contract_raw),
        "feasibilityEvidenceV1Sha256": _sha(feasibility_evidence_raw),
        "feasibilityAuditV1Sha256": _sha(feasibility_audit_raw),
        "remediationPlanV1Sha256": _sha(remediation_plan_raw),
        "remediationSchemaV1Sha256": _sha(remediation_schema_raw),
    }
    _validate_governance(
        contract, taxonomy, hypothesis_plan, hypothesis_audit, feasibility_contract,
        feasibility_evidence, feasibility_audit, remediation_plan, remediation_schema, hashes,
    )

    prior_conditional = {
        item["familyId"] for item in feasibility_audit["familyAssessments"]
        if item["status"] == "conditional"
    }
    prior_blocked = {
        item["familyId"] for item in feasibility_audit["familyAssessments"]
        if item["status"] == "blocked"
    }
    preserved = {item["familyId"] for item in remediation_plan["preservedConditionalFamilies"]}
    retired = {item["familyId"] for item in remediation_plan["retiredFamilies"]}
    if preserved != prior_conditional or retired != prior_blocked:
        raise DatasetValidationError("E14.7b preserve/retire sets differ from the E14.7a classifications.")
    if any(item["fallbackAuthorized"] for item in remediation_plan["retiredFamilies"]):
        raise DatasetValidationError("E14.7b retired families cannot authorize fallback selection.")

    sources = remediation_plan["replacementSources"]
    source_by_id = {item["sourceId"]: item for item in sources}
    if len(source_by_id) != len(sources) or len({item["url"] for item in sources}) != len(sources):
        raise DatasetValidationError("E14.7b replacement sources must have unique IDs and URLs.")
    blocked_source_ids = {
        item["sourceId"] for item in feasibility_audit["sourceAssessments"]
        if item["status"] == "blocked"
    }
    if blocked_source_ids.intersection(source_by_id):
        raise DatasetValidationError("E14.7b reuses a source blocked by E14.7a.")

    prior_family_by_id = {item["familyId"]: item for item in feasibility_audit["familyAssessments"]}
    episode_scope = {
        item["mechanism"]: {episode["episodeId"] for episode in item["episodeSignatures"]}
        for item in hypothesis_plan["mechanisms"]
    }
    episode_dates = _positive_episode_dates(taxonomy)
    replacements = remediation_plan["replacementFamilies"]
    replacement_ids = [item["replacementFamilyId"] for item in replacements]
    replaced_ids = [item["replacesFamilyId"] for item in replacements]
    if len(set(replacement_ids)) != len(replacement_ids) or set(replaced_ids) != retired:
        raise DatasetValidationError("E14.7b requires exactly one independent replacement per retired family.")

    assessments = []
    for replacement in replacements:
        replaced = prior_family_by_id[replacement["replacesFamilyId"]]
        mechanism = replacement["mechanism"]
        if mechanism != replaced["mechanism"]:
            raise DatasetValidationError("E14.7b replacement mechanism differs from the retired family.")
        if replacement["minimumHistoryMonths"] != replaced["minimumHistoryMonths"]:
            raise DatasetValidationError("E14.7b minimum causal-history rules cannot be relaxed.")
        applicable = replacement["applicableEpisodeIds"]
        if not applicable or not set(applicable).issubset(episode_scope[mechanism]):
            raise DatasetValidationError("E14.7b replacement episode scope is invalid for its mechanism.")
        try:
            selected_sources = [source_by_id[source_id] for source_id in replacement["sourceIds"]]
        except KeyError as error:
            raise DatasetValidationError("E14.7b replacement references an unknown source.") from error
        coverage_from = max(date.fromisoformat(item["coverageFrom"]) for item in selected_sources)
        coverage_to_values = [
            date.fromisoformat(item["coverageTo"]) for item in selected_sources if item.get("coverageTo")
        ]
        coverage_to = min(coverage_to_values) if coverage_to_values else None
        episode_coverage = []
        for episode_id in applicable:
            episode_start = episode_dates.get((episode_id, mechanism))
            if episode_start is None:
                raise DatasetValidationError("E14.7b replacement references an unavailable positive episode.")
            months = ((episode_start.year - coverage_from.year) * 12
                      + episode_start.month - coverage_from.month)
            within_end = coverage_to is None or episode_start <= coverage_to
            satisfied = months >= replacement["minimumHistoryMonths"] and within_end
            episode_coverage.append({
                "episodeId": episode_id,
                "episodeFirstMonth": episode_start.isoformat(),
                "latestSourceCoverageFrom": coverage_from.isoformat(),
                "earliestSourceCoverageTo": coverage_to.isoformat() if coverage_to else None,
                "causalHistoryMonths": months,
                "requiredHistoryMonths": replacement["minimumHistoryMonths"],
                "episodeWithinSourceEnd": within_end,
                "minimumHistorySatisfied": satisfied,
            })
        assessments.append({
            "replacementFamilyId": replacement["replacementFamilyId"],
            "replacesFamilyId": replacement["replacesFamilyId"],
            "mechanism": mechanism,
            "sourceIds": replacement["sourceIds"],
            "applicableEpisodeCount": len(applicable),
            "episodeCoverage": episode_coverage,
            "nominalCoverageSatisfied": all(item["minimumHistorySatisfied"] for item in episode_coverage),
            "sourceReadinessEstablished": False,
            "sourceReauditRequired": True,
            "sourceAcquisitionAuthorized": False,
        })

    if not all(item["nominalCoverageSatisfied"] for item in assessments):
        raise DatasetValidationError("E14.7b replacement nominal coverage violates frozen history rules.")
    mechanism_counts = Counter(item["mechanism"] for item in replacements)
    actual_mechanism_counts = {mechanism: mechanism_counts[mechanism] for mechanism in MECHANISMS}
    expected_inventory = (
        len(preserved), len(retired), len(sources), len(replacements), actual_mechanism_counts,
    )
    frozen_inventory = (
        contract["expectedPreservedConditionalFamilyCount"],
        contract["expectedRetiredFamilyCount"], contract["expectedReplacementSourceCount"],
        contract["expectedReplacementFamilyCount"], contract["expectedReplacementMechanismCounts"],
    )
    if expected_inventory != frozen_inventory:
        raise DatasetValidationError("E14.7b inventory differs from the frozen contract.")

    output = Path(output_path).resolve()
    input_artifacts = {
        name: _artifact(file, raw) for name, (file, raw, _) in zip((
            "remediationContract", "taxonomyV5", "hypothesisPlanV1", "hypothesisAuditV1",
            "feasibilityContractV1", "feasibilityEvidenceV1", "feasibilityAuditV1",
            "remediationPlanV1", "remediationSchemaV1",
        ), artifacts)
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FeasibilityRemediationAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "inventory": {
            "preservedConditionalFamilyCount": len(preserved),
            "retiredFamilyCount": len(retired),
            "replacementSourceCount": len(sources),
            "replacementFamilyCount": len(replacements),
            "replacementMechanismCounts": actual_mechanism_counts,
        },
        "preservedConditionalFamilies": remediation_plan["preservedConditionalFamilies"],
        "retiredFamilies": remediation_plan["retiredFamilies"],
        "replacementAssessments": assessments,
        "checks": {
            "allInputHashesExact": True,
            "priorConditionalFamiliesPreservedExactly": True,
            "priorBlockedFamiliesRetiredExactly": True,
            "oneIndependentReplacementPerRetiredFamily": True,
            "blockedSourcesNotReused": True,
            "minimumHistoryRulesUnchanged": True,
            "replacementEpisodeScopesMechanismBound": True,
            "allReplacementSourcesResolve": True,
            "allReplacementNominalCoverageSatisfied": True,
            "nominalCoverageNotTreatedAsReadiness": True,
            "seriesObservationsNotDownloaded": True,
            "outerOosNotUsed": True,
        },
        "decision": {
            "remediationPreregistered": True,
            "replacementSourceReadinessEstablished": False,
            "sourceFeasibilityReauditAuthorized": True,
            "sourceAcquisitionAuthorized": False,
            "featureFoundationMaterializationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "protocol": {
            "designMetadataOnly": True,
            "seriesObservationDownloaded": False,
            "datasetRead": False,
            "featureMaterialized": False,
            "candidateGenerated": False,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "implementation": {
            "module": "regime_eval.e14_feasibility_remediation",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output, payload)


def _validate_governance(
    contract: dict[str, Any], taxonomy: dict[str, Any], hypothesis_plan: dict[str, Any],
    hypothesis_audit: dict[str, Any], feasibility_contract: dict[str, Any],
    feasibility_evidence: dict[str, Any], feasibility_audit: dict[str, Any],
    remediation_plan: dict[str, Any], remediation_schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    auth = contract.get("authorizationPolicy", {})
    plan_auth = remediation_plan.get("authorizations", {})
    governance = remediation_plan.get("governance", {})
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-feasibility-remediation-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or auth.get("feasibilityRemediationPreregistrationAuthorized") is not True
        or auth.get("sourceFeasibilityReauditAuthorized") is not True
        or any(auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or taxonomy.get("schemaVersion") != 5
        or hypothesis_plan.get("planId") != "e14-new-information-hypothesis-plan-v1"
        or hypothesis_audit.get("status") != "NEW_INFORMATION_HYPOTHESIS_PREREGISTERED_SOURCE_FEASIBILITY_REQUIRED"
        or feasibility_contract.get("contractId") != "e14-source-vintage-feasibility-contract-v1"
        or feasibility_evidence.get("networkPolicy") != "metadata-only-no-series-download"
        or feasibility_audit.get("status")
        != "SOURCE_VINTAGE_FEASIBILITY_BLOCKED_REMEDIATION_PREREGISTRATION_REQUIRED"
        or feasibility_audit.get("decision", {}).get("sourceAcquisitionAuthorized") is not False
        or remediation_plan.get("planId") != "e14-feasibility-remediation-plan-v1"
        or remediation_schema.get("$id") != "e14-feasibility-remediation-schema-v1"
        or plan_auth.get("feasibilityRemediationPreregistrationAuthorized") is not True
        or plan_auth.get("sourceFeasibilityReauditAuthorized") is not True
        or any(plan_auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or governance.get("replacementSelectionUsedSeriesObservations") is not False
        or governance.get("replacementSelectionUsedLoeoScores") is not False
        or governance.get("replacementSelectionUsedOuterOos") is not False
        or governance.get("thresholdsChanged") is not False
        or governance.get("absoluteGatesChanged") is not False
        or governance.get("minimumHistoryRulesChanged") is not False
        or governance.get("blockedSourceReuseForbidden") is not True
    )
    if invalid:
        raise DatasetValidationError("E14.7b inputs or governance are invalid.")


def _positive_episode_dates(taxonomy: dict[str, Any]) -> dict[tuple[str, str], date]:
    output = {}
    for episode in taxonomy["episodes"]:
        if episode.get("financialState") != "positive":
            continue
        for mechanism in episode["mechanisms"]:
            output[(episode["independentEventId"], mechanism)] = date.fromisoformat(episode["firstMonth"])
    return output


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    if not file.exists():
        raise DatasetValidationError(f"E14.7b {label} does not exist: {file}")
    raw = file.read_bytes()
    try:
        return file, raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7b {label} is not valid UTF-8 JSON.") from error


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write_new(path: Path, payload: dict[str, Any]) -> Path:
    if path.exists():
        raise DatasetValidationError("Immutable E14.7b feasibility-remediation audit output already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return path
