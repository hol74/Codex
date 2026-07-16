from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_policy_redesign_review_remediation import (
    COUNTER_IDS,
    DECLARATION,
    DOSSIER_IDS,
    FINDING_IDS,
)


QUEUE_SHA = "b14f22a31abf197c1bf3227abfa35c9449003ccef81e52b1b25f583035bceb33"
REMEDIATION_AUDIT_SHA = "b4d70cfb47f90e942cda0c2effe317e57e3e3b287fb962c8dc52921c8054b8ab"
HANDOFF_AUDIT_SHA = "e9b056ca0a2aea811fdb7be4cf4f11419124551ea5ed1e71a5a148b5173a3405"
EVIDENCE_SHA = "6de9c7eb1cc16f8bcf8e44caf59cf9654583010ca271367e1f55950bcaabb6b3"
REVIEW_SCHEMA_SHA = "e0c6a1f4f2cf897552c4bf451849498e0785611c405890eac0fc8b7cc8c51a4a"
REMEDIATION_PLAN_SHA = "fb6dc44263d0e283cac14db802dff17a85ed3377d629bc3001efcbaa8e147e3c"
INGESTION_PLAN_SHA = "34218a8e36b9744e72fa136db398590918f34e4e1120efd42894bf65e594bb3b"
INGESTION_SCHEMA_SHA = "a3538a4437a0ee0ed9a7550ea4d784af258a8f012a2986836420d3565fc427e3"
RECEIPT_POLICY = {
    "exactlyOneReceiptPerDossier": True,
    "exactQueueEvidenceSchemaAndDossierHashesRequired": True,
    "reviewerMustDifferFromProposalAuthor": True,
    "reviewerMustDeclareIndependence": True,
    "everyProviderPrimaryLocatorMustBeOpened": True,
    "everyRequiredFindingMustBeAssessed": True,
    "everyCounterEvidenceItemMustBeConsidered": True,
    "noModelEvaluationOutputMayBeUsed": True,
    "acceptRequiresAllFindingsAndStrictChecks": True,
    "missingDuplicateUnexpectedOrInvalidReceiptFailsBeforeWrite": True,
    "receiptBytesRemainUnchanged": True,
}
AUTHORIZATION_POLICY = {
    "receiptIngestionAuthorized": True,
    "reviewDecisionRecordingAuthorized": True,
    "separatePolicyActivationGateAuthorizedOnlyIfBothAccepted": True,
    "policyActivationPerformedByIngestion": False,
    "requestCatalogGenerationAuthorized": False,
    "sourceAcquisitionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
NEXT_ACCEPTED = (
    "Run a separate versioned policy-activation gate against the reviewed queue v3 "
    "and ingestion audit; do not generate requests, acquire sources, or transform features"
)
NEXT_REVISIONS = (
    "Version only the rejected or needs-revision review materials and repeat "
    "independent review; do not activate policy or acquire sources"
)


def write_e14_post2005_policy_redesign_review_ingestion(
    contract_path: str | Path,
    proposal_path: str | Path,
    review_queue_v2_path: str | Path,
    remediation_audit_path: str | Path,
    handoff_audit_path: str | Path,
    dossier_dir: str | Path,
    evidence_contract_path: str | Path,
    dedicated_review_schema_path: str | Path,
    remediation_plan_path: str | Path,
    ingestion_plan_path: str | Path,
    ingestion_audit_schema_path: str | Path,
    receipt_dir: str | Path,
    reviewed_queue_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    labels = (
        "ingestion contract", "policy-redesign proposal", "review queue v2",
        "review remediation audit", "review handoff audit", "evidence contract",
        "dedicated review schema", "review remediation plan", "ingestion plan",
        "ingestion audit schema",
    )
    paths = (
        contract_path, proposal_path, review_queue_v2_path, remediation_audit_path,
        handoff_audit_path, evidence_contract_path, dedicated_review_schema_path,
        remediation_plan_path, ingestion_plan_path, ingestion_audit_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, proposal, queue, remediation_audit, handoff_audit, evidence, review_schema, remediation_plan, ingestion_plan, ingestion_schema = (
        item[2] for item in artifacts
    )
    dossiers = _load_dossiers(queue, dossier_dir)
    dossier_by_id = {item[0]["dossierId"]: item for item in dossiers}
    hashes = {
        "proposalSha256": _sha(artifacts[1][1]),
        "reviewQueueV2Sha256": _sha(artifacts[2][1]),
        "reviewRemediationAuditSha256": _sha(artifacts[3][1]),
        "reviewHandoffAuditSha256": _sha(artifacts[4][1]),
        "crossG5DossierSha256": _sha(dossier_by_id[DOSSIER_IDS[0]][1]) if DOSSIER_IDS[0] in dossier_by_id else "",
        "bankFdicDossierSha256": _sha(dossier_by_id[DOSSIER_IDS[1]][1]) if DOSSIER_IDS[1] in dossier_by_id else "",
        "evidenceContractSha256": _sha(artifacts[5][1]),
        "dedicatedReviewSchemaSha256": _sha(artifacts[6][1]),
        "reviewRemediationPlanSha256": _sha(artifacts[7][1]),
        "ingestionPlanSha256": _sha(artifacts[8][1]),
        "ingestionAuditSchemaSha256": _sha(artifacts[9][1]),
    }
    _validate_inputs(
        contract, proposal, queue, remediation_audit, handoff_audit, evidence,
        review_schema, remediation_plan, ingestion_plan, ingestion_schema,
        dossiers, hashes, artifacts,
    )
    receipts, receipt_artifacts = _load_receipts(receipt_dir, queue, hashes)

    reviewed_queue_output = Path(reviewed_queue_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    receipt_root = Path(receipt_dir).resolve()
    dossier_root = Path(dossier_dir).resolve()
    immutable_bundle = artifacts[4][0].parent / "e14-post2005-policy-redesign-review-handoff-v1"
    if (
        receipt_root.name != "completed-policy-redesign-receipts-v1"
        or receipt_root == dossier_root
        or receipt_root.is_relative_to(dossier_root)
        or receipt_root == immutable_bundle
        or receipt_root.is_relative_to(immutable_bundle)
    ):
        raise DatasetValidationError("E14.7r receipt directory is invalid or overlaps immutable dossiers.")
    protected_roots = (receipt_root, dossier_root, immutable_bundle.resolve())
    outputs = (reviewed_queue_output, audit_output)
    if (
        any(output.exists() for output in outputs)
        or reviewed_queue_output == audit_output
        or any(output in {item[0] for item in artifacts} for output in outputs)
        or any(output.is_relative_to(root) for output in outputs for root in protected_roots)
    ):
        raise DatasetValidationError("Immutable E14.7r ingestion output already exists or overlaps an input.")

    decisions = {item["dossierId"]: item["decision"] for item in receipts}
    all_accepted = len(receipts) == 2 and all(item["decision"] == "accept" for item in receipts)
    queue_status = "REVIEW_COMPLETE_ALL_ACCEPTED_SEPARATE_POLICY_ACTIVATION_GATE_REQUIRED" if all_accepted else "REVIEW_COMPLETE_REVISIONS_REQUIRED"
    reviewed_queue = {
        **queue,
        "schemaVersion": 3,
        "queueId": "e14-post2005-policy-redesign-reviewed-queue-v3",
        "supersedes": _artifact(artifacts[2][0], artifacts[2][1]),
        "status": queue_status,
        "dossiers": [
            {**item, "reviewStatus": f"{decisions[item['dossierId']]}-by-authentic-independent-receipt"}
            for item in queue["dossiers"]
        ],
        "receipts": receipt_artifacts,
    }
    reviewed_queue_raw = _json_bytes(reviewed_queue)
    status = "POST_2005_POLICY_REDESIGN_REVIEW_ACCEPTED_SEPARATE_ACTIVATION_GATE_REQUIRED" if all_accepted else "POST_2005_POLICY_REDESIGN_REVIEW_REVISIONS_REQUIRED"
    counts = {decision: sum(item["decision"] == decision for item in receipts) for decision in ("accept", "reject", "needs-revision")}
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignReviewIngestionAudit",
        "status": status,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("ingestionContract", "policyRedesignProposal", "reviewQueueV2", "reviewRemediationAudit", "reviewHandoffAudit", "evidenceContract", "dedicatedReviewSchema", "reviewRemediationPlan", "ingestionPlan", "ingestionAuditSchema"),
                artifacts,
            )
        },
        "outputs": {"reviewedQueueV3": _artifact(reviewed_queue_output, reviewed_queue_raw)},
        "inventory": {
            "queuedDossierCount": 2,
            "receiptCount": len(receipts),
            "independentReviewerCount": len({item["reviewerId"] for item in receipts}),
            "acceptedCount": counts["accept"],
            "rejectedCount": counts["reject"],
            "needsRevisionCount": counts["needs-revision"],
        },
        "receiptArtifacts": receipt_artifacts,
        "checks": {
            "allInputHashesExact": True,
            "handoffReadyAndReceiptFree": True,
            "exactlyOneReceiptPerDossier": True,
            "exactQueueEvidenceSchemaAndDossierHashes": True,
            "reviewersIndependentFromProposalAuthor": True,
            "independenceDeclarationsExact": True,
            "everyProviderPrimaryLocatorOpened": True,
            "everyRequiredFindingAssessed": True,
            "everyCounterEvidenceItemConsidered": True,
            "noModelEvaluationOutputUsed": True,
            "acceptDecisionsMeetStrictChecks": True,
            "receiptBytesUnchanged": True,
        },
        "protocol": {
            "receiptContentChangedByIngestion": False,
            "receiptDirectoryOutsideBundle": True,
            "policyActivated": False,
            "requestCatalogGenerated": False,
            "seriesObservationsDownloaded": False,
            "featuresTransformed": 0,
            "candidatesGenerated": 0,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "independentReviewComplete": True,
            "allDossiersAccepted": all_accepted,
            "dossierRevisionsRequired": not all_accepted,
            "separatePolicyActivationGateAuthorized": all_accepted,
            "policyActivated": False,
            "requestCatalogGenerationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": NEXT_ACCEPTED if all_accepted else NEXT_REVISIONS,
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_policy_redesign_review_ingestion",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _write_pair(reviewed_queue_output, reviewed_queue_raw, audit_output, _json_bytes(audit))
    return reviewed_queue_output, audit_output


def _validate_inputs(
    contract: dict[str, Any], proposal: dict[str, Any], queue: dict[str, Any],
    remediation_audit: dict[str, Any], handoff_audit: dict[str, Any], evidence: dict[str, Any],
    review_schema: dict[str, Any], remediation_plan: dict[str, Any], ingestion_plan: dict[str, Any],
    ingestion_schema: dict[str, Any], dossiers: list[tuple[dict[str, Any], bytes, dict[str, Any]]],
    hashes: dict[str, str], artifacts: list[tuple[Path, bytes, dict[str, Any]]],
) -> None:
    canonical_hashes = {
        "reviewQueueV2Sha256": QUEUE_SHA,
        "reviewRemediationAuditSha256": REMEDIATION_AUDIT_SHA,
        "reviewHandoffAuditSha256": HANDOFF_AUDIT_SHA,
        "evidenceContractSha256": EVIDENCE_SHA,
        "dedicatedReviewSchemaSha256": REVIEW_SCHEMA_SHA,
        "reviewRemediationPlanSha256": REMEDIATION_PLAN_SHA,
        "ingestionPlanSha256": INGESTION_PLAN_SHA,
        "ingestionAuditSchemaSha256": INGESTION_SCHEMA_SHA,
    }
    if (
        contract.get("contractId") != "e14-post2005-policy-redesign-review-ingestion-contract-v1"
        or contract.get("inputHashes") != hashes
        or any(hashes.get(key) != value for key, value in canonical_hashes.items())
        or contract.get("expectedDossierIds") != DOSSIER_IDS
        or contract.get("expectedQueueId") != queue.get("queueId")
        or contract.get("expectedReviewedQueueId") != "e14-post2005-policy-redesign-reviewed-queue-v3"
        or contract.get("expectedReceiptCount") != 2
        or contract.get("receiptDirectoryName") != "completed-policy-redesign-receipts-v1"
        or contract.get("receiptPolicy") != RECEIPT_POLICY
        or contract.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or contract.get("nextAllowedActionIfAccepted") != NEXT_ACCEPTED
        or contract.get("nextAllowedActionIfRevisionsRequired") != NEXT_REVISIONS
        or ingestion_plan.get("receiptPolicy") != RECEIPT_POLICY
        or ingestion_plan.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or ingestion_plan.get("expectedReceiptCount") != 2
        or ingestion_plan.get("receiptDirectoryName") != "completed-policy-redesign-receipts-v1"
        or ingestion_plan.get("nextAllowedActionIfAccepted") != NEXT_ACCEPTED
        or ingestion_plan.get("nextAllowedActionIfRevisionsRequired") != NEXT_REVISIONS
        or proposal.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or queue.get("queueId") != "e14-post2005-policy-redesign-review-queue-v2"
        or queue.get("status") != "AWAITING_INDEPENDENT_REVIEW_HANDOFF"
        or queue.get("receipts") != []
        or queue.get("proposal") != _artifact(artifacts[1][0], artifacts[1][1])
        or queue.get("dossiers") != [item[2] for item in dossiers]
        or queue.get("evidenceContract") != _artifact(artifacts[5][0], artifacts[5][1])
        or queue.get("reviewSchema") != _artifact(artifacts[6][0], artifacts[6][1])
        or remediation_audit.get("outputs", {}).get("reviewQueueV2") != _artifact(artifacts[2][0], artifacts[2][1])
        or handoff_audit.get("status") != "POST_2005_POLICY_REDESIGN_EXTERNAL_REVIEW_HANDOFF_READY"
        or handoff_audit.get("decision", {}).get("handoffReady") is not True
        or handoff_audit.get("inventory", {}).get("independentReviewReceiptCount") != 0
        or evidence.get("evidenceId") != "e14-post2005-policy-redesign-review-remediation-evidence-v1"
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-policy-redesign-independent-review-v1.json"
        or remediation_plan.get("expectedDossierIds") != DOSSIER_IDS
        or ingestion_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-policy-redesign-review-ingestion-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7r review-ingestion inputs are invalid.")


def _load_receipts(directory: str | Path, queue: dict[str, Any], hashes: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(directory).resolve()
    if not root.is_dir():
        raise DatasetValidationError("E14.7r receipt directory is missing.")
    files = sorted(root.iterdir())
    if len(files) != 2 or any(not path.is_file() or path.is_symlink() or path.suffix.lower() != ".json" or not _safe_basename(path.name) for path in files):
        raise DatasetValidationError("E14.7r requires exactly two JSON receipt files and no extras.")
    known = {item["dossierId"]: item for item in queue["dossiers"]}
    receipts = []
    receipt_artifacts = []
    seen_dossiers: set[str] = set()
    seen_reviews: set[str] = set()
    for path in files:
        source, raw, receipt = _read(path, "independent review receipt")
        if source.parent != root:
            raise DatasetValidationError("E14.7r receipt path escapes its source directory.")
        _validate_receipt(receipt, known, queue["proposalAuthor"], seen_dossiers, seen_reviews, hashes, source.name)
        receipts.append(receipt)
        artifact = _artifact(source, raw)
        artifact.update({"reviewId": receipt["reviewId"], "dossierId": receipt["dossierId"], "reviewerId": receipt["reviewerId"], "decision": receipt["decision"]})
        receipt_artifacts.append(artifact)
        seen_dossiers.add(receipt["dossierId"])
        seen_reviews.add(receipt["reviewId"])
    if seen_dossiers != set(DOSSIER_IDS):
        raise DatasetValidationError("E14.7r receipts do not cover the exact dossier roster.")
    return sorted(receipts, key=lambda item: item["dossierId"]), sorted(receipt_artifacts, key=lambda item: item["dossierId"])


def _validate_receipt(
    receipt: dict[str, Any], known: dict[str, dict[str, Any]], proposal_author: str,
    seen_dossiers: set[str], seen_reviews: set[str], hashes: dict[str, str], file_name: str,
) -> None:
    expected_keys = {"schemaVersion", "reviewId", "dossierId", "dossierSha256", "queueId", "queueSha256", "evidenceContractId", "evidenceContractSha256", "reviewSchemaId", "reviewSchemaSha256", "reviewerId", "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision", "rationale", "findingAssessments", "counterEvidenceAssessments", "checks"}
    check_keys = {"providerPrimaryLocatorsOpened", "proposalSemanticsSupported", "methodologyOrAvailabilityBoundarySupported", "counterEvidenceConsidered", "noModelOutputUsed"}
    if not isinstance(receipt, dict) or set(receipt) != expected_keys:
        raise DatasetValidationError("E14.7r receipt fields are invalid.")
    dossier_id = receipt.get("dossierId")
    dossier = known.get(dossier_id)
    checks = receipt.get("checks")
    findings = receipt.get("findingAssessments")
    counters = receipt.get("counterEvidenceAssessments")
    try:
        reviewed_at = date.fromisoformat(receipt.get("reviewedAt", ""))
    except (TypeError, ValueError) as error:
        raise DatasetValidationError("E14.7r receipt date is invalid.") from error
    expected_file = f"e14-policy-redesign-review-{dossier_id.removeprefix('e14-post2005-policy-redesign-dossier-')}-{receipt.get('reviewerId')}.json" if isinstance(dossier_id, str) else ""
    if (
        dossier is None or dossier_id in seen_dossiers or receipt.get("reviewId") in seen_reviews
        or receipt.get("schemaVersion") != 1
        or re.fullmatch(r"e14-policy-redesign-review-[a-z0-9-]+", str(receipt.get("reviewId", ""))) is None
        or receipt.get("dossierSha256") != dossier.get("sha256")
        or receipt.get("queueId") != "e14-post2005-policy-redesign-review-queue-v2"
        or receipt.get("queueSha256") != QUEUE_SHA
        or receipt.get("evidenceContractId") != "e14-post2005-policy-redesign-review-remediation-evidence-v1"
        or receipt.get("evidenceContractSha256") != EVIDENCE_SHA
        or receipt.get("reviewSchemaId") != "https://macro-regime.local/schemas/e14-policy-redesign-independent-review-v1.json"
        or receipt.get("reviewSchemaSha256") != REVIEW_SCHEMA_SHA
        or not receipt.get("reviewerId") or receipt.get("reviewerId") == proposal_author or str(receipt.get("reviewerId")).startswith("__")
        or not receipt.get("reviewerAffiliation") or str(receipt.get("reviewerAffiliation")).startswith("__")
        or receipt.get("independenceDeclaration") != DECLARATION
        or reviewed_at > date(2026, 7, 16)
        or receipt.get("decision") not in {"accept", "reject", "needs-revision"}
        or len(receipt.get("rationale", "")) < 100
        or file_name != expected_file
        or not isinstance(findings, list) or [item.get("findingId") for item in findings] != FINDING_IDS[dossier_id]
        or any(not isinstance(item, dict) or set(item) != {"findingId", "supported", "rationale"} or not isinstance(item.get("supported"), bool) or len(item.get("rationale", "")) < 20 for item in findings)
        or not isinstance(counters, list) or [item.get("counterEvidenceId") for item in counters] != COUNTER_IDS[dossier_id]
        or any(not isinstance(item, dict) or set(item) != {"counterEvidenceId", "considered", "rationale"} or item.get("considered") is not True or len(item.get("rationale", "")) < 20 for item in counters)
        or not isinstance(checks, dict) or set(checks) != check_keys or any(not isinstance(value, bool) for value in checks.values())
        or checks.get("providerPrimaryLocatorsOpened") is not True
        or checks.get("counterEvidenceConsidered") is not True
        or checks.get("noModelOutputUsed") is not True
        or (receipt.get("decision") == "accept" and (not all(item["supported"] is True for item in findings) or not all(checks[key] is True for key in check_keys)))
    ):
        raise DatasetValidationError("E14.7r receipt is invalid, unbound, incomplete, or not independent.")


def _load_dossiers(queue: dict[str, Any], directory: str | Path) -> list[tuple[dict[str, Any], bytes, dict[str, Any]]]:
    root = Path(directory).resolve()
    result = []
    for manifest in queue.get("dossiers", []):
        name = manifest.get("fileName", "")
        if not _safe_basename(name):
            raise DatasetValidationError("E14.7r dossier path is invalid.")
        file = (root / name).resolve()
        if not file.is_relative_to(root):
            raise DatasetValidationError("E14.7r dossier path escapes its source directory.")
        source, raw, dossier = _read(file, "policy-redesign dossier")
        if source.parent != root or _sha(raw) != manifest.get("sha256") or len(raw) != manifest.get("sizeBytes") or dossier.get("dossierId") != manifest.get("dossierId"):
            raise DatasetValidationError("E14.7r dossier hash or content is invalid.")
        result.append((dossier, raw, manifest))
    return result


def _safe_basename(name: Any) -> bool:
    return isinstance(name, str) and bool(name) and Path(name).name == name and "/" not in name and "\\" not in name and not Path(name).is_absolute() and ".." not in Path(name).parts


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        return file, raw, payload
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise DatasetValidationError(f"E14.7r {label} is not valid UTF-8 JSON: {file}") from error


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
        raise DatasetValidationError(f"Immutable E14.7r ingestion output already exists: {path}") from error


def _write_pair(first_path: Path, first_raw: bytes, second_path: Path, second_raw: bytes) -> None:
    created: list[Path] = []
    try:
        _write_new(first_path, first_raw)
        created.append(first_path)
        _write_new(second_path, second_raw)
        created.append(second_path)
    except (DatasetValidationError, OSError) as error:
        for path in reversed(created):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        if isinstance(error, DatasetValidationError):
            raise
        raise DatasetValidationError("E14.7r output pair could not be published atomically.") from error
