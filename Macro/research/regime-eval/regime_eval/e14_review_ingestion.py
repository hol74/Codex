from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


INDEPENDENCE_DECLARATION = (
    "I did not author the dossier or its evidence pack and reviewed the cited evidence independently."
)


def write_e14_review_ingestion(
    contract_path: str | Path,
    review_queue_path: str | Path,
    adjudication_audit_path: str | Path,
    handoff_audit_path: str | Path,
    review_schema_path: str | Path,
    receipt_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 review ingestion contract")
    queue_file, queue_bytes, queue = _read_json(review_queue_path, "E14 review queue")
    audit_file, audit_bytes, audit = _read_json(adjudication_audit_path, "E14 adjudication audit")
    handoff_file, handoff_bytes, handoff = _read_json(handoff_audit_path, "E14 handoff audit")
    schema_file, schema_bytes, schema = _read_json(review_schema_path, "E14 review schema v2")

    _validate_inputs(contract, queue, audit, handoff, schema, queue_bytes, audit_bytes, handoff_bytes, schema_bytes)
    receipts, receipt_artifacts = _load_receipts(receipt_dir, queue)

    output_queue = Path(queue_output_path).resolve()
    output = Path(output_path).resolve()
    if output_queue.exists() or output.exists():
        raise DatasetValidationError("Immutable E14 review ingestion output already exists.")

    decisions = {receipt["dossierId"]: receipt["decision"] for receipt in receipts}
    complete = len(receipts) == len(queue["dossiers"])
    counts = {decision: sum(item["decision"] == decision for item in receipts) for decision in (
        "accept", "reject", "needs-revision"
    )}
    all_accepted = complete and counts["accept"] == len(queue["dossiers"])
    queue_status = (
        "INDEPENDENT_REVIEW_INCOMPLETE" if not complete
        else "REVIEW_COMPLETE_ALL_ACCEPTED" if all_accepted
        else "REVIEW_COMPLETE_REVISIONS_REQUIRED"
    )
    reviewed_queue = {
        **queue,
        "status": queue_status,
        "reviewSchema": _artifact(schema_file, schema_bytes),
        "dossiers": [
            {
                **item,
                "reviewStatus": (
                    f"{decisions[item['dossierId']]}-by-independent-receipt"
                    if item["dossierId"] in decisions else "awaiting-independent-review"
                ),
            }
            for item in queue["dossiers"]
        ],
    }
    queue_path = _write_new_json(output_queue, reviewed_queue, "E14 reviewed queue")

    status = (
        "INDEPENDENT_REVIEW_INCOMPLETE" if not complete
        else "READY_FOR_LABEL_FOUNDATION_GATE" if all_accepted
        else "DOSSIER_REVISIONS_REQUIRED"
    )
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14IndependentReviewIngestionAudit",
        "status": status,
        "inputs": {
            "ingestionContract": _artifact(contract_file, contract_bytes),
            "reviewQueue": _artifact(queue_file, queue_bytes),
            "adjudicationAudit": _artifact(audit_file, audit_bytes),
            "handoffAudit": _artifact(handoff_file, handoff_bytes),
            "reviewSchemaV2": _artifact(schema_file, schema_bytes),
            "reviewedQueue": _artifact(queue_path, queue_path.read_bytes()),
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "receiptContentChangedByIngestion": False,
            "schemaV2Rationale": contract["schemaV2Rationale"],
        },
        "inventory": {
            "queuedDossierCount": len(queue["dossiers"]),
            "receiptCount": len(receipts),
            "independentReviewerCount": len({receipt["reviewerId"] for receipt in receipts}),
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
        "decision": {
            "independentReviewComplete": complete,
            "allDossiersAccepted": all_accepted,
            "dossierRevisionsRequired": complete and not all_accepted,
            "labelFoundationGateAuthorized": all_accepted,
            "groundTruthMutationAuthorized": False,
            "corpusPopulationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": (
                "Collect missing independent receipts"
                if not complete
                else "E14.4c run separate label-foundation gate"
                if all_accepted
                else "E14.4b4 revise needs-revision or rejected dossiers and re-review only changed hashes"
            ),
        },
        "implementation": {
            "module": "regime_eval.e14_review_ingestion",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return queue_path, _write_new_json(output, payload, "E14 review ingestion audit")


def _validate_inputs(
    contract: Any,
    queue: Any,
    audit: Any,
    handoff: Any,
    schema: Any,
    queue_bytes: bytes,
    audit_bytes: bytes,
    handoff_bytes: bytes,
    schema_bytes: bytes,
) -> None:
    actual = {
        "reviewQueueSha256": hashlib.sha256(queue_bytes).hexdigest(),
        "adjudicationAuditSha256": hashlib.sha256(audit_bytes).hexdigest(),
        "handoffAuditSha256": hashlib.sha256(handoff_bytes).hexdigest(),
        "reviewSchemaV2Sha256": hashlib.sha256(schema_bytes).hexdigest(),
    }
    policy = contract.get("receiptPolicy", {}) if isinstance(contract, dict) else {}
    if (
        contract.get("contractId") != "e14-review-ingestion-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("readinessDecision") != "READY_TO_INGEST_INDEPENDENT_REVIEWS"
        or contract.get("expectedDossierCount") != 12
        or not all(policy.values())
        or queue.get("artifactType") != "E14IndependentReviewQueue"
        or queue.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or len(queue.get("dossiers", [])) != 12
        or audit.get("status") != "INDEPENDENT_REVIEW_REQUIRED"
        or handoff.get("status") != "AWAITING_EXTERNAL_REVIEW"
        or handoff.get("decision", {}).get("handoffReady") is not True
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or schema.get("properties", {}).get("schemaVersion", {}).get("const") != 2
    ):
        raise DatasetValidationError("E14 review ingestion inputs or contract are invalid.")


def _load_receipts(
    directory: str | Path, queue: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(directory).resolve()
    known = {item["dossierId"]: item for item in queue["dossiers"]}
    author = queue["dossierAuthor"]
    receipts = []
    artifacts = []
    seen: set[str] = set()
    if not root.exists():
        return receipts, artifacts
    for path in sorted(root.glob("*.json")):
        source, raw, receipt = _read_json(path, "E14 independent review receipt v2")
        _validate_receipt(receipt, known, author, seen)
        receipts.append(receipt)
        artifact = _artifact(source, raw)
        artifact.update({
            "reviewId": receipt["reviewId"],
            "dossierId": receipt["dossierId"],
            "reviewerId": receipt["reviewerId"],
            "decision": receipt["decision"],
        })
        artifacts.append(artifact)
        seen.add(receipt["dossierId"])
    return receipts, artifacts


def _validate_receipt(
    receipt: Any, known: dict[str, dict[str, Any]], author: str, seen: set[str]
) -> None:
    receipt_keys = {
        "schemaVersion", "reviewId", "dossierId", "dossierSha256", "reviewerId",
        "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision",
        "rationale", "checks",
    }
    check_keys = {
        "sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported",
        "counterEvidenceConsidered", "noModelOutputUsed",
    }
    if not isinstance(receipt, dict):
        raise DatasetValidationError("E14 independent review receipt v2 is invalid.")
    dossier = known.get(receipt.get("dossierId"))
    checks = receipt.get("checks")
    try:
        date.fromisoformat(receipt["reviewedAt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError("E14 independent review receipt v2 date is invalid.") from exc
    if (
        set(receipt) != receipt_keys or not isinstance(checks, dict) or set(checks) != check_keys
        or dossier is None or receipt["dossierId"] in seen
        or receipt.get("schemaVersion") != 2
        or not str(receipt.get("reviewId", "")).startswith("e14-review-")
        or receipt.get("dossierSha256") != dossier["sha256"]
        or not receipt.get("reviewerId") or receipt.get("reviewerId") == author
        or not receipt.get("reviewerAffiliation")
        or receipt.get("independenceDeclaration") != INDEPENDENCE_DECLARATION
        or receipt.get("decision") not in {"accept", "reject", "needs-revision"}
        or len(receipt.get("rationale", "")) < 80
        or any(not isinstance(checks.get(key), bool) for key in check_keys)
        or checks.get("counterEvidenceConsidered") is not True
        or checks.get("noModelOutputUsed") is not True
        or (
            receipt.get("decision") == "accept"
            and not all(checks.get(key) is True for key in (
                "sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported"
            ))
        )
    ):
        raise DatasetValidationError("E14 independent review receipt v2 is invalid or not independent.")


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
