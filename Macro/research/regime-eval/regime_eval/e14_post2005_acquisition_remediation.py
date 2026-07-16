from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "POST_2005_ACQUISITION_REMEDIATION_PREREGISTERED_INDEPENDENT_REVIEW_REQUIRED"
CONTRACT_SHA256 = "99046007c358ef2b4c4d46076a1b99c18a860328c32743b565e2a106a10d8b7b"
CANONICAL_HASHES = {
    "preflightAuditV2Sha256": "63e3a440d1f4756e05c9b278d220f322cf26441933b3504c2ec91c74ef13dee0",
    "manifestV2Sha256": "cbe3e50768381c6772a8a5b70efa04fe62fb27d4f33b5623f5f7fc8caeb128dc",
    "requestCatalogV2Sha256": "cf4d1c8643d4123ff7ac3ef3bd780766cd46f4b3fbddeda858b4682ffcc36935",
    "activePolicyV2Sha256": "94db6eb64b83ea3d54ca36c8d3311f983ab48f998c4b6bb9e7218df8aad049fd",
    "remediationEvidenceV1Sha256": "e8d47f7ba704772ae3200ffdc926db6a012997f439998752a0ec7d2102ef9ea5",
    "remediationPlanV1Sha256": "e2c32ade7945700fa84c9681506df4acd2361847fad41d5f111c24e6f165aa24",
    "proposalSchemaV1Sha256": "6a3da8ba2b4ae150350e76c52b2a5422d85591f2eddcc1411dcf96e529c6f75d",
    "dossierSchemaV1Sha256": "1b26c69e6511cd9a67a13947722b60b9e8a55d85c78dc026666536d4339fa504",
    "queueSchemaV1Sha256": "d366a8c2524cc2d3abcc228ff1f817a2ab88f75991ddadf5de0c377d9baa1103",
    "reviewReceiptSchemaV1Sha256": "5a1ad516a327c01fd49fed691d5ab8c191238ef0cb18ba9f4c32d40e0fbed07b",
    "auditSchemaV1Sha256": "473b44d3f23b79e0bc9fd8f8c7f6b725f0a039991e60b7024cb55ca714e0c69f",
}


def write_e14_post2005_acquisition_remediation(
    contract_path: str | Path, preflight_path: str | Path, manifest_path: str | Path,
    catalog_path: str | Path, active_policy_path: str | Path, evidence_path: str | Path,
    plan_path: str | Path, proposal_schema_path: str | Path, dossier_schema_path: str | Path,
    queue_schema_path: str | Path, review_schema_path: str | Path, audit_schema_path: str | Path,
    proposal_output: str | Path, dossier_output: str | Path, queue_output: str | Path,
    audit_output: str | Path,
) -> tuple[Path, Path, Path, Path]:
    labels = ("contract", "preflight audit", "manifest v2", "request catalog v2", "active policy v2", "remediation evidence", "remediation plan", "proposal schema", "dossier schema", "queue schema", "review schema", "audit schema")
    paths = (contract_path, preflight_path, manifest_path, catalog_path, active_policy_path, evidence_path, plan_path, proposal_schema_path, dossier_schema_path, queue_schema_path, review_schema_path, audit_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, preflight, manifest, catalog, policy, evidence, plan, proposal_schema, dossier_schema, queue_schema, review_schema, audit_schema = (item[2] for item in artifacts)
    if _sha(artifacts[0][1]) != CONTRACT_SHA256:
        raise DatasetValidationError("E14.7w remediation contract hash is not canonical.")
    hashes = {name: _sha(artifacts[index][1]) for index, name in enumerate(CANONICAL_HASHES, start=1)}
    _validate_inputs(contract, preflight, manifest, catalog, policy, evidence, plan, proposal_schema, dossier_schema, queue_schema, review_schema, audit_schema, hashes)

    outputs = tuple(Path(path).resolve() for path in (proposal_output, dossier_output, queue_output, audit_output))
    if tuple(path.name for path in outputs) != tuple(contract["expectedOutputs"]) or len(set(outputs)) != 4 or any(path.exists() for path in outputs) or len({path.parent for path in outputs}) != 1:
        raise DatasetValidationError("E14.7w output names, topology, uniqueness, or immutability are invalid.")
    snapshot = (Path(__file__).resolve().parents[3] / manifest["snapshotRoot"]).resolve()
    if snapshot.exists() or any(path.is_relative_to(snapshot) for path in outputs):
        raise DatasetValidationError("E14.7w protected snapshot must remain absent and cannot contain outputs.")
    forbidden_catalog_name = "e14-post2005-source-acquisition-requests-v3.json"
    forbidden_catalog_paths = {outputs[0].parent / forbidden_catalog_name, artifacts[1][0].parent / forbidden_catalog_name}
    if any(path.exists() for path in forbidden_catalog_paths):
        raise DatasetValidationError("E14.7w request catalog v3 already exists; review-first docket cannot claim catalog absence.")

    authorization = {"independentReviewAuthorized": True, "requestCatalogV3MaterializationAuthorized": False, "networkRequestsAuthorized": False, "sourceAcquisitionAuthorized": False, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False}
    proposal = {
        "schemaVersion": 1, "artifactType": "E14Post2005AcquisitionRemediationProposal", "proposalId": "e14-post2005-acquisition-remediation-proposal-v1", "status": STATUS,
        "supersedesPreflight": _artifact(artifacts[1][0], artifacts[1][1]), "evidence": _artifact(artifacts[5][0], artifacts[5][1]),
        "catalogRemediation": plan["remediationItems"], "openRequirements": [evidence["openEvidenceRequirement"]], "authorizationPolicy": authorization,
    }
    pairs = []
    for pair in evidence["providerPrimaryEvidence"]["g5DuplicateReleasePairs"]:
        pairs.append({"month": pair["month"], "original": {**pair["earlier"], "role": "ORIGINAL", "effectiveFrom": pair["earlier"]["releaseDate"]}, "correction": {**pair["later"], "role": "CORRECTION", "effectiveFrom": pair["later"]["releaseDate"]}, "bothRawPayloadsMustBeRetained": True, "payloadDifferenceConfirmed": pair["earlier"]["broad"] != pair["later"]["broad"] or pair["earlier"]["afe"] != pair["later"]["afe"] or pair["earlier"]["eme"] != pair["later"]["eme"], "noRetroactiveApplication": True})
    dossier = {
        "schemaVersion": 1, "artifactType": "E14G5DuplicateReleaseAdjudicationDossier", "dossierId": "e14-g5-duplicate-release-adjudication-dossier-v1", "status": "G5_DUPLICATE_RELEASE_ADJUDICATION_PENDING_INDEPENDENT_REVIEW", "proposalId": proposal["proposalId"], "sourceId": "federal-reserve-g5-release-archive", "pairs": pairs,
        "proposedRule": "preserve-both-raw-original-effective-until-correction-date-correction-effective-from-provider-date",
        "reviewRequirements": {"allFourProviderUrlsMustBeOpened": True, "payloadDifferencesMustBeConfirmed": True, "bothRawVersionsMustBeRetained": True, "noRetroactiveApplicationMustBeAccepted": True, "reviewerMustBeIndependent": True},
        "authorizationPolicy": {**authorization, "independentReviewAuthorized": True},
    }
    proposal_raw, dossier_raw = _json_bytes(proposal), _json_bytes(dossier)
    queue = {
        "schemaVersion": 1, "artifactType": "E14Post2005AcquisitionRemediationReviewQueue", "queueId": "e14-post2005-acquisition-remediation-review-queue-v1", "status": "ACQUISITION_REMEDIATION_INDEPENDENT_REVIEW_PENDING",
        "proposal": _artifact(outputs[0], proposal_raw), "dossier": _artifact(outputs[1], dossier_raw), "reviewReceiptSchema": _artifact(artifacts[10][0], artifacts[10][1]),
        "items": [
            {"reviewItemId": "h8-count-revision-1043-to-1042", "decisionRequired": True},
            {"reviewItemId": "fdic-roster-79-and-publication-proof-gap", "decisionRequired": True},
            {"reviewItemId": "g5-duplicate-correction-chains", "decisionRequired": True},
        ],
        "authorizationPolicy": authorization,
    }
    queue_raw = _json_bytes(queue)
    audit = {
        "schemaVersion": 1, "artifactType": "E14Post2005AcquisitionRemediationAudit", "status": STATUS,
        "inputs": {name: _artifact(path, raw) for name, (path, raw, _) in zip(("remediationContract", "preflightAuditV2", "manifestV2", "requestCatalogV2", "activePolicyV2", "remediationEvidenceV1", "remediationPlanV1", "proposalSchemaV1", "dossierSchemaV1", "queueSchemaV1", "reviewReceiptSchemaV1", "auditSchemaV1"), artifacts)},
        "outputs": {"proposal": _artifact(outputs[0], proposal_raw), "g5AdjudicationDossier": _artifact(outputs[1], dossier_raw), "reviewQueue": _artifact(outputs[2], queue_raw)},
        "inventory": {"remediationItemCount": 4, "reviewItemCount": 3, "g5DuplicateMonthCount": 2, "g5ReleaseRecordCount": 4, "h8ProviderCalendarCount": 1042, "fdicEligibleQuarterCount": 79, "fdicResolvedPublicationProofCount": 0},
        "checks": {"allInputHashesExact": True, "preflightRemainsBlocked": True, "h8CountRevisionExplicit": True, "fdicRosterCompleteButPublicationProofOpen": True, "g5BothOriginalsAndCorrectionsRetained": True, "g5NoRetroactiveApplication": True, "schemasApplied": True, "catalogV3Absent": True},
        "protocol": {"networkRequestsMade": 0, "rawArtifactsWritten": 0, "requestCatalogsMaterialized": 0, "observationsAcquired": 0, "featuresTransformed": 0, "candidatesGenerated": 0, "evaluationPerformed": False, "outerOosRead": False},
        "decision": {"independentReviewAuthorized": True, "requestCatalogV3MaterializationAuthorized": False, "sourceAcquisitionAuthorized": False, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": contract["nextAllowedAction"]},
        "implementation": {"module": "regime_eval.e14_post2005_acquisition_remediation", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    _validate_outputs(proposal, dossier, queue, audit, proposal_schema, dossier_schema, queue_schema, audit_schema)
    raws = (proposal_raw, dossier_raw, queue_raw, _json_bytes(audit))
    _write_many(tuple(zip(outputs, raws)))
    return outputs


def _validate_inputs(contract: dict[str, Any], preflight: dict[str, Any], manifest: dict[str, Any], catalog: dict[str, Any], policy: dict[str, Any], evidence: dict[str, Any], plan: dict[str, Any], proposal_schema: dict[str, Any], dossier_schema: dict[str, Any], queue_schema: dict[str, Any], review_schema: dict[str, Any], audit_schema: dict[str, Any], hashes: dict[str, str]) -> None:
    blockers = {item.get("code"): item for item in preflight.get("blockers", [])}
    h8 = evidence.get("providerPrimaryEvidence", {}).get("h8ReleaseCalendar", {})
    fdic = evidence.get("providerPrimaryEvidence", {}).get("fdicPastQbpArchive", {})
    pairs = evidence.get("providerPrimaryEvidence", {}).get("g5DuplicateReleasePairs", [])
    expected_policy = {"preflightMustRemainBlocked": True, "h8CountRevisionRequiresIndependentReview": True, "fdic79QuarterRosterMayBeProposed": True, "fdic79PublicationProofLedgerMustRemainOpen": True, "g5OriginalAndCorrectionMustBothBeRetained": True, "g5CorrectionCannotApplyRetroactively": True, "catalogV3MaterializationForbidden": True, "sourceAcquisitionForbidden": True}
    if (
        contract.get("contractId") != "e14-post2005-acquisition-remediation-contract-v1" or contract.get("inputHashes") != hashes or hashes != CANONICAL_HASHES or contract.get("decisionPolicy") != expected_policy
        or preflight.get("status") != "POST_2005_SOURCE_V2_ACQUISITION_BLOCKED_DISCOVERY_CATALOG_REMEDIATION_REQUIRED" or preflight.get("decision", {}).get("fullAtomicAcquisitionAuthorized") is not False
        or set(blockers) != {"H8_DIRECT_DATED_RELEASE_VALUES_INCOMPLETE", "FDIC_ELIGIBLE_DOCUMENT_ROSTER_INCOMPLETE", "FDIC_ACTUAL_PUBLICATION_PROOFS_INCOMPLETE", "G5_DUPLICATE_MONTHS_REQUIRE_ADJUDICATION"}
        or manifest.get("manifestId") != "e14-post2005-source-acquisition-manifest-v2" or catalog.get("requestCatalogId") != "e14-post2005-source-acquisition-requests-v2"
        or policy.get("policyId") != "e14-post2005-active-source-vintage-policy-v2"
        or evidence.get("evidenceId") != "e14-post2005-acquisition-remediation-evidence-v1" or h8.get("windowReleaseCount") != 1042 or h8.get("supersedesDerivedPreflightRequirement") != 1043
        or fdic.get("eligibleQuarterCount") != 79 or fdic.get("actualPublicationDateProofCount") != 0 or fdic.get("missingEligibleQuarters") != []
        or evidence.get("openEvidenceRequirement", {}).get("requiredRowCount") != 79 or evidence.get("openEvidenceRequirement", {}).get("satisfied") is not False
        or [item.get("month") for item in pairs] != ["2024-08", "2024-10"] or [(item["earlier"]["releaseDate"], item["later"]["releaseDate"]) for item in pairs] != [("20240801", "20240807"), ("20241001", "20241003")]
        or any(item["earlier"]["broad"] == item["later"]["broad"] and item["earlier"]["afe"] == item["later"]["afe"] and item["earlier"]["eme"] == item["later"]["eme"] for item in pairs)
        or plan.get("planId") != "e14-post2005-acquisition-remediation-plan-v1" or plan.get("outputPolicy", {}).get("requestCatalogV3MayBeMaterialized") is not False or plan.get("outputPolicy", {}).get("sourceAcquisitionAuthorized") is not False
        or proposal_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-acquisition-remediation-proposal-v1.json" or dossier_schema.get("$id") != "https://macro-regime.local/schemas/e14-g5-duplicate-adjudication-dossier-v1.json" or queue_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-acquisition-remediation-review-queue-v1.json" or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-acquisition-remediation-independent-review-v1.json" or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-acquisition-remediation-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7w acquisition remediation inputs are invalid.")


def _validate_outputs(proposal: dict[str, Any], dossier: dict[str, Any], queue: dict[str, Any], audit: dict[str, Any], proposal_schema: dict[str, Any], dossier_schema: dict[str, Any], queue_schema: dict[str, Any], audit_schema: dict[str, Any]) -> None:
    for value, schema in ((proposal, proposal_schema), (dossier, dossier_schema), (queue, queue_schema), (audit, audit_schema)):
        _validate_schema_value(value, schema, schema, "$")
    if dossier["pairs"][0]["correction"]["effectiveFrom"] != "20240807" or dossier["pairs"][1]["correction"]["effectiveFrom"] != "20241003" or any(not item["bothRawPayloadsMustBeRetained"] or not item["noRetroactiveApplication"] or not item["payloadDifferenceConfirmed"] for item in dossier["pairs"]) or audit["protocol"]["networkRequestsMade"] != 0 or audit["decision"]["requestCatalogV3MaterializationAuthorized"]:
        raise DatasetValidationError("E14.7w output invariants are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7w {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write_many(items: tuple[tuple[Path, bytes], ...]) -> None:
    temporary: list[Path] = []
    published: list[Path] = []
    try:
        for path, raw in items:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_name("." + path.name + ".staging")
            if temp.exists():
                raise DatasetValidationError("E14.7w stale staging output exists.")
            with temp.open("xb") as stream:
                stream.write(raw)
            temporary.append(temp)
        for (path, _), temp in zip(items, temporary):
            temp.rename(path)
            published.append(path)
    except Exception:
        for path in temporary:
            if path.exists():
                path.unlink()
        for path in published:
            if path.exists():
                path.unlink()
        raise
