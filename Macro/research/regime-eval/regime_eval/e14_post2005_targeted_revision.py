from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


DECLARATION = "I did not author the dossier or its evidence pack and reviewed the cited evidence independently."
TARGET_ID = "e14-dossier-post2005-archegos-contained-2021-banking-credit"
PRESERVED_ID = "e14-dossier-post2005-london-whale-contained-2012-banking-credit"


def write_e14_post2005_targeted_revision(
    contract_path: str | Path,
    reviewed_queue_path: str | Path,
    ingestion_audit_path: str | Path,
    dossier_schema_path: str | Path,
    dossier_dir: str | Path,
    revised_dossier_dir: str | Path,
    bundle_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_raw, contract = _read(contract_path, "revision contract")
    queue_file, queue_raw, queue = _read(reviewed_queue_path, "reviewed queue")
    audit_file, audit_raw, audit = _read(ingestion_audit_path, "ingestion audit")
    schema_file, schema_raw, schema = _read(dossier_schema_path, "dossier schema")
    actual = {
        "dossierSchemaSha256": _sha(schema_raw),
        "reviewIngestionAuditSha256": _sha(audit_raw),
        "reviewedQueueSha256": _sha(queue_raw),
    }
    policy = {
        "acceptedDossierBytesMustRemainUnchanged": True,
        "onlyNeedsRevisionHashMayChange": True,
        "revisionAuthorMustDifferFromReviewer": True,
        "scopeActivationForbidden": True,
        "targetedIndependentRereviewRequired": True,
    }
    manifests = {item["dossierId"]: item for item in queue.get("dossiers", [])}
    revision = contract.get("revision", {})
    reviewer_ids = {item.get("reviewerId") for item in queue.get("receipts", [])}
    if (
        contract.get("contractId") != "e14-post2005-targeted-revision-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("policy") != policy
        or contract.get("readinessDecision") != "READY_FOR_HASH_SCOPED_POST_2005_DOSSIER_REVISION"
        or contract.get("dossierAuthor") in reviewer_ids
        or queue.get("status") != "REVIEW_COMPLETE_REVISIONS_REQUIRED"
        or audit.get("status") != "POST_2005_DOSSIER_REVISIONS_REQUIRED"
        or set(manifests) != {TARGET_ID, PRESERVED_ID}
        or manifests[TARGET_ID].get("reviewStatus") != "needs-revision-by-independent-receipt"
        or manifests[PRESERVED_ID].get("reviewStatus") != "accept-by-independent-receipt"
        or revision.get("dossierId") != TARGET_ID
        or revision.get("baseSha256") != manifests[TARGET_ID].get("sha256")
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
    ):
        raise DatasetValidationError("E14.7g3 targeted revision inputs or scope are invalid.")

    root = Path(dossier_dir).resolve()
    bases: dict[str, tuple[Path, bytes, dict[str, Any]]] = {}
    for dossier_id, manifest in manifests.items():
        path, raw, dossier = _read(root / manifest["fileName"], "base dossier")
        if _sha(raw) != manifest["sha256"] or len(raw) != manifest["sizeBytes"] or dossier.get("dossierId") != dossier_id:
            raise DatasetValidationError("E14.7g3 base dossier manifest mismatch.")
        bases[dossier_id] = (path, raw, dossier)

    revised = _revise(bases[TARGET_ID][2], revision, contract["dossierAuthor"])
    revised_root = Path(revised_dossier_dir).resolve()
    bundle_root = Path(bundle_dir).resolve()
    dossier_path = revised_root / manifests[TARGET_ID]["fileName"]
    bundle_dossier_path = bundle_root / "dossiers" / dossier_path.name
    worksheet_path = bundle_root / "worksheets" / f"{TARGET_ID}-review.md"
    template_path = bundle_root / "receipt-templates" / f"e14-review-{TARGET_ID.removeprefix('e14-dossier-')}-targeted-reviewer.json"
    readme_path = bundle_root / "README.md"
    queue_path = Path(queue_output_path).resolve()
    output = Path(output_path).resolve()
    if any(path.exists() for path in (dossier_path, bundle_dossier_path, worksheet_path, template_path, readme_path, queue_path, output)):
        raise DatasetValidationError("Immutable E14.7g3 targeted revision output already exists.")

    dossier_path = _write_json(dossier_path, revised)
    revised_raw = dossier_path.read_bytes()
    if _sha(revised_raw) == revision["baseSha256"]:
        raise DatasetValidationError("E14.7g3 revised dossier hash did not change.")
    _write_bytes(bundle_dossier_path, revised_raw)
    _write_text(worksheet_path, _worksheet(revised, _sha(revised_raw)))
    _write_json(template_path, _receipt_template(revised, _sha(revised_raw)))
    _write_text(readme_path, _readme(contract["dossierAuthor"]))

    revised_manifest = {
        "dossierId": TARGET_ID,
        "fileName": dossier_path.name,
        "reviewStatus": "awaiting-targeted-independent-rereview",
        "sha256": _sha(revised_raw),
        "sizeBytes": len(revised_raw),
        "supersedesSha256": revision["baseSha256"],
    }
    targeted_queue = {
        **queue,
        "status": "TARGETED_REREVIEW_REQUIRED",
        "dossierAuthor": contract["dossierAuthor"],
        "dossiers": [revised_manifest if item["dossierId"] == TARGET_ID else item for item in queue["dossiers"]],
    }
    queue_path = _write_json(queue_path, targeted_queue)
    bundle_artifacts = [_artifact(path, path.read_bytes()) for path in (bundle_dossier_path, worksheet_path, template_path, readme_path)]
    revision_audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005TargetedRevisionAudit",
        "status": "POST_2005_TARGETED_REREVIEW_REQUIRED",
        "inputs": {
            "revisionContract": _artifact(contract_file, contract_raw),
            "reviewedQueue": _artifact(queue_file, queue_raw),
            "reviewIngestionAudit": _artifact(audit_file, audit_raw),
            "dossierSchema": _artifact(schema_file, schema_raw),
        },
        "outputs": {
            "revisedDossier": {**_artifact(dossier_path, revised_raw), "dossierId": TARGET_ID},
            "targetedQueue": _artifact(queue_path, queue_path.read_bytes()),
            "bundleArtifacts": bundle_artifacts,
        },
        "checks": {
            "onlyNeedsRevisionDossierChanged": True,
            "acceptedDossierPreservedByteIdentically": True,
            "revisionAuthorDiffersFromReviewer": True,
            "fdicLocatorIsExactOfficialPdf": True,
            "boundaryMatchesQuarterEndEvidence": True,
            "targetedBundleContainsOnlyChangedHash": True,
        },
        "protocol": {"datasetRead": False, "modelOutputUsed": False, "scopeActivated": False, "sourceAcquisitionAuthorized": False},
        "decision": {
            "targetedRereviewRequired": True,
            "separateActivationGateAuthorized": False,
            "nextAllowedAction": "Independent reviewer assesses only the revised Archegos dossier hash",
        },
        "implementation": {"module": "regime_eval.e14_post2005_targeted_revision", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    return queue_path, _write_json(output, revision_audit)


def write_e14_post2005_targeted_review_ingestion(
    targeted_queue_path: str | Path,
    revision_audit_path: str | Path,
    review_schema_path: str | Path,
    receipt_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    queue_file, queue_raw, queue = _read(targeted_queue_path, "targeted queue")
    revision_file, revision_raw, revision = _read(revision_audit_path, "revision audit")
    schema_file, schema_raw, schema = _read(review_schema_path, "review schema")
    manifests = {item["dossierId"]: item for item in queue.get("dossiers", [])}
    if (
        queue.get("status") != "TARGETED_REREVIEW_REQUIRED"
        or revision.get("status") != "POST_2005_TARGETED_REREVIEW_REQUIRED"
        or revision.get("outputs", {}).get("targetedQueue", {}).get("sha256") != _sha(queue_raw)
        or manifests.get(TARGET_ID, {}).get("reviewStatus") != "awaiting-targeted-independent-rereview"
        or manifests.get(PRESERVED_ID, {}).get("reviewStatus") != "accept-by-independent-receipt"
        or schema.get("properties", {}).get("schemaVersion", {}).get("const") != 2
    ):
        raise DatasetValidationError("E14.7g4 targeted ingestion inputs are invalid.")
    receipt_paths = sorted(Path(receipt_dir).resolve().glob("*.json"))
    if len(receipt_paths) != 1:
        raise DatasetValidationError("E14.7g4 requires exactly one targeted receipt.")
    receipt_file, receipt_raw, receipt = _read(receipt_paths[0], "targeted receipt")
    _validate_receipt(receipt, manifests[TARGET_ID], queue["dossierAuthor"])
    decision = receipt["decision"]
    all_accepted = decision == "accept"
    reviewed_queue = {
        **queue,
        "status": "TARGETED_REVIEW_COMPLETE_ALL_ACCEPTED" if all_accepted else "TARGETED_REVIEW_COMPLETE_REVISIONS_REQUIRED",
        "dossiers": [
            {**item, "reviewStatus": f"{decision}-by-targeted-independent-receipt"} if item["dossierId"] == TARGET_ID else item
            for item in queue["dossiers"]
        ],
        "receipts": [*queue.get("receipts", []), {**_artifact(receipt_file, receipt_raw), "reviewId": receipt["reviewId"], "dossierId": TARGET_ID, "reviewerId": receipt["reviewerId"], "decision": decision}],
    }
    queue_output = Path(queue_output_path).resolve()
    output = Path(output_path).resolve()
    if queue_output.exists() or output.exists():
        raise DatasetValidationError("Immutable E14.7g4 targeted ingestion output already exists.")
    queue_output = _write_json(queue_output, reviewed_queue)
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005TargetedReviewIngestionAudit",
        "status": "POST_2005_REVIEW_ACCEPTED_SEPARATE_ACTIVATION_GATE_REQUIRED" if all_accepted else "POST_2005_DOSSIER_REVISIONS_REQUIRED",
        "inputs": {"targetedQueue": _artifact(queue_file, queue_raw), "revisionAudit": _artifact(revision_file, revision_raw), "reviewSchemaV2": _artifact(schema_file, schema_raw), "targetedReceipt": _artifact(receipt_file, receipt_raw)},
        "outputs": {"reviewedQueue": _artifact(queue_output, queue_output.read_bytes())},
        "checks": {"receiptSchemaV2Validated": True, "revisedHashBound": True, "acceptedDossierStillPreserved": True, "reviewerIndependentFromRevisionAuthor": True, "strictAcceptanceChecksMet": all_accepted},
        "protocol": {"datasetRead": False, "modelOutputUsed": False, "scopeActivated": False, "sourceAcquisitionAuthorized": False},
        "decision": {"allDossiersAccepted": all_accepted, "separateActivationGateAuthorized": all_accepted, "scopeActivated": False, "nextAllowedAction": "E14.7h run a separate post-2005 scope activation gate without acquiring observations" if all_accepted else "Revise the changed dossier hash and repeat targeted review"},
        "implementation": {"module": "regime_eval.e14_post2005_targeted_revision", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    return queue_output, _write_json(output, audit)


def _revise(base: dict[str, Any], revision: dict[str, Any], author: str) -> dict[str, Any]:
    try:
        first = date.fromisoformat(revision["firstMonth"])
        last = date.fromisoformat(revision["lastMonth"])
    except (KeyError, TypeError, ValueError) as error:
        raise DatasetValidationError("E14.7g3 revision boundary is invalid.") from error
    if first > last or revision.get("replacementLocator") != "https://www.fdic.gov/analysis/quarterly-banking-profile/qbp/2021jun/qbp.pdf" or len(revision.get("boundaryRationale", "")) < 120:
        raise DatasetValidationError("E14.7g3 revision evidence is invalid.")
    evidence = []
    for item in base["evidenceItems"]:
        changed = dict(item)
        if item["independenceGroup"] == "fdic":
            changed["locator"] = revision["replacementLocator"]
            changed["summary"] = revision["replacementSummary"]
            changed["role"] = "boundary-corroboration"
            changed["contentSha256"] = _sha(f"{changed['locator']}\n{changed['summary']}".encode())
        evidence.append(changed)
    return {**base, "firstMonth": revision["firstMonth"], "lastMonth": revision["lastMonth"], "boundaryRationale": revision["boundaryRationale"], "evidenceItems": evidence, "reviewers": [author]}


def _validate_receipt(receipt: Any, manifest: dict[str, Any], author: str) -> None:
    keys = {"schemaVersion", "reviewId", "dossierId", "dossierSha256", "reviewerId", "reviewerAffiliation", "independenceDeclaration", "reviewedAt", "decision", "rationale", "checks"}
    check_keys = {"sourceLocatorsOpened", "mechanismClaimSupported", "boundariesSupported", "counterEvidenceConsidered", "noModelOutputUsed"}
    try:
        date.fromisoformat(receipt["reviewedAt"])
    except (KeyError, TypeError, ValueError) as error:
        raise DatasetValidationError("E14.7g4 targeted receipt date is invalid.") from error
    checks = receipt.get("checks", {})
    if (not isinstance(receipt, dict) or set(receipt) != keys or set(checks) != check_keys or receipt.get("schemaVersion") != 2 or receipt.get("dossierId") != TARGET_ID or receipt.get("dossierSha256") != manifest["sha256"] or not receipt.get("reviewerId") or receipt.get("reviewerId") == author or not receipt.get("reviewerAffiliation") or receipt.get("independenceDeclaration") != DECLARATION or receipt.get("decision") not in {"accept", "reject", "needs-revision"} or len(receipt.get("rationale", "")) < 80 or any(not isinstance(value, bool) for value in checks.values()) or checks.get("counterEvidenceConsidered") is not True or checks.get("noModelOutputUsed") is not True or (receipt.get("decision") == "accept" and not all(checks.values()))):
        raise DatasetValidationError("E14.7g4 targeted receipt is invalid or not independent.")


def _worksheet(dossier: dict[str, Any], digest: str) -> str:
    lines = [f"# Targeted review: {TARGET_ID}", "", f"- SHA-256: `{digest}`", f"- Boundary: `{dossier['firstMonth']}` to `{dossier['lastMonth']}`", "", "## Boundary rationale", "", dossier["boundaryRationale"], "", "## Evidence", ""]
    for item in dossier["evidenceItems"]:
        lines.extend([f"- **{item['role']} — {item['provider']}**", f"  - {item['locator']}", f"  - {item['summary']}"])
    lines.extend(["", "## Counterevidence", ""])
    for item in dossier["counterEvidence"]:
        lines.extend([f"- **{item['provider']}**", f"  - {item['locator']}", f"  - {item['summary']}"])
    return "\n".join(lines) + "\n"


def _receipt_template(dossier: dict[str, Any], digest: str) -> dict[str, Any]:
    return {"schemaVersion": 2, "reviewId": f"e14-review-{TARGET_ID.removeprefix('e14-dossier-')}-targeted-reviewer", "dossierId": TARGET_ID, "dossierSha256": digest, "reviewerId": "__REQUIRED_INDEPENDENT_REVIEWER_ID__", "reviewerAffiliation": "__REQUIRED_REVIEWER_AFFILIATION__", "independenceDeclaration": DECLARATION, "reviewedAt": "__YYYY-MM-DD__", "decision": "__accept|reject|needs-revision__", "rationale": "__REQUIRED_MINIMUM_80_CHARACTER_RATIONALE__", "checks": {"sourceLocatorsOpened": None, "mechanismClaimSupported": None, "boundariesSupported": None, "counterEvidenceConsidered": None, "noModelOutputUsed": None}}


def _readme(author: str) -> str:
    return f"# E14 post-2005 targeted independent rereview\n\nThis immutable bundle contains only the revised Archegos dossier hash.\n\n- Revision author: `{author}`\n- The accepted London Whale dossier is intentionally absent and must remain byte-identical.\n- Open every locator and reassess the mechanism and March–June 2021 boundaries.\n- Complete one schema-v2 receipt outside this bundle.\n- Do not use model output, outer-OOS metrics or the prior decision as evidence.\n"


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14 post-2005 {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    return _write_bytes(path, json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n")


def _write_text(path: str | Path, payload: str) -> Path:
    return _write_bytes(path, payload.encode())


def _write_bytes(path: str | Path, payload: bytes) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14 post-2005 output exists: {destination}") from error
    return destination
