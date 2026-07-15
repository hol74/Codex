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
ACCEPTED_STATUSES = {
    "accept-by-independent-receipt",
    "accept-by-targeted-independent-receipt",
}


def write_e14_hard_negative_expansion_review_ingestion(
    contract_path: str | Path,
    review_queue_path: str | Path,
    curation_audit_path: str | Path,
    handoff_audit_path: str | Path,
    handoff_contract_path: str | Path,
    review_schema_path: str | Path,
    receipt_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path | None, Path]:
    contract_file, contract_bytes, contract = _read_json(
        contract_path, "E14.4g expansion review ingestion contract"
    )
    queue_file, queue_bytes, queue = _read_json(review_queue_path, "E14 review queue v6")
    curation_file, curation_bytes, curation = _read_json(
        curation_audit_path, "E14.4e curation audit"
    )
    handoff_file, handoff_bytes, handoff = _read_json(
        handoff_audit_path, "E14.4f handoff audit"
    )
    handoff_contract_file, handoff_contract_bytes, handoff_contract = _read_json(
        handoff_contract_path, "E14.4f handoff contract"
    )
    schema_file, schema_bytes, schema = _read_json(
        review_schema_path, "E14 independent review schema v2"
    )
    _validate_inputs(
        contract,
        queue,
        curation,
        handoff,
        handoff_contract,
        schema,
        queue_bytes,
        curation_bytes,
        handoff_bytes,
        handoff_contract_bytes,
        schema_bytes,
    )
    receipts, receipt_artifacts = _load_receipts(receipt_dir, queue, handoff)

    expected = contract["expectedExpansionReceiptCount"]
    complete = len(receipts) == expected
    counts = {
        decision: sum(item["decision"] == decision for item in receipts)
        for decision in ("accept", "reject", "needs-revision")
    }
    all_accepted = complete and counts["accept"] == expected
    output = Path(output_path).resolve()
    queue_output = Path(queue_output_path).resolve()
    if output.exists() or (complete and queue_output.exists()):
        raise DatasetValidationError("Immutable E14.4g expansion ingestion output already exists.")

    reviewed_queue_path: Path | None = None
    reviewed_queue_artifact: dict[str, Any] | None = None
    if complete:
        decisions = {item["dossierId"]: item["decision"] for item in receipts}
        expansion_ids = set(queue["expansionDossierIds"])
        reviewed_dossiers = []
        for item in queue["dossiers"]:
            if item["dossierId"] in expansion_ids:
                reviewed_dossiers.append(
                    {
                        **item,
                        "reviewStatus": (
                            f"{decisions[item['dossierId']]}-by-expansion-independent-receipt"
                        ),
                    }
                )
            else:
                reviewed_dossiers.append(item)
        reviewed_queue = {
            **queue,
            "status": (
                "EXPANSION_REVIEW_COMPLETE_ALL_ACCEPTED"
                if all_accepted
                else "EXPANSION_REVIEW_COMPLETE_REVISIONS_REQUIRED"
            ),
            "reviewReceipts": receipt_artifacts,
            "dossiers": reviewed_dossiers,
        }
        reviewed_queue_path = _write_new_json(
            queue_output, reviewed_queue, "E14.4g reviewed queue v7"
        )
        reviewed_queue_artifact = _artifact(
            reviewed_queue_path, reviewed_queue_path.read_bytes()
        )

    status = (
        contract["decisionPolicy"]["missingReceipt"]
        if not complete
        else contract["decisionPolicy"]["allAccepted"]
        if all_accepted
        else contract["decisionPolicy"]["anyRejectOrNeedsRevision"]
    )
    inputs: dict[str, Any] = {
        "ingestionContract": _artifact(contract_file, contract_bytes),
        "reviewQueueV6": _artifact(queue_file, queue_bytes),
        "curationAudit": _artifact(curation_file, curation_bytes),
        "handoffAudit": _artifact(handoff_file, handoff_bytes),
        "handoffContract": _artifact(handoff_contract_file, handoff_contract_bytes),
        "reviewSchemaV2": _artifact(schema_file, schema_bytes),
    }
    if reviewed_queue_artifact is not None:
        inputs["reviewedQueueV7"] = reviewed_queue_artifact
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14HardNegativeExpansionReviewIngestionAudit",
        "status": status,
        "inputs": inputs,
        "inventory": {
            "preservedAcceptedDossierCount": contract[
                "expectedPreservedAcceptedDossierCount"
            ],
            "expectedExpansionReceiptCount": expected,
            "receivedExpansionReceiptCount": len(receipts),
            "missingExpansionReceiptCount": expected - len(receipts),
            "acceptedExpansionCount": counts["accept"],
            "rejectedExpansionCount": counts["reject"],
            "needsRevisionExpansionCount": counts["needs-revision"],
            "independentReviewerCount": len({item["reviewerId"] for item in receipts}),
        },
        "receiptArtifacts": receipt_artifacts,
        "checks": {
            "queueAndHandoffHashesValidated": True,
            "onlyExpansionHashesEligibleForReview": True,
            "priorAcceptedManifestsPreserved": True,
            "receiptSchemaV2Validated": True,
            "dossierHashesBoundToHandoff": True,
            "reviewersIndependentFromDossierAuthor": True,
            "strictAcceptChecksValidated": True,
            "counterEvidenceConsidered": True,
            "modelOutputsExcluded": True,
            "receiptContentUnchangedByIngestion": True,
            "reviewedQueueWrittenOnlyWhenComplete": complete,
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsAccepted": 0,
            "taxonomyMutated": False,
            "candidateGenerated": False,
            "promotionPerformed": False,
            "reviewPerformedByIngestionProcess": False,
        },
        "decision": {
            "independentReviewComplete": complete,
            "allExpansionDossiersAccepted": all_accepted,
            "expansionDossierRevisionsRequired": complete and not all_accepted,
            "hardNegativeCoverageGateAuthorized": all_accepted,
            "taxonomyUpdateAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": (
                "Collect the missing independent expansion review receipts"
                if not complete
                else contract["nextAfterAllAccepted"]
                if all_accepted
                else contract["nextAfterNonAccept"]
            ),
        },
        "implementation": {
            "module": "regime_eval.e14_hard_negative_expansion_review_ingestion",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    audit_path = _write_new_json(output, payload, "E14.4g expansion ingestion audit")
    return reviewed_queue_path, audit_path


def _validate_inputs(
    contract: Any,
    queue: Any,
    curation: Any,
    handoff: Any,
    handoff_contract: Any,
    schema: Any,
    queue_bytes: bytes,
    curation_bytes: bytes,
    handoff_bytes: bytes,
    handoff_contract_bytes: bytes,
    schema_bytes: bytes,
) -> None:
    actual_hashes = {
        "reviewQueueV6Sha256": hashlib.sha256(queue_bytes).hexdigest(),
        "curationAuditSha256": hashlib.sha256(curation_bytes).hexdigest(),
        "handoffAuditSha256": hashlib.sha256(handoff_bytes).hexdigest(),
        "handoffContractSha256": hashlib.sha256(handoff_contract_bytes).hexdigest(),
        "reviewSchemaV2Sha256": hashlib.sha256(schema_bytes).hexdigest(),
    }
    required_receipt_policy = {
        "schemaV2Required": True,
        "exactlyOneReceiptPerExpansionDossier": True,
        "unexpectedDossierReceiptsForbidden": True,
        "exactHandoffDossierHashRequired": True,
        "reviewerMustDifferFromDossierAuthor": True,
        "independenceDeclarationRequired": True,
        "strictAcceptChecksRequired": True,
        "counterEvidenceRequiredForEveryDecision": True,
        "modelOutputsForbidden": True,
        "receiptContentMustRemainUnchanged": True,
        "priorAcceptedManifestsMustRemainUnchanged": True,
    }
    required_incomplete_policy = {
        "writeReadinessAudit": True,
        "writeReviewedQueue": False,
        "taxonomyMutationAuthorized": False,
        "candidateGenerationAuthorized": False,
    }
    required_authorization = {
        "receiptValidationAuthorized": True,
        "reviewedQueueWriteAuthorizedWhenComplete": True,
        "taxonomyMutationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    dossiers = queue.get("dossiers", []) if isinstance(queue, dict) else []
    prior = dossiers[:12]
    expansion = dossiers[12:]
    handoff_hashes = handoff.get("expansionDossierHashes", {}) if isinstance(handoff, dict) else {}
    queue_hashes = {item.get("dossierId"): item.get("sha256") for item in expansion}
    if (
        not isinstance(contract, dict)
        or contract.get("contractId")
        != "e14-hard-negative-expansion-review-ingestion-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("expectedPreservedAcceptedDossierCount") != 12
        or contract.get("expectedExpansionReceiptCount") != 4
        or contract.get("receiptPolicy") != required_receipt_policy
        or contract.get("incompleteRunPolicy") != required_incomplete_policy
        or contract.get("authorizationPolicy") != required_authorization
        or contract.get("readinessDecision") != "READY_TO_VALIDATE_EXPANSION_RECEIPTS"
        or queue.get("artifactType") != "E14HardNegativeExpansionReviewQueue"
        or queue.get("status") != "EXPANSION_AWAITING_INDEPENDENT_REVIEW"
        or len(dossiers) != 16
        or any(item.get("reviewStatus") not in ACCEPTED_STATUSES for item in prior)
        or len(expansion) != 4
        or any(
            item.get("reviewStatus") != "awaiting-expansion-independent-review"
            for item in expansion
        )
        or curation.get("status") != "INDEPENDENT_REVIEW_REQUIRED"
        or curation.get("decision", {}).get("independentReviewComplete") is not False
        or handoff.get("artifactType") != "E14HardNegativeExpansionHandoffAudit"
        or handoff.get("status") != "EXPANSION_AWAITING_EXTERNAL_REVIEW"
        or handoff.get("decision", {}).get("handoffReady") is not True
        or handoff.get("decision", {}).get("coverageAccepted") is not False
        or handoff_hashes != dict(sorted(queue_hashes.items()))
        or handoff_contract.get("contractId")
        != "e14-hard-negative-expansion-handoff-contract-v1"
        or handoff_contract.get("authorizationPolicy", {}).get(
            "reviewByGeneratorAuthorized"
        )
        is not False
        or schema.get("$id")
        != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or schema.get("properties", {}).get("schemaVersion", {}).get("const") != 2
    ):
        raise DatasetValidationError("E14.4g expansion ingestion inputs or contract are invalid.")


def _load_receipts(
    directory: str | Path,
    queue: dict[str, Any],
    handoff: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    expansion_ids = set(queue["expansionDossierIds"])
    known = {
        item["dossierId"]: item
        for item in queue["dossiers"]
        if item["dossierId"] in expansion_ids
    }
    author = queue["dossierAuthor"]
    handoff_hashes = handoff["expansionDossierHashes"]
    root = Path(directory).resolve()
    receipts: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    seen_dossiers: set[str] = set()
    seen_reviews: set[str] = set()
    if not root.exists():
        return receipts, artifacts
    if not root.is_dir():
        raise DatasetValidationError("E14.4g receipt path is not a directory.")
    for path in sorted(root.glob("*.json")):
        source, raw, receipt = _read_json(path, "E14.4g independent review receipt")
        _validate_receipt(
            receipt,
            known,
            handoff_hashes,
            author,
            seen_dossiers,
            seen_reviews,
        )
        receipts.append(receipt)
        artifact = _artifact(source, raw)
        artifact.update(
            {
                "reviewId": receipt["reviewId"],
                "dossierId": receipt["dossierId"],
                "reviewerId": receipt["reviewerId"],
                "decision": receipt["decision"],
            }
        )
        artifacts.append(artifact)
        seen_dossiers.add(receipt["dossierId"])
        seen_reviews.add(receipt["reviewId"])
    return receipts, artifacts


def _validate_receipt(
    receipt: Any,
    known: dict[str, dict[str, Any]],
    handoff_hashes: dict[str, str],
    author: str,
    seen_dossiers: set[str],
    seen_reviews: set[str],
) -> None:
    receipt_keys = {
        "schemaVersion",
        "reviewId",
        "dossierId",
        "dossierSha256",
        "reviewerId",
        "reviewerAffiliation",
        "independenceDeclaration",
        "reviewedAt",
        "decision",
        "rationale",
        "checks",
    }
    check_keys = {
        "sourceLocatorsOpened",
        "mechanismClaimSupported",
        "boundariesSupported",
        "counterEvidenceConsidered",
        "noModelOutputUsed",
    }
    if not isinstance(receipt, dict):
        raise DatasetValidationError("E14.4g independent review receipt is invalid.")
    dossier = known.get(receipt.get("dossierId"))
    checks = receipt.get("checks")
    try:
        date.fromisoformat(receipt["reviewedAt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError("E14.4g independent review receipt date is invalid.") from exc
    reviewer_id = receipt.get("reviewerId")
    affiliation = receipt.get("reviewerAffiliation")
    if (
        set(receipt) != receipt_keys
        or not isinstance(checks, dict)
        or set(checks) != check_keys
        or dossier is None
        or receipt.get("dossierId") in seen_dossiers
        or receipt.get("reviewId") in seen_reviews
        or receipt.get("schemaVersion") != 2
        or not str(receipt.get("reviewId", "")).startswith("e14-review-")
        or receipt.get("dossierSha256") != dossier.get("sha256")
        or receipt.get("dossierSha256") != handoff_hashes.get(receipt.get("dossierId"))
        or not isinstance(reviewer_id, str)
        or not reviewer_id
        or reviewer_id.startswith("__")
        or reviewer_id == author
        or not isinstance(affiliation, str)
        or not affiliation
        or affiliation.startswith("__")
        or receipt.get("independenceDeclaration") != INDEPENDENCE_DECLARATION
        or receipt.get("decision") not in {"accept", "reject", "needs-revision"}
        or len(receipt.get("rationale", "")) < 80
        or any(not isinstance(checks.get(key), bool) for key in check_keys)
        or checks.get("counterEvidenceConsidered") is not True
        or checks.get("noModelOutputUsed") is not True
        or (
            receipt.get("decision") == "accept"
            and not all(
                checks.get(key) is True
                for key in (
                    "sourceLocatorsOpened",
                    "mechanismClaimSupported",
                    "boundariesSupported",
                )
            )
        )
    ):
        raise DatasetValidationError(
            "E14.4g independent review receipt is invalid or not independent."
        )


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {
        "fileName": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "sizeBytes": len(raw),
    }


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
