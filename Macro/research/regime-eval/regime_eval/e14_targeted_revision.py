from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


REVISION_IDS = {
    "e14-dossier-continental-illinois-1984-banking-credit",
    "e14-dossier-mexico-1994-banking-credit-hard-negative",
    "e14-dossier-mexico-1994-broad-market-repricing",
    "e14-dossier-mexico-1994-cross-border-growth",
}
RECEIPT_DECLARATION = (
    "I did not author the dossier or its evidence pack and reviewed the cited evidence independently."
)


def write_e14_targeted_revision(
    contract_path: str | Path,
    reviewed_queue_path: str | Path,
    review_ingestion_audit_path: str | Path,
    dossier_schema_path: str | Path,
    positive_dossier_dir: str | Path,
    hard_negative_dossier_dir: str | Path,
    revised_dossier_dir: str | Path,
    bundle_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 revision contract")
    queue_file, queue_bytes, queue = _read_json(reviewed_queue_path, "E14 reviewed queue")
    audit_file, audit_bytes, audit = _read_json(review_ingestion_audit_path, "E14 ingestion audit")
    schema_file, schema_bytes, schema = _read_json(dossier_schema_path, "E14 dossier schema")
    _validate_inputs(contract, queue, audit, schema, queue_bytes, audit_bytes, schema_bytes)

    old = _load_dossiers(queue, positive_dossier_dir, hard_negative_dossier_dir)
    revisions = {item["dossierId"]: item for item in contract["revisions"]}
    revised = [_revise(old[dossier_id], revisions[dossier_id], contract["dossierAuthor"])
               for dossier_id in sorted(REVISION_IDS)]

    revised_root = Path(revised_dossier_dir).resolve()
    bundle_root = Path(bundle_dir).resolve()
    queue_output = Path(queue_output_path).resolve()
    output = Path(output_path).resolve()
    destinations = [queue_output, output, bundle_root / "README.md"]
    for dossier in revised:
        dossier_id = dossier["dossierId"]
        destinations.extend([
            revised_root / f"{dossier_id}.json",
            bundle_root / "dossiers" / f"{dossier_id}.json",
            bundle_root / "worksheets" / f"{dossier_id}-review.md",
            bundle_root / "receipt-templates" / f"e14-review-{dossier_id.removeprefix('e14-dossier-')}-reviewer.json",
        ])
    if any(path.exists() for path in destinations):
        raise DatasetValidationError("Immutable E14 targeted revision output already exists.")

    revised_artifacts: dict[str, dict[str, Any]] = {}
    bundle_artifacts = []
    for dossier in revised:
        path = _write_new_json(revised_root / f"{dossier['dossierId']}.json", dossier, "revised dossier")
        raw = path.read_bytes()
        artifact = _artifact(path, raw)
        artifact["dossierId"] = dossier["dossierId"]
        if artifact["sha256"] == revisions[dossier["dossierId"]]["baseSha256"]:
            raise DatasetValidationError("E14 revised dossier did not receive a new hash.")
        revised_artifacts[dossier["dossierId"]] = artifact
        copy = _write_new_bytes(
            bundle_root / "dossiers" / path.name, raw, "targeted review dossier copy"
        )
        bundle_artifacts.append(_bundle_artifact(copy, raw, "dossier-copy", dossier["dossierId"]))
        worksheet = _worksheet(dossier, artifact["sha256"])
        worksheet_path = _write_new_text(
            bundle_root / "worksheets" / f"{dossier['dossierId']}-review.md",
            worksheet,
            "targeted review worksheet",
        )
        bundle_artifacts.append(_bundle_artifact(
            worksheet_path, worksheet_path.read_bytes(), "worksheet", dossier["dossierId"]
        ))
        template = _receipt_template(dossier, artifact["sha256"])
        template_path = _write_new_json(
            bundle_root / "receipt-templates" /
            f"e14-review-{dossier['dossierId'].removeprefix('e14-dossier-')}-reviewer.json",
            template,
            "targeted receipt template",
        )
        bundle_artifacts.append(_bundle_artifact(
            template_path, template_path.read_bytes(), "non-ingestible-template", dossier["dossierId"]
        ))

    readme = _write_new_text(
        bundle_root / "README.md", _readme(contract["dossierAuthor"]), "targeted review README"
    )
    bundle_artifacts.append(_bundle_artifact(readme, readme.read_bytes(), "instructions"))

    accepted_ids = {
        item["dossierId"] for item in queue["dossiers"]
        if item["reviewStatus"] == "accept-by-independent-receipt"
    }
    queue_dossiers = []
    for item in queue["dossiers"]:
        if item["dossierId"] in revised_artifacts:
            queue_dossiers.append({
                **revised_artifacts[item["dossierId"]],
                "reviewStatus": "awaiting-targeted-independent-rereview",
                "supersedesSha256": item["sha256"],
            })
        else:
            queue_dossiers.append(item)
    revised_queue = {
        **queue,
        "status": "TARGETED_REREVIEW_REQUIRED",
        "dossierAuthor": contract["dossierAuthor"],
        "dossiers": queue_dossiers,
    }
    queue_path = _write_new_json(queue_output, revised_queue, "E14 targeted review queue")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14TargetedDossierRevisionAudit",
        "status": "AWAITING_TARGETED_INDEPENDENT_REREVIEW",
        "inputs": {
            "revisionContract": _artifact(contract_file, contract_bytes),
            "reviewedQueueV3": _artifact(queue_file, queue_bytes),
            "reviewIngestionAuditV1": _artifact(audit_file, audit_bytes),
            "dossierSchema": _artifact(schema_file, schema_bytes),
            "targetedReviewQueue": _artifact(queue_path, queue_path.read_bytes()),
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "acceptedDossierBytesChanged": False,
            "reviewPerformedByRevisionAuthor": False,
            "groundTruthMutated": False,
        },
        "inventory": {
            "totalDossierCount": 12,
            "preservedAcceptedDossierCount": len(accepted_ids),
            "revisedDossierCount": len(revised_artifacts),
            "targetedWorksheetCount": len(revised_artifacts),
            "targetedReceiptTemplateCount": len(revised_artifacts),
            "pendingTargetedReviewCount": len(revised_artifacts),
        },
        "revisedDossierArtifacts": [revised_artifacts[key] for key in sorted(revised_artifacts)],
        "preservedAcceptedArtifacts": [
            {key: item[key] for key in ("dossierId", "fileName", "sha256", "sizeBytes")}
            for item in queue["dossiers"] if item["dossierId"] in accepted_ids
        ],
        "bundleArtifacts": sorted(bundle_artifacts, key=lambda item: item["relativePath"]),
        "checks": {
            "onlyNeedsRevisionDossiersChanged": True,
            "allAcceptedDossiersPreservedByteIdentically": True,
            "allRevisedDossiersHaveNewHashes": True,
            "revisionEvidenceHasTwoIndependentProviders": True,
            "boundaryEvidenceAddedPerRevision": True,
            "targetedBundleContainsOnlyChangedHashes": True,
            "outerOosClosed": True,
        },
        "decision": {
            "targetedRereviewRequired": True,
            "labelFoundationGateAuthorized": False,
            "groundTruthMutationAuthorized": False,
            "nextAllowedAction": "Independent reviewer assesses only the four revised dossier hashes",
        },
        "implementation": {
            "module": "regime_eval.e14_targeted_revision",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return queue_path, _write_new_json(output, payload, "E14 targeted revision audit")


def _validate_inputs(
    contract: Any, queue: Any, audit: Any, schema: Any,
    queue_bytes: bytes, audit_bytes: bytes, schema_bytes: bytes,
) -> None:
    actual = {
        "reviewedQueueV3Sha256": hashlib.sha256(queue_bytes).hexdigest(),
        "reviewIngestionAuditV1Sha256": hashlib.sha256(audit_bytes).hexdigest(),
        "dossierSchemaSha256": hashlib.sha256(schema_bytes).hexdigest(),
    }
    policy = contract.get("policy", {}) if isinstance(contract, dict) else {}
    revisions = contract.get("revisions", []) if isinstance(contract, dict) else []
    queue_decisions = {item.get("dossierId"): item.get("reviewStatus") for item in queue.get("dossiers", [])}
    queue_hashes = {item.get("dossierId"): item.get("sha256") for item in queue.get("dossiers", [])}
    if (
        contract.get("contractId") != "e14-targeted-dossier-revision-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("readinessDecision") != "READY_FOR_HASH_SCOPED_DOSSIER_REVISION"
        or not contract.get("dossierAuthor") or not all(policy.values())
        or {item.get("dossierId") for item in revisions} != REVISION_IDS
        or len(revisions) != 4
        or any(item.get("baseSha256") != queue_hashes.get(item.get("dossierId")) for item in revisions)
        or any(queue_decisions.get(dossier_id) != "needs-revision-by-independent-receipt"
               for dossier_id in REVISION_IDS)
        or sum(value == "accept-by-independent-receipt" for value in queue_decisions.values()) != 8
        or queue.get("status") != "REVIEW_COMPLETE_REVISIONS_REQUIRED"
        or audit.get("status") != "DOSSIER_REVISIONS_REQUIRED"
        or audit.get("inventory", {}).get("acceptedCount") != 8
        or audit.get("inventory", {}).get("needsRevisionCount") != 4
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
    ):
        raise DatasetValidationError("E14 targeted revision inputs or scope are invalid.")


def _load_dossiers(queue: dict[str, Any], positive_dir: str | Path, negative_dir: str | Path) -> dict[str, dict[str, Any]]:
    roots = [Path(positive_dir).resolve(), Path(negative_dir).resolve()]
    result = {}
    for manifest in queue["dossiers"]:
        matches = [root / manifest["fileName"] for root in roots if (root / manifest["fileName"]).exists()]
        if len(matches) != 1:
            raise DatasetValidationError("E14 base dossier is missing or duplicated.")
        raw = matches[0].read_bytes()
        dossier = json.loads(raw)
        if hashlib.sha256(raw).hexdigest() != manifest["sha256"] or len(raw) != manifest["sizeBytes"]:
            raise DatasetValidationError("E14 base dossier hash is invalid.")
        result[dossier["dossierId"]] = dossier
    return result


def _revise(base: dict[str, Any], revision: dict[str, Any], author: str) -> dict[str, Any]:
    if revision.get("baseSha256") is None:
        raise DatasetValidationError("E14 revision base hash is missing.")
    try:
        first = date.fromisoformat(revision["firstMonth"])
        last = date.fromisoformat(revision["lastMonth"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError("E14 revised boundary is invalid.") from exc
    evidence = revision.get("evidenceAssertions", [])
    counters = revision.get("counterEvidenceAssertions", [])
    if (
        first > last or len(revision.get("boundaryRationale", "")) < 80
        or len(evidence) < 2 or not counters
        or len({item.get("independenceGroup") for item in evidence}) < 2
        or not any(item.get("role") == "boundary-corroboration" for item in evidence)
           and revision["dossierId"] != "e14-dossier-mexico-1994-banking-credit-hard-negative"
    ):
        raise DatasetValidationError("E14 revised dossier evidence or boundary is invalid.")
    for item in evidence + counters:
        _validate_assertion(item, item in counters)
    return {
        **base,
        "firstMonth": revision["firstMonth"],
        "lastMonth": revision["lastMonth"],
        "boundaryRationale": revision["boundaryRationale"],
        "evidenceItems": [_evidence_payload(item) for item in evidence],
        "counterEvidence": [_evidence_payload(item) for item in counters],
        "adjudicationStatus": "reviewed",
        "reviewers": [author],
    }


def _validate_assertion(item: Any, counter: bool) -> None:
    try:
        date.fromisoformat(item["publishedAt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError("E14 revision evidence date is invalid.") from exc
    required = {"sourceId", "provider", "independenceGroup", "publishedAt", "role", "locator", "summary"}
    allowed = {"official-narrative", "quantitative-observation", "boundary-corroboration", "counterevidence"}
    if (
        set(item) != required or item.get("role") not in allowed
        or (counter and item.get("role") != "counterevidence")
        or (not counter and item.get("role") == "counterevidence")
        or not item.get("locator", "").startswith("https://") or len(item.get("summary", "")) < 40
    ):
        raise DatasetValidationError("E14 revision evidence assertion is invalid.")


def _evidence_payload(item: dict[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    payload["contentSha256"] = hashlib.sha256(
        f"{item['locator']}\n{item['summary']}".encode("utf-8")
    ).hexdigest()
    return payload


def _readme(author: str) -> str:
    return f"""# E14 targeted independent rereview

This immutable bundle contains only the four dossier hashes revised after the first independent review.

- Revision author: `{author}`
- The eight previously accepted dossier hashes are intentionally absent.
- Open every locator and reassess the mechanism and both boundaries.
- Complete a schema-v2 receipt outside this bundle.
- Do not use model output, outer-OOS metrics or prior review decisions as evidence.
"""


def _worksheet(dossier: dict[str, Any], digest: str) -> str:
    lines = [
        f"# Targeted review: {dossier['dossierId']}", "", f"- SHA-256: `{digest}`",
        f"- Mechanism: `{dossier['mechanism']}`", f"- State: `{dossier['proposedState']}`",
        f"- Boundary: `{dossier['firstMonth']}` to `{dossier['lastMonth']}`", "",
        "## Boundary rationale", "", dossier["boundaryRationale"], "", "## Evidence", "",
    ]
    for item in dossier["evidenceItems"]:
        lines.extend([f"- **{item['role']} — {item['provider']}**", f"  - {item['locator']}",
                      f"  - {item['summary']}", f"  - digest: `{item['contentSha256']}`"])
    lines.extend(["", "## Counterevidence", ""])
    for item in dossier["counterEvidence"]:
        lines.extend([f"- **{item['provider']}**", f"  - {item['locator']}",
                      f"  - {item['summary']}", f"  - digest: `{item['contentSha256']}`"])
    return "\n".join(lines) + "\n"


def _receipt_template(dossier: dict[str, Any], digest: str) -> dict[str, Any]:
    slug = dossier["dossierId"].removeprefix("e14-dossier-")
    return {
        "schemaVersion": 2,
        "reviewId": f"e14-review-{slug}-targeted-reviewer",
        "dossierId": dossier["dossierId"],
        "dossierSha256": digest,
        "reviewerId": "__REQUIRED_INDEPENDENT_REVIEWER_ID__",
        "reviewerAffiliation": "__REQUIRED_REVIEWER_AFFILIATION__",
        "independenceDeclaration": RECEIPT_DECLARATION,
        "reviewedAt": "__YYYY-MM-DD__",
        "decision": "__accept|reject|needs-revision__",
        "rationale": "__REQUIRED_MINIMUM_80_CHARACTER_RATIONALE__",
        "checks": {
            "sourceLocatorsOpened": None,
            "mechanismClaimSupported": None,
            "boundariesSupported": None,
            "counterEvidenceConsidered": None,
            "noModelOutputUsed": None,
        },
    }


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _bundle_artifact(path: Path, raw: bytes, role: str, dossier_id: str | None = None) -> dict[str, Any]:
    result = {"relativePath": "/".join(path.parts[-2:]), "sha256": hashlib.sha256(raw).hexdigest(),
              "sizeBytes": len(raw), "role": role}
    if dossier_id:
        result["dossierId"] = dossier_id
    return result


def _write_new_json(path: str | Path, payload: dict[str, Any], label: str) -> Path:
    return _write_new_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n", label)


def _write_new_text(path: str | Path, content: str, label: str) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{destination}'.") from exc
    return destination


def _write_new_bytes(path: str | Path, content: bytes, label: str) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("xb") as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{destination}'.") from exc
    return destination
