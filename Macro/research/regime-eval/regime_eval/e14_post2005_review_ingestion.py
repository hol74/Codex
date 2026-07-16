from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


DECLARATION = "I did not author the dossier or its evidence pack and reviewed the cited evidence independently."


def write_e14_post2005_review_ingestion(
    contract_path: str | Path,
    proposal_path: str | Path,
    review_queue_path: str | Path,
    proposal_audit_path: str | Path,
    handoff_audit_path: str | Path,
    review_schema_path: str | Path,
    receipt_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    labels = ("ingestion contract", "taxonomy proposal", "review queue", "proposal audit", "handoff audit", "review schema")
    paths = (contract_path, proposal_path, review_queue_path, proposal_audit_path, handoff_audit_path, review_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (_, _, contract), (_, _, proposal), (_, _, queue), (_, _, proposal_audit), \
        (_, _, handoff), (schema_file, schema_raw, schema) = artifacts
    hashes = {
        "taxonomyProposalSha256": _sha(artifacts[1][1]),
        "reviewQueueSha256": _sha(artifacts[2][1]),
        "proposalAuditSha256": _sha(artifacts[3][1]),
        "handoffAuditSha256": _sha(artifacts[4][1]),
        "reviewSchemaV2Sha256": _sha(schema_raw),
    }
    _validate_inputs(contract, proposal, queue, proposal_audit, handoff, schema, hashes)
    receipts, receipt_artifacts = _load_receipts(receipt_dir, queue)

    queue_output = Path(queue_output_path).resolve()
    audit_output = Path(output_path).resolve()
    if queue_output.exists() or audit_output.exists():
        raise DatasetValidationError("Immutable E14.7g ingestion output already exists.")

    decisions = {item["dossierId"]: item["decision"] for item in receipts}
    complete = len(receipts) == len(queue["dossiers"])
    counts = {decision: sum(item["decision"] == decision for item in receipts) for decision in ("accept", "reject", "needs-revision")}
    all_accepted = complete and counts["accept"] == len(queue["dossiers"])
    queue_status = "INDEPENDENT_REVIEW_INCOMPLETE" if not complete else "REVIEW_COMPLETE_ALL_ACCEPTED" if all_accepted else "REVIEW_COMPLETE_REVISIONS_REQUIRED"
    reviewed_queue = {
        **queue,
        "status": queue_status,
        "reviewSchema": _artifact(schema_file, schema_raw),
        "dossiers": [
            {**item, "reviewStatus": f"{decisions[item['dossierId']]}-by-independent-receipt" if item["dossierId"] in decisions else "awaiting-independent-review"}
            for item in queue["dossiers"]
        ],
        "receipts": receipt_artifacts,
    }
    queue_raw = _json_bytes(reviewed_queue)
    _write_new(queue_output, queue_raw)

    status = "POST_2005_INDEPENDENT_REVIEW_INCOMPLETE" if not complete else "POST_2005_REVIEW_ACCEPTED_SEPARATE_ACTIVATION_GATE_REQUIRED" if all_accepted else "POST_2005_DOSSIER_REVISIONS_REQUIRED"
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005IndependentReviewIngestionAudit",
        "status": status,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("ingestionContract", "taxonomyProposal", "reviewQueue", "proposalAudit", "handoffAudit", "reviewSchemaV2"),
                artifacts,
            )
        },
        "outputs": {"reviewedQueue": _artifact(queue_output, queue_raw)},
        "inventory": {
            "queuedDossierCount": len(queue["dossiers"]),
            "receiptCount": len(receipts),
            "independentReviewerCount": len({item["reviewerId"] for item in receipts}),
            "acceptedCount": counts["accept"],
            "rejectedCount": counts["reject"],
            "needsRevisionCount": counts["needs-revision"],
        },
        "receiptArtifacts": receipt_artifacts,
        "checks": {
            "receiptSchemaV2Validated": True,
            "dossierHashesBound": True,
            "reviewersIndependentFromAuthor": True,
            "acceptDecisionsMeetStrictChecks": True,
            "counterEvidenceConsidered": True,
            "modelOutputsExcluded": True,
            "selfAcceptancePrevented": True,
        },
        "protocol": {
            "datasetRead": False,
            "loeoScoreRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "receiptContentChangedByIngestion": False,
            "scopeActivated": False,
            "sourceAcquisitionAuthorized": False,
        },
        "decision": {
            "independentReviewComplete": complete,
            "allDossiersAccepted": all_accepted,
            "dossierRevisionsRequired": complete and not all_accepted,
            "separateActivationGateAuthorized": all_accepted,
            "scopeActivated": False,
            "sourceAcquisitionAuthorized": False,
            "candidateGenerationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": "Collect missing independent receipts" if not complete else "E14.7h run a separate post-2005 scope activation gate without acquiring observations" if all_accepted else "Revise only rejected or needs-revision dossier hashes and repeat independent review",
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_review_ingestion",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _write_new(audit_output, _json_bytes(audit))
    return queue_output, audit_output


def _validate_inputs(
    contract: dict[str, Any], proposal: dict[str, Any], queue: dict[str, Any],
    proposal_audit: dict[str, Any], handoff: dict[str, Any], schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    policy = {
        "schemaVersionTwoRequired": True,
        "dossierHashMustMatchQueue": True,
        "reviewerMustDifferFromDossierAuthor": True,
        "oneReceiptPerDossier": True,
        "acceptRequiresAllStrictChecks": True,
        "missingOrInvalidReceiptFailsClosed": True,
        "ingestionCannotActivateScope": True,
    }
    if (
        contract.get("contractId") != "e14-post2005-review-ingestion-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("receiptPolicy") != policy
        or contract.get("expectedDossierCount") != 2
        or contract.get("expectedReceiptCountForCompletion") != 2
        or contract.get("readinessDecision") != "READY_TO_INGEST_EXTERNAL_RECEIPTS_FAIL_CLOSED"
        or proposal.get("activation", {}).get("active") is not False
        or queue.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or len(queue.get("dossiers", [])) != 2
        or queue.get("receipts") != []
        or proposal_audit.get("status") != "POST_2005_TAXONOMY_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
        or handoff.get("status") != "POST_2005_EXTERNAL_REVIEW_HANDOFF_READY"
        or handoff.get("decision", {}).get("handoffReady") is not True
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or schema.get("properties", {}).get("schemaVersion", {}).get("const") != 2
    ):
        raise DatasetValidationError("E14.7g ingestion inputs or contract are invalid.")


def _load_receipts(directory: str | Path, queue: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(directory).resolve()
    known = {item["dossierId"]: item for item in queue["dossiers"]}
    author = queue["dossierAuthor"]
    receipts = []
    artifacts = []
    seen: set[str] = set()
    if not root.exists():
        return receipts, artifacts
    for path in sorted(root.glob("*.json")):
        source, raw, receipt = _read(path, "independent receipt")
        _validate_receipt(receipt, known, author, seen)
        receipts.append(receipt)
        artifact = _artifact(source, raw)
        artifact.update({"reviewId": receipt["reviewId"], "dossierId": receipt["dossierId"], "reviewerId": receipt["reviewerId"], "decision": receipt["decision"]})
        artifacts.append(artifact)
        seen.add(receipt["dossierId"])
    return receipts, artifacts


def _validate_receipt(receipt: Any, known: dict[str, dict[str, Any]], author: str, seen: set[str]) -> None:
    receipt_keys = {"schemaVersion", "reviewId", "dossierId", "dossierSha256", "reviewerId", "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision", "rationale", "checks"}
    check_keys = {"sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported", "counterEvidenceConsidered", "noModelOutputUsed"}
    if not isinstance(receipt, dict):
        raise DatasetValidationError("E14.7g receipt is invalid.")
    dossier = known.get(receipt.get("dossierId"))
    checks = receipt.get("checks")
    try:
        date.fromisoformat(receipt["reviewedAt"])
    except (KeyError, TypeError, ValueError) as error:
        raise DatasetValidationError("E14.7g receipt date is invalid.") from error
    if (
        set(receipt) != receipt_keys or not isinstance(checks, dict) or set(checks) != check_keys
        or dossier is None or receipt["dossierId"] in seen
        or receipt.get("schemaVersion") != 2
        or not str(receipt.get("reviewId", "")).startswith("e14-review-")
        or receipt.get("dossierSha256") != dossier["sha256"]
        or not receipt.get("reviewerId") or receipt.get("reviewerId") == author
        or not receipt.get("reviewerAffiliation")
        or receipt.get("independenceDeclaration") != DECLARATION
        or receipt.get("decision") not in {"accept", "reject", "needs-revision"}
        or len(receipt.get("rationale", "")) < 80
        or any(not isinstance(checks.get(key), bool) for key in check_keys)
        or checks.get("counterEvidenceConsidered") is not True
        or checks.get("noModelOutputUsed") is not True
        or (receipt.get("decision") == "accept" and not all(checks.get(key) is True for key in ("sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported")))
    ):
        raise DatasetValidationError("E14.7g receipt is invalid or not independent.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        return file, raw, json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7g {label} is not valid UTF-8 JSON: {file}") from error


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
        raise DatasetValidationError(f"Immutable E14.7g ingestion output already exists: {path}") from error
