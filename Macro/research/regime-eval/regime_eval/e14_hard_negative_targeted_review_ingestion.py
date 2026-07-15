from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_hard_negative_targeted_revision import DECLARATION


PENDING = "awaiting-targeted-expansion-independent-rereview"


def write_e14_hard_negative_targeted_review_ingestion(
    contract_path: str | Path,
    targeted_queue_path: str | Path,
    revision_audit_path: str | Path,
    revision_pack_path: str | Path,
    review_schema_path: str | Path,
    receipt_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path | None, Path]:
    contract_file, contract_raw, contract = _read_json(contract_path, "targeted ingestion contract")
    queue_file, queue_raw, queue = _read_json(targeted_queue_path, "targeted queue v8")
    audit_file, audit_raw, audit = _read_json(revision_audit_path, "targeted revision audit")
    pack_file, pack_raw, pack = _read_json(revision_pack_path, "targeted revision pack")
    schema_file, schema_raw, schema = _read_json(review_schema_path, "review schema v2")
    _validate_inputs(contract, queue, audit, pack, schema, queue_raw, audit_raw, pack_raw, schema_raw)
    receipts, receipt_artifacts = _load_receipts(receipt_dir, queue)

    expected = contract["expectedTargetedReceiptCount"]
    complete = len(receipts) == expected
    counts = {value: sum(item["decision"] == value for item in receipts)
              for value in ("accept", "reject", "needs-revision")}
    all_accepted = complete and counts["accept"] == expected
    preserved_count = contract["expectedPreservedAcceptedDossierCount"]
    prior_independent_hard_negatives = 4 if preserved_count == 14 else 5
    output = Path(output_path).resolve()
    queue_output = Path(queue_output_path).resolve()
    if output.exists() or (complete and queue_output.exists()):
        raise DatasetValidationError("Immutable E14.4g3 targeted ingestion output already exists.")

    reviewed_queue_path: Path | None = None
    reviewed_queue_artifact: dict[str, Any] | None = None
    if complete:
        decisions = {item["dossierId"]: item["decision"] for item in receipts}
        dossiers = []
        for item in queue["dossiers"]:
            if item["reviewStatus"] == PENDING:
                dossiers.append({**item, "reviewStatus":
                                 f"{decisions[item['dossierId']]}-by-targeted-expansion-independent-receipt"})
            else:
                dossiers.append(item)
        reviewed_queue = {
            **queue,
            "status": ("EXPANSION_REVIEW_COMPLETE_ALL_ACCEPTED" if all_accepted
                       else "EXPANSION_TARGETED_REVIEW_COMPLETE_REVISIONS_REQUIRED"),
            "reviewReceipts": [*queue.get("reviewReceipts", []), *receipt_artifacts],
            "dossiers": dossiers,
        }
        reviewed_queue_path = _write_new_json(queue_output, reviewed_queue, "reviewed queue v9")
        reviewed_queue_artifact = _artifact(reviewed_queue_path, reviewed_queue_path.read_bytes())

    status = (contract["decisionPolicy"]["missingReceipt"] if not complete
              else contract["decisionPolicy"]["allAccepted"] if all_accepted
              else contract["decisionPolicy"]["anyRejectOrNeedsRevision"])
    inputs: dict[str, Any] = {
        "ingestionContract": _artifact(contract_file, contract_raw),
        "targetedQueueV8": _artifact(queue_file, queue_raw),
        "targetedRevisionAudit": _artifact(audit_file, audit_raw),
        "targetedRevisionPack": _artifact(pack_file, pack_raw),
        "reviewSchemaV2": _artifact(schema_file, schema_raw),
    }
    if reviewed_queue_artifact:
        inputs["reviewedQueueV9"] = reviewed_queue_artifact
    report = {
        "schemaVersion": 1,
        "artifactType": "E14HardNegativeTargetedReviewIngestionAudit",
        "status": status,
        "inputs": inputs,
        "inventory": {
            "preservedAcceptedDossierCount": preserved_count,
            "expectedTargetedReceiptCount": expected,
            "receivedTargetedReceiptCount": len(receipts),
            "missingTargetedReceiptCount": expected - len(receipts),
            "acceptedTargetedCount": counts["accept"],
            "rejectedTargetedCount": counts["reject"],
            "needsRevisionTargetedCount": counts["needs-revision"],
            "independentReviewerCount": len({item["reviewerId"] for item in receipts}),
            "potentialIndependentHardNegativeEventCount": prior_independent_hard_negatives + counts["accept"],
        },
        "potentialCoverage": {
            "independentHardNegativeEpisodeCount": prior_independent_hard_negatives + counts["accept"],
            "hardNegativeEpisodesPerMechanism": 2 if all_accepted else None,
            "coverageThresholdsSatisfied": all_accepted,
        },
        "receiptArtifacts": receipt_artifacts,
        "checks": {
            "inputHashesValidated": True,
            "onlyChangedHashesEligibleForReview": True,
            "fourteenAcceptedManifestsPreserved": True,
            "receiptSchemaV2Validated": True,
            "dossierHashesBoundToQueue": True,
            "reviewersIndependentFromRevisionAuthor": True,
            "strictAcceptChecksValidated": True,
            "counterEvidenceConsidered": True,
            "modelOutputsExcluded": True,
            "reviewedQueueWrittenOnlyWhenComplete": complete,
        },
        "protocol": {
            "datasetRead": False, "outerFeatureRowCountUsed": 0, "labelsAccepted": 0,
            "taxonomyMutated": False, "candidateGenerated": False, "promotionPerformed": False,
            "reviewPerformedByIngestionProcess": False,
        },
        "decision": {
            "independentReviewComplete": complete,
            "allTargetedDossiersAccepted": all_accepted,
            "hardNegativeCoverageGateAuthorized": all_accepted,
            "taxonomyUpdateAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": ("Collect the missing targeted independent receipts" if not complete
                                  else contract["nextAfterAllAccepted"] if all_accepted
                                  else contract["nextAfterNonAccept"]),
        },
        "implementation": {
            "module": "regime_eval.e14_hard_negative_targeted_review_ingestion",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return reviewed_queue_path, _write_new_json(output, report, "targeted ingestion audit")


def _validate_inputs(contract: Any, queue: Any, audit: Any, pack: Any, schema: Any,
                     queue_raw: bytes, audit_raw: bytes, pack_raw: bytes, schema_raw: bytes) -> None:
    hashes = {
        "targetedQueueV8Sha256": hashlib.sha256(queue_raw).hexdigest(),
        "targetedRevisionAuditSha256": hashlib.sha256(audit_raw).hexdigest(),
        "targetedRevisionPackSha256": hashlib.sha256(pack_raw).hexdigest(),
        "reviewSchemaV2Sha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    dossiers = queue.get("dossiers", []) if isinstance(queue, dict) else []
    pending = [item for item in dossiers if item.get("reviewStatus") == PENDING]
    preserved = [item for item in dossiers if item.get("reviewStatus", "").startswith("accept")]
    contract_id = contract.get("contractId")
    is_v1 = contract_id == "e14-hard-negative-targeted-review-ingestion-contract-v1"
    is_v2 = contract_id == "e14-hard-negative-targeted-review-ingestion-contract-v2"
    expected_preserved = 14 if is_v1 else 15
    expected_receipts = 2 if is_v1 else 1
    if (
        not (is_v1 or is_v2)
        or contract.get("inputHashes") != hashes
        or contract.get("expectedPreservedAcceptedDossierCount") != expected_preserved
        or contract.get("expectedTargetedReceiptCount") != expected_receipts
        or contract.get("readinessDecision") != "READY_TO_VALIDATE_TARGETED_EXPANSION_RECEIPTS"
        or queue.get("status") != "EXPANSION_TARGETED_REREVIEW_REQUIRED"
        or len(dossiers) != 16 or len(preserved) != expected_preserved or len(pending) != expected_receipts
        or set(queue.get("targetedRevisionDossierIds", [])) != {item["dossierId"] for item in pending}
        or audit.get("status") != "AWAITING_TARGETED_EXPANSION_INDEPENDENT_REREVIEW"
        or audit.get("inventory", {}).get("preservedAcceptedDossierCount") != expected_preserved
        or pack.get("packId") != ("e14-hard-negative-targeted-revision-pack-v1" if is_v1
                                  else "e14-hard-negative-targeted-revision-pack-v2")
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
    ):
        raise DatasetValidationError("E14.4g3 targeted ingestion inputs or scope are invalid.")


def _load_receipts(directory: str | Path, queue: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    known = {item["dossierId"]: item for item in queue["dossiers"] if item["reviewStatus"] == PENDING}
    root = Path(directory).resolve()
    if not root.exists():
        return [], []
    if not root.is_dir():
        raise DatasetValidationError("E14.4g3 receipt path is not a directory.")
    receipts, artifacts, seen_dossiers, seen_reviews = [], [], set(), set()
    for path in sorted(root.glob("*.json")):
        source, raw, receipt = _read_json(path, "targeted receipt")
        _validate_receipt(receipt, known, queue["dossierAuthor"], seen_dossiers, seen_reviews)
        receipts.append(receipt)
        artifacts.append({**_artifact(source, raw), "reviewId": receipt["reviewId"],
                          "dossierId": receipt["dossierId"], "reviewerId": receipt["reviewerId"],
                          "decision": receipt["decision"]})
        seen_dossiers.add(receipt["dossierId"]); seen_reviews.add(receipt["reviewId"])
    return receipts, artifacts


def _validate_receipt(receipt: Any, known: dict[str, dict[str, Any]], author: str,
                      seen_dossiers: set[str], seen_reviews: set[str]) -> None:
    keys = {"schemaVersion", "reviewId", "dossierId", "dossierSha256", "reviewerId",
            "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision", "rationale", "checks"}
    check_keys = {"sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported",
                  "counterEvidenceConsidered", "noModelOutputUsed"}
    dossier = known.get(receipt.get("dossierId")) if isinstance(receipt, dict) else None
    checks = receipt.get("checks", {}) if isinstance(receipt, dict) else {}
    try:
        date.fromisoformat(receipt["reviewedAt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError("E14.4g3 receipt date is invalid.") from exc
    if (
        set(receipt) != keys or set(checks) != check_keys or dossier is None
        or receipt["dossierId"] in seen_dossiers or receipt["reviewId"] in seen_reviews
        or receipt.get("schemaVersion") != 2 or receipt.get("dossierSha256") != dossier["sha256"]
        or not receipt.get("reviewerId") or receipt["reviewerId"].startswith("__")
        or receipt["reviewerId"] == author or not receipt.get("reviewerAffiliation")
        or receipt.get("independenceDeclaration") != DECLARATION
        or receipt.get("decision") not in {"accept", "reject", "needs-revision"}
        or len(receipt.get("rationale", "")) < 80
        or any(not isinstance(checks.get(key), bool) for key in check_keys)
        or checks.get("counterEvidenceConsidered") is not True or checks.get("noModelOutputUsed") is not True
        or (receipt["decision"] == "accept" and not all(checks[key] for key in
            ("sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported")))
    ):
        raise DatasetValidationError("E14.4g3 independent receipt is invalid or not independent.")


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes(); return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new_json(path: str | Path, payload: dict[str, Any], label: str) -> Path:
    destination = Path(path).resolve(); destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True); stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{destination}'.") from exc
    return destination
