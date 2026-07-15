from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "REPLACEMENT_SOURCE_FEASIBILITY_BLOCKED_VINTAGE_POLICY_DECISION_REQUIRED"
REQUIRED_READY_FIELDS = [
    "providerPrimaryPageReachable",
    "coverageVerified",
    "licensingCleared",
    "componentCoverageVerified",
    "releaseProofComplete",
    "vintageProofComplete",
    "methodologyManifestComplete",
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


def write_e14_replacement_source_feasibility_audit(
    contract_path: str | Path,
    hypothesis_plan_path: str | Path,
    prior_feasibility_audit_path: str | Path,
    remediation_contract_path: str | Path,
    remediation_plan_path: str | Path,
    remediation_audit_path: str | Path,
    evidence_path: str | Path,
    evidence_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "replacement feasibility contract", "hypothesis plan", "prior feasibility audit",
        "remediation contract", "remediation plan", "remediation audit",
        "replacement feasibility evidence", "replacement feasibility evidence schema",
    )
    paths = (
        contract_path, hypothesis_plan_path, prior_feasibility_audit_path,
        remediation_contract_path, remediation_plan_path, remediation_audit_path,
        evidence_path, evidence_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract),
     (hypothesis_plan_file, hypothesis_plan_raw, hypothesis_plan),
     (prior_audit_file, prior_audit_raw, prior_audit),
     (remediation_contract_file, remediation_contract_raw, remediation_contract),
     (remediation_plan_file, remediation_plan_raw, remediation_plan),
     (remediation_audit_file, remediation_audit_raw, remediation_audit),
     (evidence_file, evidence_raw, evidence),
     (evidence_schema_file, evidence_schema_raw, evidence_schema)) = artifacts
    hashes = {
        "hypothesisPlanV1Sha256": _sha(hypothesis_plan_raw),
        "priorFeasibilityAuditV1Sha256": _sha(prior_audit_raw),
        "remediationContractV1Sha256": _sha(remediation_contract_raw),
        "remediationPlanV1Sha256": _sha(remediation_plan_raw),
        "remediationAuditV1Sha256": _sha(remediation_audit_raw),
        "reauditEvidenceV1Sha256": _sha(evidence_raw),
        "reauditEvidenceSchemaV1Sha256": _sha(evidence_schema_raw),
    }
    _validate_governance(
        contract, hypothesis_plan, prior_audit, remediation_contract,
        remediation_plan, remediation_audit, evidence, evidence_schema, hashes,
    )

    expected_preserved_sources = _preserved_source_ids(hypothesis_plan, remediation_plan)
    expected_replacement_sources = {
        item["sourceId"] for item in remediation_plan["replacementSources"]
    }
    expected_sources = expected_preserved_sources | expected_replacement_sources
    evidence_sources = evidence["sources"]
    if len(evidence_sources) != len(expected_sources):
        raise DatasetValidationError("E14.7c evidence source count differs from the remediation roster.")
    evidence_by_id = {item["sourceId"]: item for item in evidence_sources}
    if len(evidence_by_id) != len(evidence_sources) or set(evidence_by_id) != expected_sources:
        raise DatasetValidationError("E14.7c evidence source roster differs from the remediation roster.")
    for source_id, item in evidence_by_id.items():
        expected_lineage = (
            "preserved-conditional" if source_id in expected_preserved_sources else "replacement"
        )
        if item["lineage"] != expected_lineage or not item["evidenceUrls"] or not item["evidenceNotes"]:
            raise DatasetValidationError("E14.7c source lineage or evidence is invalid.")

    source_assessments = []
    for item in evidence_sources:
        failed_fields = [field for field in REQUIRED_READY_FIELDS if item[field] is not True]
        status = "ready" if not failed_fields and not item["blockingReasons"] else "blocked"
        if status == "blocked" and not item["blockingReasons"]:
            raise DatasetValidationError("E14.7c blocked source requires explicit blocking reasons.")
        if status == "ready" and item["blockingReasons"]:
            raise DatasetValidationError("E14.7c ready source cannot retain blocking reasons.")
        source_assessments.append({
            "sourceId": item["sourceId"],
            "lineage": item["lineage"],
            "status": status,
            "failedReadinessFields": failed_fields,
            "blockingReasons": item["blockingReasons"],
            "evidenceUrls": item["evidenceUrls"],
            "sourceAcquisitionAuthorized": False,
        })

    source_status = {item["sourceId"]: item["status"] for item in source_assessments}
    family_assessments = []
    for item in remediation_plan["preservedConditionalFamilies"]:
        source_ids = _hypothesis_family(hypothesis_plan, item["familyId"])["sourceIds"]
        family_assessments.append(_assess_family(
            item["familyId"], item["mechanism"], "preserved-conditional",
            source_ids, source_status,
        ))
    for item in remediation_plan["replacementFamilies"]:
        family_assessments.append(_assess_family(
            item["replacementFamilyId"], item["mechanism"], "replacement",
            item["sourceIds"], source_status,
        ))

    source_counts = Counter(item["status"] for item in source_assessments)
    family_counts = Counter(item["status"] for item in family_assessments)
    source_counts = {status: source_counts[status] for status in ("ready", "blocked")}
    family_counts = {status: family_counts[status] for status in ("ready", "blocked")}
    ready_source_ids = sorted(item["sourceId"] for item in source_assessments if item["status"] == "ready")
    blocked_family_ids = sorted(item["familyId"] for item in family_assessments if item["status"] == "blocked")
    if (
        source_counts != contract["expectedSourceStatusCounts"]
        or family_counts != contract["expectedFamilyStatusCounts"]
        or ready_source_ids != sorted(contract["expectedReadySourceIds"])
        or blocked_family_ids != sorted(contract["expectedBlockedFamilyIds"])
    ):
        raise DatasetValidationError("E14.7c classifications differ from the frozen contract.")

    output = Path(output_path).resolve()
    input_artifacts = {
        name: _artifact(file, raw) for name, (file, raw, _) in zip((
            "replacementFeasibilityContract", "hypothesisPlanV1", "priorFeasibilityAuditV1",
            "remediationContractV1", "remediationPlanV1", "remediationAuditV1",
            "replacementFeasibilityEvidenceV1", "replacementFeasibilityEvidenceSchemaV1",
        ), artifacts)
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14ReplacementSourceFeasibilityAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "inventory": {
            "sourceCount": len(source_assessments),
            "familyCount": len(family_assessments),
            "sourceStatusCounts": source_counts,
            "familyStatusCounts": family_counts,
        },
        "sourceAssessments": source_assessments,
        "familyAssessments": family_assessments,
        "checks": {
            "allInputHashesExact": True,
            "sourceRosterMatchesRemediation": True,
            "preservedAndReplacementLineageSeparated": True,
            "providerPrimaryEvidencePresent": True,
            "longCoverageNotSubstitutedForVintageProof": True,
            "allReadinessDimensionsEnforced": True,
            "priorReadyReferenceLegReusedWithSameSemantics": True,
            "allBlockedSourcesHaveExplicitReasons": True,
            "everyFamilyAssessedExactlyOnce": True,
            "seriesObservationsNotDownloaded": True,
            "datasetNotRead": True,
            "outerOosNotUsed": True,
        },
        "decision": {
            "fullSourceReadiness": family_counts["ready"] == len(family_assessments),
            "sourceAcquisitionAuthorized": False,
            "vintagePolicyDecisionPreregistrationAuthorized": True,
            "featureFoundationMaterializationAuthorized": False,
            "taxonomyMutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "candidateFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "candidateRankingAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "protocol": {
            "providerMetadataInspected": True,
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
            "module": "regime_eval.e14_replacement_source_feasibility",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output, payload)


def _assess_family(
    family_id: str, mechanism: str, lineage: str,
    source_ids: list[str], source_status: dict[str, str],
) -> dict[str, Any]:
    blocked_sources = sorted(source_id for source_id in source_ids if source_status[source_id] != "ready")
    return {
        "familyId": family_id,
        "mechanism": mechanism,
        "lineage": lineage,
        "sourceIds": source_ids,
        "status": "blocked" if blocked_sources else "ready",
        "blockedSourceIds": blocked_sources,
        "sourceAcquisitionAuthorized": False,
    }


def _preserved_source_ids(
    hypothesis_plan: dict[str, Any], remediation_plan: dict[str, Any],
) -> set[str]:
    output = set()
    for item in remediation_plan["preservedConditionalFamilies"]:
        output.update(_hypothesis_family(hypothesis_plan, item["familyId"])["sourceIds"])
    return output


def _hypothesis_family(plan: dict[str, Any], family_id: str) -> dict[str, Any]:
    matches = [
        family for mechanism in plan["mechanisms"] for family in mechanism["featureFamilies"]
        if family["familyId"] == family_id
    ]
    if len(matches) != 1:
        raise DatasetValidationError("E14.7c preserved family does not resolve exactly once.")
    return matches[0]


def _validate_governance(
    contract: dict[str, Any], hypothesis_plan: dict[str, Any], prior_audit: dict[str, Any],
    remediation_contract: dict[str, Any], remediation_plan: dict[str, Any],
    remediation_audit: dict[str, Any], evidence: dict[str, Any],
    evidence_schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    auth = contract.get("authorizationPolicy", {})
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-replacement-source-feasibility-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or auth.get("replacementSourceFeasibilityReauditAuthorized") is not True
        or auth.get("vintagePolicyDecisionPreregistrationAuthorizedOnFailure") is not True
        or any(auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or hypothesis_plan.get("planId") != "e14-new-information-hypothesis-plan-v1"
        or prior_audit.get("status")
        != "SOURCE_VINTAGE_FEASIBILITY_BLOCKED_REMEDIATION_PREREGISTRATION_REQUIRED"
        or remediation_contract.get("contractId") != "e14-feasibility-remediation-contract-v1"
        or remediation_contract.get("authorizationPolicy", {}).get("sourceAcquisitionAuthorized") is not False
        or remediation_plan.get("planId") != "e14-feasibility-remediation-plan-v1"
        or remediation_plan.get("authorizations", {}).get("sourceAcquisitionAuthorized") is not False
        or remediation_audit.get("status") != "FEASIBILITY_REMEDIATION_PREREGISTERED_REAUDIT_REQUIRED"
        or remediation_audit.get("decision", {}).get("sourceFeasibilityReauditAuthorized") is not True
        or remediation_audit.get("decision", {}).get("sourceAcquisitionAuthorized") is not False
        or evidence.get("evidencePackId") != "e14-replacement-source-feasibility-evidence-v1"
        or evidence.get("networkPolicy")
        != "provider-metadata-only-no-series-observation-download"
        or evidence_schema.get("$id")
        != "e14-replacement-source-feasibility-evidence-schema-v1"
    )
    if invalid:
        raise DatasetValidationError("E14.7c inputs or governance are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    if not file.exists():
        raise DatasetValidationError(f"E14.7c {label} does not exist: {file}")
    raw = file.read_bytes()
    try:
        return file, raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7c {label} is not valid UTF-8 JSON.") from error


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write_new(path: Path, payload: dict[str, Any]) -> Path:
    if path.exists():
        raise DatasetValidationError("Immutable E14.7c replacement-feasibility audit output already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return path
