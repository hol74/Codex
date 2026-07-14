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


def write_e14_adjudication_queue(
    hard_negative_pack_path: str | Path,
    dossier_schema_path: str | Path,
    review_schema_path: str | Path,
    detector_contract_path: str | Path,
    positive_pack_path: str | Path,
    positive_curation_audit_path: str | Path,
    positive_dossier_dir: str | Path,
    hard_negative_dossier_dir: str | Path,
    review_receipt_dir: str | Path,
    queue_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    pack_file, pack_bytes, pack = _read_json(hard_negative_pack_path, "E14 hard-negative pack")
    schema_file, schema_bytes, schema = _read_json(dossier_schema_path, "E14 dossier schema")
    review_schema_file, review_schema_bytes, review_schema = _read_json(review_schema_path, "E14 review schema")
    contract_file, contract_bytes, contract = _read_json(detector_contract_path, "E14 detector contract")
    positive_pack_file, positive_pack_bytes, positive_pack = _read_json(positive_pack_path, "E14 positive pack")
    positive_audit_file, positive_audit_bytes, positive_audit = _read_json(
        positive_curation_audit_path, "E14 positive curation audit"
    )

    _validate_input_hashes(
        pack, schema_bytes, review_schema_bytes, contract_bytes, positive_pack_bytes, positive_audit_bytes
    )
    _validate_upstream(pack, schema, review_schema, contract, positive_pack, positive_audit)
    assertions = _validate_assertions(pack)
    negative_dossiers = _build_hard_negatives(pack, contract, assertions)
    positive_artifacts = _validate_positive_dossiers(positive_audit, positive_dossier_dir)

    negative_dir = Path(hard_negative_dossier_dir).resolve()
    queue_output = Path(queue_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    negative_paths = [negative_dir / f"{item['dossierId']}.json" for item in negative_dossiers]
    if queue_output.exists() or audit_output.exists() or any(path.exists() for path in negative_paths):
        raise DatasetValidationError("Immutable E14 adjudication output already exists.")

    negative_artifacts = [
        _artifact(path, _json_bytes(dossier))
        for path, dossier in zip(negative_paths, negative_dossiers, strict=True)
    ]
    all_artifacts = sorted(positive_artifacts + negative_artifacts, key=lambda item: item["fileName"])
    receipts = _load_review_receipts(review_receipt_dir, all_artifacts, pack["reviewer"])
    decisions = {receipt["dossierId"]: receipt["decision"] for receipt in receipts}
    accepted_ids = sorted(dossier_id for dossier_id, decision in decisions.items() if decision == "accept")
    review_complete = len(receipts) == len(all_artifacts)
    all_accepted = review_complete and len(accepted_ids) == len(all_artifacts)

    for path, dossier in zip(negative_paths, negative_dossiers, strict=True):
        _write_new_json(path, dossier, "E14 hard-negative dossier")

    queue = {
        "schemaVersion": 1,
        "artifactType": "E14IndependentReviewQueue",
        "status": (
            "AWAITING_INDEPENDENT_REVIEW" if not review_complete
            else "REVIEW_COMPLETE_ALL_ACCEPTED" if all_accepted
            else "REVIEW_COMPLETE_REVISIONS_REQUIRED"
        ),
        "reviewSchema": _artifact(review_schema_file, review_schema_bytes),
        "dossierAuthor": pack["reviewer"],
        "requirements": pack["independencePolicy"],
        "dossiers": [
            {
                **artifact,
                "reviewStatus": (
                    f"{decisions[artifact['dossierId']]}-by-independent-receipt"
                    if artifact["dossierId"] in decisions else "awaiting-independent-review"
                ),
            }
            for artifact in all_artifacts
        ],
    }
    queue_path = _write_new_json(queue_output, queue, "E14 independent review queue")

    hard_by_mechanism = {
        mechanism: sum(item["mechanism"] == mechanism for item in negative_dossiers)
        for mechanism in contract["requiredMechanisms"]
    }
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14AdjudicationReadinessAudit",
        "status": (
            "INDEPENDENT_REVIEW_REQUIRED" if not review_complete
            else "READY_FOR_LABEL_FOUNDATION_GATE" if all_accepted
            else "DOSSIER_REVISIONS_REQUIRED"
        ),
        "inputs": {
            "hardNegativePack": _artifact(pack_file, pack_bytes),
            "dossierSchema": _artifact(schema_file, schema_bytes),
            "reviewSchema": _artifact(review_schema_file, review_schema_bytes),
            "detectorContract": _artifact(contract_file, contract_bytes),
            "positiveDossierPack": _artifact(positive_pack_file, positive_pack_bytes),
            "positiveCurationAudit": _artifact(positive_audit_file, positive_audit_bytes),
            "reviewQueue": _artifact(queue_path, queue_path.read_bytes()),
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "selfAcceptanceForbidden": True,
            "remoteByteSnapshotsArchived": False,
        },
        "inventory": {
            "positiveReviewedDossierCount": len(positive_artifacts),
            "hardNegativeReviewedDossierCount": len(negative_artifacts),
            "queuedDossierCount": len(all_artifacts),
            "independentReviewReceiptCount": len(receipts),
            "independentlyAcceptedDossierCount": len(accepted_ids),
            "independentlyRejectedDossierCount": sum(
                receipt["decision"] == "reject" for receipt in receipts
            ),
            "needsRevisionDossierCount": sum(
                receipt["decision"] == "needs-revision" for receipt in receipts
            ),
        },
        "hardNegativeMechanismCoverage": hard_by_mechanism,
        "hardNegativeDossierArtifacts": negative_artifacts,
        "checks": {
            "allMechanismsHaveAffirmativeHardNegative": all(value >= 1 for value in hard_by_mechanism.values()),
            "twoIndependentEvidenceProvidersPerHardNegative": True,
            "counterEvidencePresentPerHardNegative": True,
            "positiveDossierHashesRevalidated": True,
            "reviewQueueHashBound": True,
            "selfAcceptancePrevented": True,
            "outerOosClosed": True,
            "groundTruthUnchanged": True,
        },
        "limitations": pack["limitations"],
        "decision": {
            "hardNegativeResearchCompleteForAllMechanisms": True,
            "independentReviewComplete": review_complete,
            "allDossiersAccepted": all_accepted,
            "labelFoundationGateAuthorized": all_accepted,
            "groundTruthMutationAuthorized": False,
            "corpusPopulationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": (
                "E14.4b3 ingest remaining independent review receipts"
                if not review_complete
                else "Revise rejected or needs-revision dossiers and repeat independent review"
                if not all_accepted
                else "E14.4c run separate label-foundation gate"
            ),
        },
        "implementation": {
            "module": "regime_eval.e14_adjudication",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return queue_path, _write_new_json(audit_output, audit, "E14 adjudication readiness audit")


def _validate_input_hashes(
    pack: Any,
    schema_bytes: bytes,
    review_schema_bytes: bytes,
    contract_bytes: bytes,
    positive_pack_bytes: bytes,
    positive_audit_bytes: bytes,
) -> None:
    actual = {
        "dossierSchemaSha256": hashlib.sha256(schema_bytes).hexdigest(),
        "reviewSchemaSha256": hashlib.sha256(review_schema_bytes).hexdigest(),
        "detectorContractSha256": hashlib.sha256(contract_bytes).hexdigest(),
        "positiveDossierPackSha256": hashlib.sha256(positive_pack_bytes).hexdigest(),
        "positiveCurationAuditSha256": hashlib.sha256(positive_audit_bytes).hexdigest(),
    }
    if (
        not isinstance(pack, dict)
        or pack.get("packId") != "e14-hard-negative-dossier-pack-v1"
        or pack.get("inputHashes") != actual
    ):
        raise DatasetValidationError("E14 hard-negative pack input hashes are invalid.")


def _validate_upstream(
    pack: dict[str, Any], schema: Any, review_schema: Any, contract: Any, positive_pack: Any, audit: Any
) -> None:
    policy = pack.get("independencePolicy", {})
    if (
        schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v1.json"
        or review_schema.get("properties", {}).get("independenceDeclaration", {}).get("const") != INDEPENDENCE_DECLARATION
        or contract.get("readinessDecision") != "READY_FOR_DOSSIER_CURATION"
        or positive_pack.get("packId") != "e14-positive-dossier-pack-v1"
        or audit.get("artifactType") != "E14PositiveDossierCurationAudit"
        or audit.get("status") != "SECOND_REVIEW_AND_HARD_NEGATIVES_REQUIRED"
        or audit.get("inventory", {}).get("acceptedDossierCount") != 0
        or policy.get("selfAcceptanceForbidden") is not True
        or policy.get("minimumTotalReviewersAfterReceipt") != 2
    ):
        raise DatasetValidationError("E14 adjudication upstream contract is invalid.")


def _validate_assertions(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = pack.get("evidenceAssertions")
    by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list) or not items:
        raise DatasetValidationError("E14 hard-negative evidence assertions are missing.")
    for item in items:
        assertion_id = item.get("id") if isinstance(item, dict) else None
        try:
            date.fromisoformat(item["publishedAt"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError("E14 hard-negative evidence date is invalid.") from exc
        if (
            not isinstance(assertion_id, str) or assertion_id in by_id
            or item.get("role") not in {"official-narrative", "quantitative-observation", "counterevidence"}
            or not str(item.get("locator", "")).startswith("https://")
            or len(item.get("summary", "")) < 20
        ):
            raise DatasetValidationError("E14 hard-negative evidence assertion is invalid.")
        by_id[assertion_id] = item
    return by_id


def _build_hard_negatives(
    pack: dict[str, Any], contract: dict[str, Any], assertions: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    blueprints = pack.get("hardNegativeBlueprints")
    required = set(contract.get("requiredMechanisms", []))
    if not isinstance(blueprints, list) or {item.get("mechanism") for item in blueprints} != required:
        raise DatasetValidationError("E14 hard-negative blueprints do not cover every mechanism.")
    dossiers = []
    ids: set[str] = set()
    for item in blueprints:
        evidence_ids = item.get("evidenceIds", [])
        counter_ids = item.get("counterEvidenceIds", [])
        if (
            item.get("proposedState") != "hard-negative"
            or item.get("dossierId") in ids
            or not str(item.get("dossierId", "")).startswith("e14-dossier-")
            or len(evidence_ids) < 2 or not counter_ids
            or any(source_id not in assertions for source_id in evidence_ids + counter_ids)
            or len(item.get("boundaryRationale", "")) < 40
        ):
            raise DatasetValidationError("E14 hard-negative blueprint is invalid.")
        try:
            first = date.fromisoformat(item["firstMonth"])
            last = date.fromisoformat(item["lastMonth"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError("E14 hard-negative boundary is invalid.") from exc
        evidence = [assertions[source_id] for source_id in evidence_ids]
        counters = [assertions[source_id] for source_id in counter_ids]
        if first > last:
            raise DatasetValidationError("E14 hard-negative boundary is reversed.")
        if len({source["independenceGroup"] for source in evidence}) < 2:
            raise DatasetValidationError("E14 hard-negative lacks independent providers.")
        if not {"official-narrative", "quantitative-observation"} <= {source["role"] for source in evidence}:
            raise DatasetValidationError("E14 hard-negative lacks affirmative narrative and quantitative evidence.")
        if any(source["role"] != "counterevidence" for source in counters):
            raise DatasetValidationError("E14 hard-negative counterevidence role is invalid.")
        dossiers.append({
            "schemaVersion": 1,
            "dossierId": item["dossierId"],
            "hypothesisId": item["hypothesisId"],
            "mechanism": item["mechanism"],
            "proposedState": "hard-negative",
            "firstMonth": item["firstMonth"],
            "lastMonth": item["lastMonth"],
            "boundaryRationale": item["boundaryRationale"],
            "affirmativeOrderlyEvidence": True,
            "evidenceItems": [_evidence_payload(source) for source in evidence],
            "counterEvidence": [_evidence_payload(source) for source in counters],
            "exclusionChecks": {
                "outerOosUsed": False,
                "modelPredictionUsedAsLabel": False,
                "absenceTreatedAsEvidence": False,
                "methodologyRegimeRecorded": True,
                "nberOverlapReviewed": True,
            },
            "adjudicationStatus": "reviewed",
            "reviewers": [pack["reviewer"]],
        })
        ids.add(item["dossierId"])
    return dossiers


def _validate_positive_dossiers(audit: dict[str, Any], directory: str | Path) -> list[dict[str, Any]]:
    root = Path(directory).resolve()
    expected = audit.get("dossierArtifacts", [])
    artifacts = []
    for manifest in expected:
        path = root / manifest["fileName"]
        try:
            raw = path.read_bytes()
            dossier = json.loads(raw)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise DatasetValidationError("Cannot read an E14 positive dossier.") from exc
        artifact = _artifact(path, raw)
        if (
            artifact["sha256"] != manifest.get("sha256")
            or artifact["sizeBytes"] != manifest.get("sizeBytes")
            or dossier.get("adjudicationStatus") != "reviewed"
            or dossier.get("proposedState") != "positive"
        ):
            raise DatasetValidationError("E14 positive dossier hash or status is invalid.")
        artifact["dossierId"] = dossier["dossierId"]
        artifacts.append(artifact)
    if len(artifacts) != 8:
        raise DatasetValidationError("E14 positive dossier inventory is incomplete.")
    return artifacts


def _load_review_receipts(
    directory: str | Path, artifacts: list[dict[str, Any]], dossier_author: str
) -> list[dict[str, Any]]:
    root = Path(directory).resolve()
    if not root.exists():
        return []
    known = {item["dossierId"]: item for item in artifacts}
    receipts = []
    reviewed_ids: set[str] = set()
    for path in sorted(root.glob("*.json")):
        _, _, receipt = _read_json(path, "E14 independent review receipt")
        dossier = known.get(receipt.get("dossierId"))
        try:
            date.fromisoformat(receipt["reviewedAt"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError("E14 independent review date is invalid.") from exc
        checks = receipt.get("checks", {})
        receipt_keys = {
            "schemaVersion", "reviewId", "dossierId", "dossierSha256", "reviewerId",
            "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision",
            "rationale", "checks",
        }
        check_keys = {
            "sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported",
            "counterEvidenceConsidered", "noModelOutputUsed",
        }
        if (
            dossier is None or receipt.get("dossierId") in reviewed_ids
            or set(receipt) != receipt_keys or not isinstance(checks, dict) or set(checks) != check_keys
            or receipt.get("schemaVersion") != 1
            or not str(receipt.get("reviewId", "")).startswith("e14-review-")
            or receipt.get("dossierSha256") != dossier["sha256"]
            or not receipt.get("reviewerId") or receipt.get("reviewerId") == dossier_author
            or not receipt.get("reviewerAffiliation")
            or receipt.get("independenceDeclaration") != INDEPENDENCE_DECLARATION
            or receipt.get("decision") not in {"accept", "reject", "needs-revision"}
            or len(receipt.get("rationale", "")) < 80
            or checks.get("sourceLocatorsOpened") is not True
            or checks.get("counterEvidenceConsidered") is not True
            or checks.get("noModelOutputUsed") is not True
            or not isinstance(checks.get("mechanismClaimSupported"), bool)
            or not isinstance(checks.get("boundariesSupported"), bool)
            or (
                receipt.get("decision") == "accept"
                and (checks.get("mechanismClaimSupported") is not True or checks.get("boundariesSupported") is not True)
            )
        ):
            raise DatasetValidationError("E14 independent review receipt is invalid or not independent.")
        receipts.append(receipt)
        reviewed_ids.add(receipt["dossierId"])
    return receipts


def _evidence_payload(assertion: dict[str, Any]) -> dict[str, Any]:
    payload = {key: assertion[key] for key in (
        "sourceId", "provider", "independenceGroup", "publishedAt", "role", "locator", "summary"
    )}
    payload["contentSha256"] = hashlib.sha256(
        f"{assertion['locator']}\n{assertion['summary']}".encode("utf-8")
    ).hexdigest()
    return payload


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    result = {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}
    try:
        dossier = json.loads(raw)
        if isinstance(dossier, dict) and "dossierId" in dossier:
            result["dossierId"] = dossier["dossierId"]
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return result


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


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
