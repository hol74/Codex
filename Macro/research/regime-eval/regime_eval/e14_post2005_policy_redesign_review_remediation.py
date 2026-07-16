from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .dataset import DatasetValidationError


STATUS = "POST_2005_POLICY_REDESIGN_REVIEW_CONTRACT_REMEDIATED_AWAITING_HANDOFF"
DOSSIER_IDS = [
    "e14-post2005-policy-redesign-dossier-cross-g5-monthly-release-replacement-v1",
    "e14-post2005-policy-redesign-dossier-bank-fdic-publication-vintage-policy-v1",
]
FINDING_IDS = {
    DOSSIER_IDS[0]: ["g5-monthly-coverage", "g5-legacy-components", "g5-methodology-boundary", "g5-no-backcast-event-time"],
    DOSSIER_IDS[1]: ["fdic-actual-publication-required", "fdic-q3-eligible", "fdic-q4-ineligible", "fdic-forward-fill-stale-age"],
}
COUNTER_IDS = {
    DOSSIER_IDS[0]: ["g5-backcast-not-event-time"],
    DOSSIER_IDS[1]: ["fdic-quarter-end-not-publication-proof"],
}
REQUIRED_LOCATORS = {
    "https://www.federalreserve.gov/releases/g5/releaseDates.json",
    "https://www.federalreserve.gov/releases/g5/20060103/",
    "https://www.federalreserve.gov/releases/g5/20130401/",
    "https://www.federalreserve.gov/econres/notes/feds-notes/revisions-to-the-federal-reserve-dollar-indexes-20190115.html",
    "https://www.fdic.gov/analysis/quarterly-banking-profile/",
    "https://www.fdic.gov/news/speeches/2025/fdic-quarterly-banking-profile-third-quarter-2025",
    "https://www.fdic.gov/news/speeches/2026/fdic-quarterly-banking-profile-fourth-quarter-2025",
}
AUTHORIZATION_POLICY = {
    "reviewRemediationMaterializationAuthorized": True,
    "independentReviewHandoffAuthorized": True,
    "reviewPerformedByRemediator": False,
    "receiptIngestionAuthorized": False,
    "policyActivationAuthorized": False,
    "requestCatalogGenerationAuthorized": False,
    "sourceAcquisitionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
NEXT_ACTION = (
    "Build an immutable handoff bundle from the byte-identical E14.7n dossiers, "
    "review queue v2, external evidence contract, and dedicated policy-redesign "
    "review schema; collect no receipt and activate no policy in this step"
)
DECLARATION = (
    "I did not author the policy-redesign proposal, dossier, evidence contract, "
    "or review materials and reviewed every cited provider-primary locator independently."
)
EXPECTED_DEDICATED_SCHEMA_SHA = "e0c6a1f4f2cf897552c4bf451849498e0785611c405890eac0fc8b7cc8c51a4a"
EXPECTED_EVIDENCE_SHA = "6de9c7eb1cc16f8bcf8e44caf59cf9654583010ca271367e1f55950bcaabb6b3"
EXPECTED_PLAN_SHA = "fb6dc44263d0e283cac14db802dff17a85ed3377d629bc3001efcbaa8e147e3c"
EXPECTED_AUDIT_SCHEMA_SHA = "813353bc7ed74172d916e29499c3d427ed77226099d76c1ad0a984fe94512954"


def write_e14_post2005_policy_redesign_review_remediation(
    contract_path: str | Path,
    proposal_path: str | Path,
    review_queue_v1_path: str | Path,
    proposal_audit_path: str | Path,
    blocked_handoff_audit_path: str | Path,
    legacy_review_schema_path: str | Path,
    dedicated_review_schema_path: str | Path,
    dossier_dir: str | Path,
    remediation_evidence_path: str | Path,
    remediation_plan_path: str | Path,
    remediation_audit_schema_path: str | Path,
    queue_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    labels = (
        "remediation contract", "policy-redesign proposal", "review queue v1",
        "proposal audit", "blocked handoff audit", "legacy review schema",
        "dedicated review schema", "remediation evidence", "remediation plan",
        "remediation audit schema",
    )
    paths = (
        contract_path, proposal_path, review_queue_v1_path, proposal_audit_path,
        blocked_handoff_audit_path, legacy_review_schema_path,
        dedicated_review_schema_path, remediation_evidence_path,
        remediation_plan_path, remediation_audit_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, proposal, queue_v1, proposal_audit, blocked_handoff, legacy_schema, dedicated_schema, evidence, plan, audit_schema = (
        item[2] for item in artifacts
    )
    dossiers = _load_dossiers(queue_v1, dossier_dir)
    dossier_by_id = {item[0]["dossierId"]: item for item in dossiers}
    hashes = {
        "proposalSha256": _sha(artifacts[1][1]),
        "reviewQueueV1Sha256": _sha(artifacts[2][1]),
        "proposalAuditSha256": _sha(artifacts[3][1]),
        "blockedHandoffAuditSha256": _sha(artifacts[4][1]),
        "crossG5DossierSha256": _sha(dossier_by_id[DOSSIER_IDS[0]][1]) if DOSSIER_IDS[0] in dossier_by_id else "",
        "bankFdicDossierSha256": _sha(dossier_by_id[DOSSIER_IDS[1]][1]) if DOSSIER_IDS[1] in dossier_by_id else "",
        "legacyReviewSchemaV2Sha256": _sha(artifacts[5][1]),
        "dedicatedReviewSchemaSha256": _sha(artifacts[6][1]),
        "remediationEvidenceSha256": _sha(artifacts[7][1]),
        "remediationPlanSha256": _sha(artifacts[8][1]),
        "remediationAuditSchemaSha256": _sha(artifacts[9][1]),
    }
    _validate_inputs(
        contract, proposal, queue_v1, proposal_audit, blocked_handoff,
        legacy_schema, dedicated_schema, evidence, plan, audit_schema,
        dossiers, hashes, artifacts,
    )

    queue_output = Path(queue_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    if queue_output.exists() or audit_output.exists():
        raise DatasetValidationError("Immutable E14.7p remediation output already exists.")

    queue = {
        "schemaVersion": 2,
        "artifactType": "E14Post2005PolicyRedesignReviewQueue",
        "queueId": "e14-post2005-policy-redesign-review-queue-v2",
        "supersedes": _artifact(artifacts[2][0], artifacts[2][1]),
        "proposal": queue_v1["proposal"],
        "proposalAuthor": queue_v1["proposalAuthor"],
        "dossiers": queue_v1["dossiers"],
        "evidenceContract": _artifact(artifacts[7][0], artifacts[7][1]),
        "reviewSchema": _artifact(artifacts[6][0], artifacts[6][1]),
        "requirements": {
            "independentReviewerRequired": True,
            "selfAcceptanceForbidden": True,
            "everyProviderPrimaryLocatorMustBeOpened": True,
            "everyRequiredFindingMustBeAssessed": True,
            "everyCounterEvidenceItemMustBeAssessed": True,
            "acceptRequiresAllFindingsSupported": True,
            "receiptMustBindQueueEvidenceContractSchemaAndDossier": True,
            "bothDossiersMustBeAcceptedBeforeSeparateActivationGate": True,
        },
        "receipts": [],
        "status": "AWAITING_INDEPENDENT_REVIEW_HANDOFF",
    }
    queue_raw = _json_bytes(queue)
    queue_sha = _sha(queue_raw)
    for dossier_id in DOSSIER_IDS:
        specimen = _completed_accept_specimen(
            dossier_id, dossier_by_id[dossier_id][2]["sha256"], queue_sha,
            hashes["remediationEvidenceSha256"], hashes["dedicatedReviewSchemaSha256"],
        )
        _validate_completed_receipt_contract(specimen, dossier_id, queue_sha, hashes)
        try:
            _validate_completed_receipt_contract(_placeholder_specimen(specimen), dossier_id, queue_sha, hashes)
        except DatasetValidationError:
            pass
        else:
            raise DatasetValidationError("E14.7p placeholder receipt unexpectedly passed the dedicated contract.")

    _write_new(queue_output, queue_raw)
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignReviewRemediationAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("remediationContract", "policyRedesignProposal", "reviewQueueV1", "proposalAudit", "blockedHandoffAudit", "legacyReviewSchemaV2", "dedicatedReviewSchema", "remediationEvidence", "remediationPlan", "remediationAuditSchema"),
                artifacts,
            )
        },
        "outputs": {"reviewQueueV2": _artifact(queue_output, queue_raw)},
        "inventory": {
            "dossierCount": 2,
            "dossierBytesChanged": 0,
            "evidenceItemCount": 7,
            "counterEvidenceItemCount": 2,
            "requiredFindingCount": 8,
            "independentReviewReceiptCount": 0,
            "bundleArtifactCount": 0,
            "receiptTemplateCount": 0,
        },
        "checks": {
            "allInputHashesExact": True,
            "e14nProposalUnchanged": True,
            "e14nDossiersPreservedByteIdentically": True,
            "queueV2SupersedesQueueV1ByHash": True,
            "dedicatedSchemaAcceptsExactE14nDossierIds": True,
            "receiptBindsQueueEvidenceContractSchemaAndDossier": True,
            "allRequiredProviderPrimaryLocatorsPresent": True,
            "allAssertionDigestsExact": True,
            "requiredFindingsAndCounterEvidenceMapped": True,
            "completedAcceptSpecimensPassDedicatedContract": True,
            "placeholderSpecimensFailDedicatedContract": True,
            "selfReviewNotPerformed": True,
        },
        "protocol": {
            "metadataOnly": True,
            "providerPrimaryPagesLocated": 7,
            "providerPagesSnapshotted": 0,
            "bundlePublished": False,
            "reviewPerformedByRemediator": False,
            "receiptsCreated": 0,
            "requestCatalogGenerated": False,
            "seriesObservationsDownloaded": False,
            "featuresTransformed": 0,
            "candidatesGenerated": 0,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "reviewContractRemediated": True,
            "independentReviewHandoffAuthorized": True,
            "reviewComplete": False,
            "receiptIngestionAuthorized": False,
            "policyActivationAuthorized": False,
            "requestCatalogGenerationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": NEXT_ACTION,
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_policy_redesign_review_remediation",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _write_new(audit_output, _json_bytes(audit))
    return queue_output, audit_output


def _validate_inputs(
    contract: dict[str, Any], proposal: dict[str, Any], queue_v1: dict[str, Any],
    proposal_audit: dict[str, Any], blocked_handoff: dict[str, Any],
    legacy_schema: dict[str, Any], dedicated_schema: dict[str, Any],
    evidence: dict[str, Any], plan: dict[str, Any], audit_schema: dict[str, Any],
    dossiers: list[tuple[dict[str, Any], bytes, dict[str, Any]]],
    hashes: dict[str, str], artifacts: list[tuple[Path, bytes, dict[str, Any]]],
) -> None:
    ids = [item[0]["dossierId"] for item in dossiers]
    dossier_outputs = [_artifact(Path(manifest["fileName"]), raw) for _, raw, manifest in dossiers]
    evidence_items = evidence.get("reviewItems", [])
    evidence_ids = [item.get("dossierId") for item in evidence_items]
    locators = {entry.get("locator") for item in evidence_items for key in ("evidenceItems", "counterEvidence") for entry in item.get(key, [])}
    assertions = [entry for item in evidence_items for entry in item.get("evidenceItems", [])]
    finding_ids = {item.get("dossierId"): [finding.get("findingId") for finding in item.get("requiredFindings", [])] for item in evidence_items}
    counter_ids = {item.get("dossierId"): [counter.get("counterEvidenceId") for counter in item.get("counterEvidence", [])] for item in evidence_items}
    schema_ids = dedicated_schema.get("properties", {}).get("dossierId", {}).get("enum")
    required_receipt_fields = set(dedicated_schema.get("required", []))
    required_bindings = {"queueId", "queueSha256", "evidenceContractId", "evidenceContractSha256", "reviewSchemaId", "reviewSchemaSha256"}
    if (
        contract.get("contractId") != "e14-post2005-policy-redesign-review-remediation-contract-v1"
        or contract.get("inputHashes") != hashes
        or hashes.get("dedicatedReviewSchemaSha256") != EXPECTED_DEDICATED_SCHEMA_SHA
        or hashes.get("remediationEvidenceSha256") != EXPECTED_EVIDENCE_SHA
        or hashes.get("remediationPlanSha256") != EXPECTED_PLAN_SHA
        or hashes.get("remediationAuditSchemaSha256") != EXPECTED_AUDIT_SCHEMA_SHA
        or contract.get("expectedDossierIds") != DOSSIER_IDS
        or contract.get("expectedQueueId") != "e14-post2005-policy-redesign-review-queue-v2"
        or contract.get("expectedLegacyQueueId") != queue_v1.get("queueId")
        or contract.get("expectedDedicatedReviewSchemaId") != dedicated_schema.get("$id")
        or contract.get("expectedEvidenceItemCount") != 7
        or contract.get("expectedCounterEvidenceItemCount") != 2
        or contract.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or contract.get("expectedStatus") != STATUS
        or contract.get("nextAllowedAction") != NEXT_ACTION
        or plan.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or plan.get("expectedStatus") != STATUS
        or plan.get("expectedDossierIds") != DOSSIER_IDS
        or plan.get("nextAllowedAction") != NEXT_ACTION
        or proposal.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or queue_v1.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or queue_v1.get("receipts") != []
        or ids != DOSSIER_IDS or len(ids) != len(set(ids))
        or queue_v1.get("proposal") != _artifact(artifacts[1][0], artifacts[1][1])
        or proposal_audit.get("status") != "POST_2005_POLICY_REDESIGN_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
        or proposal_audit.get("outputs", {}).get("dossiers") != dossier_outputs
        or blocked_handoff.get("status") != "POST_2005_POLICY_REDESIGN_HANDOFF_BLOCKED_SCHEMA_ID_INCOMPATIBILITY"
        or blocked_handoff.get("decision", {}).get("handoffReady") is not False
        or legacy_schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or dedicated_schema.get("$id") != "https://macro-regime.local/schemas/e14-policy-redesign-independent-review-v1.json"
        or schema_ids != DOSSIER_IDS
        or not required_bindings <= required_receipt_fields
        or dedicated_schema.get("properties", {}).get("independenceDeclaration", {}).get("const") != DECLARATION
        or evidence.get("evidenceId") != "e14-post2005-policy-redesign-review-remediation-evidence-v1"
        or evidence_ids != DOSSIER_IDS
        or locators != REQUIRED_LOCATORS
        or finding_ids != FINDING_IDS
        or counter_ids != COUNTER_IDS
        or any(entry.get("assertionSha256") != _sha(entry.get("assertion", "").encode("utf-8")) for entry in assertions)
        or any(item.get("dossierSha256") != dossiers[index][2]["sha256"] for index, item in enumerate(evidence_items))
        or any(urlparse(locator).scheme != "https" or urlparse(locator).hostname not in {"www.federalreserve.gov", "www.fdic.gov"} for locator in locators)
        or evidence.get("governance") != {
            "providerPrimaryLocatorsOnly": True,
            "locatorContentNotSnapshotted": True,
            "reviewerMustOpenEveryLocator": True,
            "assertionDigestsAreNotPageContentDigests": True,
            "e14nOutputsMutated": False,
        }
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-policy-redesign-review-remediation-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7p review-remediation inputs are invalid.")


def _completed_accept_specimen(dossier_id: str, dossier_sha: str, queue_sha: str, evidence_sha: str, schema_sha: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "reviewId": f"e14-policy-redesign-review-{dossier_id.removeprefix('e14-post2005-policy-redesign-dossier-')}-reviewer",
        "dossierId": dossier_id,
        "dossierSha256": dossier_sha,
        "queueId": "e14-post2005-policy-redesign-review-queue-v2",
        "queueSha256": queue_sha,
        "evidenceContractId": "e14-post2005-policy-redesign-review-remediation-evidence-v1",
        "evidenceContractSha256": evidence_sha,
        "reviewSchemaId": "https://macro-regime.local/schemas/e14-policy-redesign-independent-review-v1.json",
        "reviewSchemaSha256": schema_sha,
        "reviewerId": "independent-reviewer",
        "reviewerAffiliation": "independent-review-affiliation",
        "independenceDeclaration": DECLARATION,
        "reviewedAt": "2026-07-16",
        "decision": "accept",
        "rationale": "Independent specimen used only to prove that the frozen receipt contract has a valid completion path; it is never published as an authentic review receipt.",
        "findingAssessments": [{"findingId": item, "supported": True, "rationale": "The cited provider-primary evidence supports this required finding."} for item in FINDING_IDS[dossier_id]],
        "counterEvidenceAssessments": [{"counterEvidenceId": item, "considered": True, "rationale": "The named limitation was considered against the proposal semantics."} for item in COUNTER_IDS[dossier_id]],
        "checks": {
            "providerPrimaryLocatorsOpened": True,
            "proposalSemanticsSupported": True,
            "methodologyOrAvailabilityBoundarySupported": True,
            "counterEvidenceConsidered": True,
            "noModelOutputUsed": True,
        },
    }


def _placeholder_specimen(specimen: dict[str, Any]) -> dict[str, Any]:
    placeholder = json.loads(json.dumps(specimen))
    placeholder["reviewerId"] = "__REQUIRED__"
    placeholder["reviewedAt"] = "__YYYY-MM-DD__"
    placeholder["decision"] = "__REQUIRED__"
    placeholder["checks"]["providerPrimaryLocatorsOpened"] = None
    return placeholder


def _validate_completed_receipt_contract(receipt: dict[str, Any], dossier_id: str, queue_sha: str, hashes: dict[str, str]) -> None:
    expected_keys = {"schemaVersion", "reviewId", "dossierId", "dossierSha256", "queueId", "queueSha256", "evidenceContractId", "evidenceContractSha256", "reviewSchemaId", "reviewSchemaSha256", "reviewerId", "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision", "rationale", "findingAssessments", "counterEvidenceAssessments", "checks"}
    checks = receipt.get("checks", {})
    expected_dossier_sha = hashes["crossG5DossierSha256"] if dossier_id == DOSSIER_IDS[0] else hashes["bankFdicDossierSha256"]
    try:
        date.fromisoformat(receipt.get("reviewedAt", ""))
    except ValueError as error:
        raise DatasetValidationError("E14.7p receipt specimen date is invalid.") from error
    if (
        set(receipt) != expected_keys
        or receipt.get("schemaVersion") != 1
        or re.fullmatch(r"e14-policy-redesign-review-[a-z0-9-]+", str(receipt.get("reviewId", ""))) is None
        or receipt.get("dossierId") != dossier_id
        or receipt.get("dossierSha256") != expected_dossier_sha
        or receipt.get("queueId") != "e14-post2005-policy-redesign-review-queue-v2"
        or receipt.get("queueSha256") != queue_sha
        or receipt.get("evidenceContractId") != "e14-post2005-policy-redesign-review-remediation-evidence-v1"
        or receipt.get("evidenceContractSha256") != hashes["remediationEvidenceSha256"]
        or receipt.get("reviewSchemaId") != "https://macro-regime.local/schemas/e14-policy-redesign-independent-review-v1.json"
        or receipt.get("reviewSchemaSha256") != hashes["dedicatedReviewSchemaSha256"]
        or receipt.get("independenceDeclaration") != DECLARATION
        or not receipt.get("reviewerId") or str(receipt.get("reviewerId")).startswith("__")
        or not receipt.get("reviewerAffiliation") or str(receipt.get("reviewerAffiliation")).startswith("__")
        or receipt.get("decision") != "accept"
        or len(receipt.get("rationale", "")) < 100
        or [item.get("findingId") for item in receipt.get("findingAssessments", [])] != FINDING_IDS[dossier_id]
        or not all(set(item) == {"findingId", "supported", "rationale"} and item.get("supported") is True and len(item.get("rationale", "")) >= 20 for item in receipt.get("findingAssessments", []))
        or [item.get("counterEvidenceId") for item in receipt.get("counterEvidenceAssessments", [])] != COUNTER_IDS[dossier_id]
        or not all(set(item) == {"counterEvidenceId", "considered", "rationale"} and item.get("considered") is True and len(item.get("rationale", "")) >= 20 for item in receipt.get("counterEvidenceAssessments", []))
        or set(checks) != {"providerPrimaryLocatorsOpened", "proposalSemanticsSupported", "methodologyOrAvailabilityBoundarySupported", "counterEvidenceConsidered", "noModelOutputUsed"}
        or not all(value is True for value in checks.values())
    ):
        raise DatasetValidationError("E14.7p receipt specimen is not completable under the dedicated contract.")


def _load_dossiers(queue: dict[str, Any], directory: str | Path) -> list[tuple[dict[str, Any], bytes, dict[str, Any]]]:
    root = Path(directory).resolve()
    result = []
    for manifest in queue.get("dossiers", []):
        name = manifest.get("fileName", "")
        if not name or Path(name).name != name:
            raise DatasetValidationError("E14.7p dossier path is invalid.")
        file, raw, dossier = _read(root / name, "policy-redesign dossier")
        if file.parent != root or _sha(raw) != manifest.get("sha256") or len(raw) != manifest.get("sizeBytes") or dossier.get("dossierId") != manifest.get("dossierId"):
            raise DatasetValidationError("E14.7p dossier hash or content is invalid.")
        result.append((dossier, raw, manifest))
    return result


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        return file, raw, payload
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise DatasetValidationError(f"E14.7p {label} is not valid UTF-8 JSON: {file}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write_new(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14.7p remediation output already exists: {path}") from error
