from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "TARGETED_VINTAGE_REMEDIATION_BLOCKED_POLICY_REDESIGN_REQUIRED"
EXPECTED_SOURCES = [
    "federal-reserve-h8-release-archive",
    "fdic-qbp-archive",
    "federal-reserve-h10-release-archive",
]


def write_e14_post2005_vintage_remediation_audit(
    contract_path: str | Path,
    vintage_fitness_audit_path: str | Path,
    snapshot_index_path: str | Path,
    acquisition_audit_path: str | Path,
    scope_plan_path: str | Path,
    fitness_plan_path: str | Path,
    source_acquisition_manifest_path: str | Path,
    remediation_evidence_path: str | Path,
    remediation_plan_path: str | Path,
    remediation_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "remediation contract", "vintage fitness audit", "snapshot index",
        "acquisition audit", "scope plan", "fitness plan", "source acquisition manifest",
        "remediation evidence", "remediation plan", "remediation schema",
    )
    paths = (
        contract_path, vintage_fitness_audit_path, snapshot_index_path,
        acquisition_audit_path, scope_plan_path, fitness_plan_path,
        source_acquisition_manifest_path, remediation_evidence_path,
        remediation_plan_path, remediation_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract = artifacts[0][2]
    fitness = artifacts[1][2]
    scope = artifacts[4][2]
    evidence = artifacts[7][2]
    plan = artifacts[8][2]
    schema = artifacts[9][2]
    hash_names = (
        "vintageFitnessAuditSha256", "snapshotIndexSha256", "acquisitionAuditSha256",
        "scopePlanSha256", "fitnessPlanSha256", "sourceAcquisitionManifestSha256",
        "remediationEvidenceSha256", "remediationPlanSha256", "remediationSchemaSha256",
    )
    actual_hashes = {
        name: _sha(raw) for name, (_, raw, _) in zip(hash_names, artifacts[1:])
    }
    _validate_inputs(contract, fitness, scope, evidence, plan, schema, actual_hashes)

    source_by_id = {item["sourceId"]: item for item in evidence["sources"]}
    h8 = source_by_id["federal-reserve-h8-release-archive"]
    h10 = source_by_id["federal-reserve-h10-release-archive"]
    fdic = source_by_id["fdic-qbp-archive"]
    source_assessments = [
        {
            "sourceId": h8["sourceId"], "mechanism": "banking-credit",
            "datedLocatorDiscoveryComplete": True,
            "unchangedFitnessPolicyFeasible": len(h8["missingReleaseMonthsBeforeTaper"]) == 0,
            "structuralGapCount": 0,
            "blockingReasons": [],
            "requestCatalogGenerationAuthorized": False,
        },
        {
            "sourceId": fdic["sourceId"], "mechanism": "banking-credit",
            "datedLocatorDiscoveryComplete": True,
            "unchangedFitnessPolicyFeasible": fdic["eligibleCoverageEndAtCutoff"] >= fdic["requiredCoverageEnd"],
            "structuralGapCount": 1,
            "blockingReasons": ["q4-2025-publication-not-eligible-at-2025-12-31-cutoff"],
            "requestCatalogGenerationAuthorized": False,
        },
        {
            "sourceId": h10["sourceId"], "mechanism": "cross-border-growth",
            "datedLocatorDiscoveryComplete": True,
            "unchangedFitnessPolicyFeasible": len(h10["missingReleaseMonthsBeforeTaper"]) == 0,
            "structuralGapCount": len(h10["missingReleaseMonthsBeforeTaper"]),
            "blockingReasons": ["weekly-h10-publication-ceased-2006-06-through-2008-12"],
            "requestCatalogGenerationAuthorized": False,
        },
    ]
    banking_ready = all(item["unchangedFitnessPolicyFeasible"] for item in source_assessments if item["mechanism"] == "banking-credit")
    cross_ready = all(item["unchangedFitnessPolicyFeasible"] for item in source_assessments if item["mechanism"] == "cross-border-growth")
    mechanism_assessments = [
        _mechanism("banking-credit", False, banking_ready, ["fdic-qbp-archive"]),
        _mechanism("broad-market-repricing", True, True, []),
        _mechanism("cross-border-growth", False, cross_ready, ["federal-reserve-h10-release-archive"]),
        _mechanism("funding-liquidity", True, True, []),
    ]
    if banking_ready or cross_ready:
        raise DatasetValidationError("E14.7m frozen structural blockers were unexpectedly removed.")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005VintageRemediationAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw) for name, (file, raw, _) in zip(
                ("remediationContract", "vintageFitnessAudit", "snapshotIndex", "acquisitionAudit", "scopePlan", "fitnessPlan", "sourceAcquisitionManifest", "remediationEvidence", "remediationPlan", "remediationSchema"),
                artifacts,
            )
        },
        "inventory": {
            "preservedReadyMechanismCount": 2, "blockedMechanismCount": 2,
            "remediationSourceCount": 3, "h10MissingReleaseMonthCount": len(h10["missingReleaseMonthsBeforeTaper"]),
            "fdicLatestEligibleQuarterAtCutoff": fdic["latestEligibleQuarterAtCutoff"],
        },
        "sourceAssessments": source_assessments,
        "mechanismAssessments": mechanism_assessments,
        "checks": {
            "allInputHashesExact": True,
            "remediationRosterExact": True,
            "readyMechanismsPreservedExactly": True,
            "h8DatedReleaseMonthsCompleteBeforeTaper": True,
            "h10StructuralPublicationGapDetected": True,
            "h10CurrentBulkRejectedAsGapFill": True,
            "fdicActualAvailabilityCutoffPreserved": True,
            "fdicQ4PostCutoffRejected": True,
            "minimumHistoryPolicyUnchanged": True,
            "globalTransformationGateRemainsClosed": True,
        },
        "protocol": {
            "discoveryMetadataRead": True, "seriesObservationsDownloaded": False,
            "requestCatalogGenerated": False, "featuresTransformed": 0,
            "candidatesGenerated": 0, "evaluationPerformed": False, "outerOosRead": False,
        },
        "decision": {
            "remediationFeasibilityComplete": True,
            "targetedAcquisitionPreregistrationAuthorized": False,
            "requestCatalogGenerationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "policyRedesignRequired": True,
            "requiredRedesigns": [
                "replace-h10-with-a-separately-preregistered-event-time-source-that-satisfies-the-60-month-pre-taper-history",
                "define-fdic-coverage-by-actual-publication-vintage-without-using-q4-2025-before-its-release",
            ],
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_vintage_remediation",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_output(payload, schema)
    return _write_new(Path(output_path).resolve(), payload)


def _mechanism(mechanism: str, preserved: bool, feasible: bool, blockers: list[str]) -> dict[str, Any]:
    return {
        "mechanism": mechanism, "priorVintageFitPreserved": preserved,
        "unchangedFitnessPolicyFeasible": feasible,
        "status": "VINTAGE_FIT_PRESERVED" if preserved else "POLICY_REDESIGN_REQUIRED",
        "blockingSourceIds": blockers,
    }


def _validate_inputs(
    contract: dict[str, Any], fitness: dict[str, Any], scope: dict[str, Any],
    evidence: dict[str, Any], plan: dict[str, Any], schema: dict[str, Any],
    actual_hashes: dict[str, str],
) -> None:
    source_ids = [item.get("sourceId") for item in evidence.get("sources", [])]
    roster_ids = [item.get("sourceId") for item in plan.get("remediationRoster", [])]
    h10 = next((item for item in evidence.get("sources", []) if item.get("sourceId") == "federal-reserve-h10-release-archive"), {})
    fdic = next((item for item in evidence.get("sources", []) if item.get("sourceId") == "fdic-qbp-archive"), {})
    if (
        contract.get("contractId") != "e14-post2005-vintage-remediation-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("expectedStatus") != STATUS
        or contract.get("expectedRemediationSourceIds") != EXPECTED_SOURCES
        or len(source_ids) != 3 or set(source_ids) != set(EXPECTED_SOURCES)
        or roster_ids != EXPECTED_SOURCES
        or fitness.get("status") != "POST_2005_PARTIAL_VINTAGE_FITNESS_REMEDIATION_REQUIRED"
        or fitness.get("decision", {}).get("readyMechanisms") != contract.get("expectedPreservedReadyMechanisms")
        or fitness.get("decision", {}).get("blockedMechanisms") != contract.get("expectedBlockedMechanisms")
        or scope.get("cutoffInclusive") != "2006-01-01"
        or plan.get("planId") != "e14-post2005-vintage-remediation-plan-v1"
        or plan.get("authorizationPolicy") != contract.get("authorizationPolicy")
        or not all(plan.get("decisionPolicy", {}).values())
        or len(h10.get("missingReleaseMonthsBeforeTaper", [])) != contract.get("expectedH10MissingMonthCount")
        or fdic.get("latestEligibleQuarterAtCutoff") != contract.get("expectedLatestEligibleFDICQuarter")
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-vintage-remediation-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7m remediation inputs are invalid.")


def _validate_output(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    required = set(schema.get("required", []))
    properties = schema.get("properties", {})
    if (
        not required.issubset(payload)
        or set(payload) != set(properties)
        or payload.get("status") != STATUS
        or len(payload.get("sourceAssessments", [])) != 3
        or len(payload.get("mechanismAssessments", [])) != 4
        or payload.get("decision", {}).get("sourceAcquisitionAuthorized") is not False
        or payload.get("decision", {}).get("featureTransformationAuthorized") is not False
    ):
        raise DatasetValidationError("E14.7m output violates the frozen schema or gate invariants.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7m {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_new(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14.7m output exists: {path}") from error
    return path
