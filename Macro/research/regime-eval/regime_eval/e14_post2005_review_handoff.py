from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "POST_2005_EXTERNAL_REVIEW_HANDOFF_READY"


def write_e14_post2005_review_handoff(
    contract_path: str | Path,
    proposal_path: str | Path,
    review_queue_path: str | Path,
    proposal_audit_path: str | Path,
    review_schema_path: str | Path,
    dossier_dir: str | Path,
    bundle_dir: str | Path,
    output_path: str | Path,
) -> Path:
    labels = ("handoff contract", "taxonomy proposal", "review queue", "proposal audit", "review schema")
    paths = (contract_path, proposal_path, review_queue_path, proposal_audit_path, review_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (_, _, contract), (proposal_file, proposal_raw, proposal), (queue_file, queue_raw, queue), \
        (_, _, proposal_audit), (schema_file, schema_raw, schema) = artifacts
    hashes = {
        "taxonomyProposalSha256": _sha(proposal_raw),
        "reviewQueueSha256": _sha(queue_raw),
        "proposalAuditSha256": _sha(artifacts[3][1]),
        "reviewSchemaV2Sha256": _sha(schema_raw),
    }
    _validate_inputs(contract, proposal, queue, proposal_audit, schema, hashes)
    dossiers = _load_dossiers(queue, dossier_dir)

    root = Path(bundle_dir).resolve()
    audit_path = Path(output_path).resolve()
    destinations = [
        root / "README.md",
        root / "proposal" / proposal_file.name,
        root / "queue" / queue_file.name,
    ]
    for dossier, _, manifest in dossiers:
        dossier_id = dossier["dossierId"]
        destinations.extend([
            root / "dossiers" / manifest["fileName"],
            root / "worksheets" / f"{dossier_id}-review.md",
            root / "receipt-templates" / f"e14-review-{dossier_id.removeprefix('e14-dossier-')}-reviewer.json",
        ])
    if audit_path.exists() or any(path.exists() for path in destinations):
        raise DatasetValidationError("Immutable E14.7g handoff output already exists.")

    bundle_artifacts = []
    _write_new(root / "proposal" / proposal_file.name, proposal_raw)
    bundle_artifacts.append(_bundle_artifact(root, root / "proposal" / proposal_file.name, proposal_raw, "taxonomy-proposal"))
    _write_new(root / "queue" / queue_file.name, queue_raw)
    bundle_artifacts.append(_bundle_artifact(root, root / "queue" / queue_file.name, queue_raw, "review-queue"))

    readme_raw = _readme(contract).encode("utf-8")
    _write_new(root / "README.md", readme_raw)
    bundle_artifacts.append(_bundle_artifact(root, root / "README.md", readme_raw, "instructions"))

    locator_count = 0
    for dossier, raw, manifest in dossiers:
        dossier_id = dossier["dossierId"]
        dossier_path = root / "dossiers" / manifest["fileName"]
        _write_new(dossier_path, raw)
        bundle_artifacts.append(_bundle_artifact(root, dossier_path, raw, "dossier-copy", dossier_id))
        locator_count += len(dossier["evidenceItems"]) + len(dossier["counterEvidence"])

        worksheet_raw = _worksheet(dossier, manifest["sha256"]).encode("utf-8")
        worksheet_path = root / "worksheets" / f"{dossier_id}-review.md"
        _write_new(worksheet_path, worksheet_raw)
        bundle_artifacts.append(_bundle_artifact(root, worksheet_path, worksheet_raw, "worksheet", dossier_id))

        template_raw = _json_bytes(_receipt_template(dossier, manifest["sha256"]))
        template_path = root / "receipt-templates" / f"e14-review-{dossier_id.removeprefix('e14-dossier-')}-reviewer.json"
        _write_new(template_path, template_raw)
        bundle_artifacts.append(_bundle_artifact(root, template_path, template_raw, "non-ingestible-template", dossier_id))

    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005ExternalReviewHandoffAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("handoffContract", "taxonomyProposal", "reviewQueue", "proposalAudit", "reviewSchemaV2"),
                artifacts,
            )
        },
        "inventory": {
            "dossierCount": len(dossiers),
            "worksheetCount": len(dossiers),
            "receiptTemplateCount": len(dossiers),
            "evidenceLocatorOccurrenceCount": locator_count,
            "independentReviewReceiptCount": 0,
        },
        "bundleArtifacts": sorted(bundle_artifacts, key=lambda item: item["relativePath"]),
        "checks": {
            "proposalCopiedByteIdentically": True,
            "queueCopiedByteIdentically": True,
            "allDossiersHashValidatedAndCopiedByteIdentically": True,
            "oneWorksheetPerDossier": True,
            "oneNonIngestibleTemplatePerDossier": True,
            "templatesSeparatedFromCompletedReceiptDirectory": True,
            "selfReviewNotPerformed": True,
        },
        "protocol": {
            "datasetRead": False,
            "loeoScoreRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsAccepted": 0,
            "reviewPerformedByBundleGenerator": False,
            "scopeActivated": False,
            "sourceAcquisitionAuthorized": False,
        },
        "decision": {
            "handoffReady": True,
            "independentReviewComplete": False,
            "receiptIngestionAuthorized": True,
            "scopeActivationAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_review_handoff",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _write_new(audit_path, _json_bytes(audit))
    return audit_path


def _validate_inputs(
    contract: dict[str, Any], proposal: dict[str, Any], queue: dict[str, Any],
    audit: dict[str, Any], schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    rules = {
        "proposalAndQueueCopiedByteIdentically": True,
        "dossiersCopiedByteIdentically": True,
        "oneWorksheetAndTemplatePerDossier": True,
        "templatesMustRemainNonIngestible": True,
        "completedReceiptsStoredOutsideBundle": True,
        "bundleGeneratorCannotReview": True,
    }
    if (
        contract.get("contractId") != "e14-post2005-review-handoff-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("bundleRules") != rules
        or contract.get("expectedStatus") != STATUS
        or proposal.get("status") != "POST_2005_TAXONOMY_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
        or proposal.get("activation", {}).get("active") is not False
        or queue.get("artifactType") != "E14Post2005IndependentReviewQueue"
        or queue.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or len(queue.get("dossiers", [])) != 2
        or queue.get("receipts") != []
        or audit.get("status") != "POST_2005_TAXONOMY_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
        or audit.get("decision", {}).get("post2005ScopeActivated") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
    ):
        raise DatasetValidationError("E14.7g handoff inputs or contract are invalid.")


def _load_dossiers(queue: dict[str, Any], directory: str | Path) -> list[tuple[dict[str, Any], bytes, dict[str, Any]]]:
    root = Path(directory).resolve()
    result = []
    for manifest in queue["dossiers"]:
        path = root / manifest["fileName"]
        try:
            raw = path.read_bytes()
            dossier = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DatasetValidationError("Cannot read an E14.7g dossier.") from error
        if (
            _sha(raw) != manifest.get("sha256")
            or len(raw) != manifest.get("sizeBytes")
            or dossier.get("dossierId") != manifest.get("dossierId")
            or dossier.get("adjudicationStatus") != "reviewed"
            or dossier.get("reviewers") != [queue["dossierAuthor"]]
            or not dossier.get("evidenceItems")
            or not dossier.get("counterEvidence")
        ):
            raise DatasetValidationError("E14.7g dossier hash or content is invalid.")
        result.append((dossier, raw, manifest))
    return sorted(result, key=lambda item: item[0]["dossierId"])


def _readme(contract: dict[str, Any]) -> str:
    directory = contract["receiptOutputConvention"]["directory"]
    pattern = contract["receiptOutputConvention"]["fileName"]
    return f"""# E14.7g post-2005 independent review handoff

This bundle contains two immutable banking-credit dossiers. It does not contain completed receipts and does not authorize the reviewer to edit proposal, queue or dossier files.

## Required workflow

1. Confirm that you did not author the proposal, evidence plan or dossiers.
2. Open every evidence and counterevidence locator in the matching worksheet.
3. Assess only the named banking-credit mechanism and frozen monthly boundary.
4. Copy the matching JSON from `receipt-templates/` outside this bundle.
5. Replace every placeholder and null; choose `accept`, `reject` or `needs-revision`.
6. Save the completed receipt in `{directory}` using `{pattern}`.
7. Do not consult model output, LOEO scores or outer OOS outcomes.

Templates are intentionally invalid until completed by a genuinely independent reviewer.
"""


def _worksheet(dossier: dict[str, Any], sha256: str) -> str:
    lines = [
        f"# Review worksheet: {dossier['dossierId']}", "",
        f"- Dossier SHA-256: `{sha256}`",
        f"- Mechanism: `{dossier['mechanism']}`",
        f"- Proposed state: `{dossier['proposedState']}`",
        f"- Boundary: `{dossier['firstMonth']}` to `{dossier['lastMonth']}`", "",
        "## Boundary rationale", "", dossier["boundaryRationale"], "", "## Evidence to open", "",
    ]
    for index, item in enumerate(dossier["evidenceItems"], 1):
        lines.extend([
            f"### Evidence {index}: {item['role']}", "",
            f"- Provider: {item['provider']}",
            f"- Independence group: `{item['independenceGroup']}`",
            f"- Locator: {item['locator']}",
            f"- Assertion digest: `{item['contentSha256']}`", "", item["summary"], "",
        ])
    lines.extend(["## Counterevidence to open", ""])
    for index, item in enumerate(dossier["counterEvidence"], 1):
        lines.extend([
            f"### Counterevidence {index}", "", f"- Provider: {item['provider']}",
            f"- Locator: {item['locator']}",
            f"- Assertion digest: `{item['contentSha256']}`", "", item["summary"], "",
        ])
    lines.extend([
        "## Checklist", "", "- [ ] I opened every locator.",
        "- [ ] I am independent from the dossier author.",
        "- [ ] I assessed the mechanism and both boundaries without model outputs.",
        "- [ ] I considered all counterevidence.", "",
    ])
    return "\n".join(lines)


def _receipt_template(dossier: dict[str, Any], sha256: str) -> dict[str, Any]:
    slug = dossier["dossierId"].removeprefix("e14-dossier-")
    return {
        "schemaVersion": 2,
        "reviewId": f"e14-review-{slug}-reviewer",
        "dossierId": dossier["dossierId"],
        "dossierSha256": sha256,
        "reviewerId": "__REQUIRED_INDEPENDENT_REVIEWER_ID__",
        "reviewerAffiliation": "__REQUIRED_REVIEWER_AFFILIATION__",
        "independenceDeclaration": "I did not author the dossier or its evidence pack and reviewed the cited evidence independently.",
        "reviewedAt": "__YYYY-MM-DD__",
        "decision": "__accept|reject|needs-revision__",
        "rationale": "__REQUIRED_RATIONALE_MINIMUM_80_CHARACTERS__",
        "checks": {
            "sourceLocatorsOpened": None,
            "mechanismClaimSupported": None,
            "boundariesSupported": None,
            "counterEvidenceConsidered": None,
            "noModelOutputUsed": None,
        },
    }


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        return file, raw, json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7g {label} is not valid UTF-8 JSON: {file}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _bundle_artifact(root: Path, path: Path, raw: bytes, role: str, dossier_id: str | None = None) -> dict[str, Any]:
    result = {"relativePath": path.relative_to(root).as_posix(), "role": role, "sha256": _sha(raw), "sizeBytes": len(raw)}
    if dossier_id is not None:
        result["dossierId"] = dossier_id
    return result


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
        raise DatasetValidationError(f"Immutable E14.7g handoff output already exists: {path}") from error
