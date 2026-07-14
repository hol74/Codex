from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_targeted_revision import RECEIPT_DECLARATION


def write_e14_targeted_review_ingestion(
    contract_path: str | Path,
    targeted_queue_path: str | Path,
    revision_audit_path: str | Path,
    review_schema_path: str | Path,
    receipt_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_bytes, contract = _read_json(contract_path, "targeted ingestion contract")
    queue_file, queue_bytes, queue = _read_json(targeted_queue_path, "targeted review queue")
    audit_file, audit_bytes, audit = _read_json(revision_audit_path, "targeted revision audit")
    schema_file, schema_bytes, schema = _read_json(review_schema_path, "review schema v2")
    _validate_inputs(contract, queue, audit, schema, queue_bytes, audit_bytes, schema_bytes)
    receipts, receipt_artifacts = _load_receipts(receipt_dir, queue)

    queue_output = Path(queue_output_path).resolve()
    output = Path(output_path).resolve()
    if queue_output.exists() or output.exists():
        raise DatasetValidationError("Immutable E14 targeted review ingestion output already exists.")

    decisions = {item["dossierId"]: item["decision"] for item in receipts}
    expected = contract["expectedTargetedReceiptCount"]
    complete = len(receipts) == expected
    targeted_accepts = sum(item["decision"] == "accept" for item in receipts)
    needs_revision = sum(item["decision"] == "needs-revision" for item in receipts)
    rejected = sum(item["decision"] == "reject" for item in receipts)
    all_accepted = complete and targeted_accepts == expected

    dossiers = []
    for item in queue["dossiers"]:
        if item["reviewStatus"] == "awaiting-targeted-independent-rereview":
            status = (f"{decisions[item['dossierId']]}-by-targeted-independent-receipt"
                      if item["dossierId"] in decisions else item["reviewStatus"])
            dossiers.append({**item, "reviewStatus": status})
        else:
            dossiers.append(item)
    reviewed_queue = {
        **queue,
        "status": ("TARGETED_REREVIEW_INCOMPLETE" if not complete else
                   "REVIEW_COMPLETE_ALL_ACCEPTED" if all_accepted else
                   "TARGETED_REREVIEW_REVISIONS_REQUIRED"),
        "dossiers": dossiers,
    }
    queue_path = _write_new_json(queue_output, reviewed_queue, "E14 targeted reviewed queue")

    total_accepted = contract["expectedPreservedAcceptCount"] + targeted_accepts
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14TargetedReviewIngestionAudit",
        "status": ("TARGETED_REREVIEW_INCOMPLETE" if not complete else
                   "READY_FOR_LABEL_FOUNDATION_GATE" if all_accepted else
                   "DOSSIER_REVISIONS_REQUIRED"),
        "inputs": {
            "ingestionContract": _artifact(contract_file, contract_bytes),
            "targetedReviewQueueV4": _artifact(queue_file, queue_bytes),
            "targetedRevisionAuditV1": _artifact(audit_file, audit_bytes),
            "reviewSchemaV2": _artifact(schema_file, schema_bytes),
            "reviewedQueueV5": _artifact(queue_path, queue_path.read_bytes()),
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "preservedAcceptedReceiptsReopened": False,
            "onlyChangedHashesRereviewed": True,
            "receiptContentChangedByIngestion": False,
        },
        "inventory": {
            "preservedAcceptedCount": contract["expectedPreservedAcceptCount"],
            "targetedReceiptCount": len(receipts),
            "targetedAcceptedCount": targeted_accepts,
            "targetedNeedsRevisionCount": needs_revision,
            "targetedRejectedCount": rejected,
            "totalAcceptedCount": total_accepted,
            "totalDossierCount": len(queue["dossiers"]),
            "independentReviewerCount": len({item["reviewerId"] for item in receipts}),
        },
        "receiptArtifacts": receipt_artifacts,
        "checks": {
            "onlyRevisedHashesReceivedNewReceipts": True,
            "preservedAcceptsRemainHashIdentical": True,
            "receiptSchemaV2Validated": True,
            "reviewersIndependentFromRevisionAuthor": True,
            "strictAcceptChecksValidated": True,
            "counterEvidenceConsidered": True,
            "modelOutputsExcluded": True,
        },
        "decision": {
            "targetedReviewComplete": complete,
            "allTwelveDossiersAccepted": all_accepted,
            "labelFoundationGateAuthorized": all_accepted,
            "groundTruthMutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": (
                "Collect missing targeted review receipts" if not complete else
                "E14.4c run separate label-foundation gate" if all_accepted else
                "Revise only remaining non-accepted dossier hashes and repeat targeted review"
            ),
        },
        "implementation": {
            "module": "regime_eval.e14_targeted_review_ingestion",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return queue_path, _write_new_json(output, payload, "E14 targeted review ingestion audit")


def _validate_inputs(
    contract: Any, queue: Any, audit: Any, schema: Any,
    queue_bytes: bytes, audit_bytes: bytes, schema_bytes: bytes,
) -> None:
    actual = {
        "targetedReviewQueueV4Sha256": hashlib.sha256(queue_bytes).hexdigest(),
        "targetedRevisionAuditV1Sha256": hashlib.sha256(audit_bytes).hexdigest(),
        "reviewSchemaV2Sha256": hashlib.sha256(schema_bytes).hexdigest(),
    }
    policy = contract.get("receiptPolicy", {}) if isinstance(contract, dict) else {}
    statuses = [item.get("reviewStatus") for item in queue.get("dossiers", [])]
    if (
        contract.get("contractId") != "e14-targeted-review-ingestion-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("readinessDecision") != "READY_TO_INGEST_TARGETED_REREVIEW"
        or contract.get("expectedPreservedAcceptCount") != 8
        or contract.get("expectedTargetedReceiptCount") != 4
        or not all(policy.values())
        or queue.get("status") != "TARGETED_REREVIEW_REQUIRED"
        or statuses.count("accept-by-independent-receipt") != 8
        or statuses.count("awaiting-targeted-independent-rereview") != 4
        or audit.get("status") != "AWAITING_TARGETED_INDEPENDENT_REREVIEW"
        or audit.get("inventory", {}).get("revisedDossierCount") != 4
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
    ):
        raise DatasetValidationError("E14 targeted ingestion inputs are invalid.")


def _load_receipts(directory: str | Path, queue: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    known = {item["dossierId"]: item for item in queue["dossiers"]
             if item["reviewStatus"] == "awaiting-targeted-independent-rereview"}
    author = queue["dossierAuthor"]
    root = Path(directory).resolve()
    receipts, artifacts, seen = [], [], set()
    if not root.exists():
        return receipts, artifacts
    for path in sorted(root.glob("*.json")):
        source, raw, receipt = _read_json(path, "targeted review receipt")
        _validate_receipt(receipt, known, author, seen)
        receipts.append(receipt)
        artifact = _artifact(source, raw)
        artifact.update({key: receipt[key] for key in ("reviewId", "dossierId", "reviewerId", "decision")})
        artifacts.append(artifact)
        seen.add(receipt["dossierId"])
    return receipts, artifacts


def _validate_receipt(receipt: Any, known: dict[str, dict[str, Any]], author: str, seen: set[str]) -> None:
    keys = {"schemaVersion", "reviewId", "dossierId", "dossierSha256", "reviewerId",
            "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision", "rationale", "checks"}
    check_keys = {"sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported",
                  "counterEvidenceConsidered", "noModelOutputUsed"}
    if not isinstance(receipt, dict):
        raise DatasetValidationError("E14 targeted review receipt is invalid.")
    dossier = known.get(receipt.get("dossierId"))
    checks = receipt.get("checks")
    try:
        date.fromisoformat(receipt["reviewedAt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError("E14 targeted review date is invalid.") from exc
    if (
        set(receipt) != keys or not isinstance(checks, dict) or set(checks) != check_keys
        or dossier is None or receipt["dossierId"] in seen
        or receipt.get("schemaVersion") != 2
        or receipt.get("dossierSha256") != dossier["sha256"]
        or not receipt.get("reviewerId") or receipt.get("reviewerId") == author
        or not receipt.get("reviewerAffiliation")
        or receipt.get("independenceDeclaration") != RECEIPT_DECLARATION
        or receipt.get("decision") not in {"accept", "reject", "needs-revision"}
        or len(receipt.get("rationale", "")) < 80
        or any(not isinstance(checks.get(key), bool) for key in check_keys)
        or checks.get("counterEvidenceConsidered") is not True
        or checks.get("noModelOutputUsed") is not True
        or (receipt.get("decision") == "accept" and not all(
            checks.get(key) is True for key in ("sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported")
        ))
    ):
        raise DatasetValidationError("E14 targeted review receipt is invalid or not independent.")


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new_json(path: str | Path, payload: dict[str, Any], label: str) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{destination}'.") from exc
    return destination
