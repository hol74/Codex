from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


def write_e14_review_handoff_bundle(
    contract_path: str | Path,
    review_queue_path: str | Path,
    adjudication_audit_path: str | Path,
    review_schema_path: str | Path,
    dossier_schema_path: str | Path,
    positive_dossier_dir: str | Path,
    hard_negative_dossier_dir: str | Path,
    bundle_dir: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 handoff contract")
    queue_file, queue_bytes, queue = _read_json(review_queue_path, "E14 review queue")
    audit_file, audit_bytes, audit = _read_json(adjudication_audit_path, "E14 adjudication audit")
    review_schema_file, review_schema_bytes, review_schema = _read_json(review_schema_path, "E14 review schema")
    dossier_schema_file, dossier_schema_bytes, dossier_schema = _read_json(dossier_schema_path, "E14 dossier schema")

    _validate_inputs(
        contract, queue, audit, review_schema, dossier_schema,
        queue_bytes, audit_bytes, review_schema_bytes, dossier_schema_bytes,
    )
    dossiers = _load_dossiers(queue, positive_dossier_dir, hard_negative_dossier_dir)

    root = Path(bundle_dir).resolve()
    output = Path(output_path).resolve()
    destinations = [root / "README.md"]
    for dossier, _, _ in dossiers:
        dossier_id = dossier["dossierId"]
        destinations.extend([
            root / "dossiers" / f"{dossier_id}.json",
            root / "worksheets" / f"{dossier_id}-review.md",
            root / "receipt-templates" / f"e14-review-{dossier_id.removeprefix('e14-dossier-')}-reviewer.json",
        ])
    if output.exists() or any(path.exists() for path in destinations):
        raise DatasetValidationError("Immutable E14 review handoff output already exists.")

    artifacts = []
    readme = _readme(contract, len(dossiers))
    readme_path = _write_new_text(root / "README.md", readme, "E14 handoff README")
    artifacts.append(_artifact(readme_path, readme_path.read_bytes(), "instructions"))

    locator_count = 0
    for dossier, raw, manifest in dossiers:
        dossier_id = dossier["dossierId"]
        copy_path = _write_new_bytes(root / "dossiers" / f"{dossier_id}.json", raw, "E14 dossier copy")
        artifacts.append(_artifact(copy_path, raw, "dossier-copy", dossier_id))

        worksheet = _worksheet(dossier, manifest["sha256"])
        locator_count += len(dossier["evidenceItems"]) + len(dossier["counterEvidence"])
        worksheet_path = _write_new_text(
            root / "worksheets" / f"{dossier_id}-review.md", worksheet, "E14 review worksheet"
        )
        artifacts.append(_artifact(worksheet_path, worksheet_path.read_bytes(), "worksheet", dossier_id))

        template = _receipt_template(dossier, manifest["sha256"])
        template_path = _write_new_json(
            root / "receipt-templates" / f"e14-review-{dossier_id.removeprefix('e14-dossier-')}-reviewer.json",
            template,
            "E14 receipt template",
        )
        artifacts.append(_artifact(template_path, template_path.read_bytes(), "non-ingestible-template", dossier_id))

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14ExternalReviewHandoffAudit",
        "status": "AWAITING_EXTERNAL_REVIEW",
        "inputs": {
            "handoffContract": _artifact(contract_file, contract_bytes, "input"),
            "reviewQueue": _artifact(queue_file, queue_bytes, "input"),
            "adjudicationAudit": _artifact(audit_file, audit_bytes, "input"),
            "reviewSchema": _artifact(review_schema_file, review_schema_bytes, "input"),
            "dossierSchema": _artifact(dossier_schema_file, dossier_schema_bytes, "input"),
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "reviewPerformedByBundleGenerator": False,
            "receiptTemplatesInIngestDirectory": False,
        },
        "inventory": {
            "dossierCount": len(dossiers),
            "worksheetCount": len(dossiers),
            "receiptTemplateCount": len(dossiers),
            "dossierCopyCount": len(dossiers),
            "evidenceLocatorOccurrenceCount": locator_count,
            "independentReviewReceiptCount": 0,
        },
        "bundleArtifacts": sorted(artifacts, key=lambda item: item["relativePath"]),
        "checks": {
            "allQueueDossiersHashValidated": True,
            "allDossiersCopiedByteIdentically": True,
            "oneWorksheetPerDossier": True,
            "oneNonIngestibleTemplatePerDossier": True,
            "allEvidenceAndCounterevidenceIncluded": True,
            "completedReceiptDirectorySeparated": True,
            "selfReviewNotPerformed": True,
        },
        "decision": {
            "handoffReady": True,
            "independentReviewComplete": False,
            "labelFoundationGateAuthorized": False,
            "groundTruthMutationAuthorized": False,
            "nextAllowedAction": "External reviewer completes receipts, then E14.4b3 ingests and validates them",
        },
        "implementation": {
            "module": "regime_eval.e14_review_handoff",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output, payload, "E14 external review handoff audit")


def _validate_inputs(
    contract: Any,
    queue: Any,
    audit: Any,
    review_schema: Any,
    dossier_schema: Any,
    queue_bytes: bytes,
    audit_bytes: bytes,
    review_schema_bytes: bytes,
    dossier_schema_bytes: bytes,
) -> None:
    actual = {
        "reviewQueueSha256": hashlib.sha256(queue_bytes).hexdigest(),
        "adjudicationAuditSha256": hashlib.sha256(audit_bytes).hexdigest(),
        "reviewSchemaSha256": hashlib.sha256(review_schema_bytes).hexdigest(),
        "dossierSchemaSha256": hashlib.sha256(dossier_schema_bytes).hexdigest(),
    }
    rules = contract.get("bundleRules", {}) if isinstance(contract, dict) else {}
    if (
        contract.get("contractId") != "e14-review-handoff-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("readinessDecision") != "READY_TO_BUILD_EXTERNAL_REVIEW_BUNDLE"
        or not all(rules.values())
        or queue.get("artifactType") != "E14IndependentReviewQueue"
        or queue.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or len(queue.get("dossiers", [])) != 12
        or any(item.get("reviewStatus") != "awaiting-independent-review" for item in queue["dossiers"])
        or audit.get("artifactType") != "E14AdjudicationReadinessAudit"
        or audit.get("status") != "INDEPENDENT_REVIEW_REQUIRED"
        or audit.get("inventory", {}).get("independentReviewReceiptCount") != 0
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v1.json"
        or dossier_schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
    ):
        raise DatasetValidationError("E14 review handoff inputs or contract are invalid.")


def _load_dossiers(
    queue: dict[str, Any], positive_dir: str | Path, hard_negative_dir: str | Path
) -> list[tuple[dict[str, Any], bytes, dict[str, Any]]]:
    roots = [Path(positive_dir).resolve(), Path(hard_negative_dir).resolve()]
    result = []
    for manifest in queue["dossiers"]:
        matches = [root / manifest["fileName"] for root in roots if (root / manifest["fileName"]).exists()]
        if len(matches) != 1:
            raise DatasetValidationError("E14 review handoff dossier is missing or duplicated.")
        try:
            raw = matches[0].read_bytes()
            dossier = json.loads(raw)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise DatasetValidationError("Cannot read an E14 review handoff dossier.") from exc
        if (
            hashlib.sha256(raw).hexdigest() != manifest.get("sha256")
            or len(raw) != manifest.get("sizeBytes")
            or dossier.get("dossierId") != manifest.get("dossierId")
            or dossier.get("adjudicationStatus") != "reviewed"
            or not dossier.get("evidenceItems")
            or not dossier.get("counterEvidence")
        ):
            raise DatasetValidationError("E14 review handoff dossier hash or content is invalid.")
        result.append((dossier, raw, manifest))
    return result


def _readme(contract: dict[str, Any], dossier_count: int) -> str:
    convention = contract["receiptOutputConvention"]
    return f"""# E14 independent review handoff

This bundle contains {dossier_count} immutable dossiers awaiting a genuinely independent review.

## Required workflow

1. Confirm that you did not author the dossier or its evidence pack.
2. Open every evidence and counterevidence locator in the worksheet.
3. Assess the named mechanism and the proposed monthly boundaries independently.
4. Copy the matching file from `receipt-templates/` outside this bundle.
5. Replace every `__REQUIRED...__` or `null` value and choose `accept`, `reject` or `needs-revision`.
6. Save the completed receipt in `{convention['directory']}` using `{convention['fileName']}`.
7. Do not edit dossier copies, queue artifacts or templates in place.

Templates are intentionally invalid review receipts until completed. Model outputs and outer-OOS outcomes must not be consulted.
"""


def _worksheet(dossier: dict[str, Any], sha256: str) -> str:
    lines = [
        f"# Review worksheet: {dossier['dossierId']}", "",
        f"- Dossier SHA-256: `{sha256}`",
        f"- Hypothesis: `{dossier['hypothesisId']}`",
        f"- Mechanism: `{dossier['mechanism']}`",
        f"- Proposed state: `{dossier['proposedState']}`",
        f"- Boundary: `{dossier['firstMonth']}` to `{dossier['lastMonth']}`", "",
        "## Boundary rationale", "", dossier["boundaryRationale"], "",
        "## Evidence to open", "",
    ]
    for index, item in enumerate(dossier["evidenceItems"], 1):
        lines.extend([
            f"### Evidence {index}: {item['role']}", "",
            f"- Provider: {item['provider']}",
            f"- Independence group: `{item['independenceGroup']}`",
            f"- Published: `{item['publishedAt']}`",
            f"- Locator: {item['locator']}",
            f"- Assertion digest: `{item['contentSha256']}`", "",
            item["summary"], "",
        ])
    lines.extend(["## Counterevidence to open", ""])
    for index, item in enumerate(dossier["counterEvidence"], 1):
        lines.extend([
            f"### Counterevidence {index}", "",
            f"- Provider: {item['provider']}",
            f"- Locator: {item['locator']}",
            f"- Assertion digest: `{item['contentSha256']}`", "",
            item["summary"], "",
        ])
    lines.extend([
        "## Reviewer decision checklist", "",
        "- [ ] I opened every locator above.",
        "- [ ] I am independent from the dossier author.",
        "- [ ] I assessed the mechanism claim without model outputs.",
        "- [ ] I assessed both monthly boundaries.",
        "- [ ] I considered the counterevidence.",
        "- [ ] I copied and completed the corresponding receipt template outside this bundle.", "",
    ])
    return "\n".join(lines)


def _receipt_template(dossier: dict[str, Any], sha256: str) -> dict[str, Any]:
    slug = dossier["dossierId"].removeprefix("e14-dossier-")
    return {
        "schemaVersion": 1,
        "reviewId": f"e14-review-{slug}-reviewer",
        "dossierId": dossier["dossierId"],
        "dossierSha256": sha256,
        "reviewerId": "__REQUIRED_INDEPENDENT_REVIEWER_ID__",
        "reviewerAffiliation": "__REQUIRED_REVIEWER_AFFILIATION__",
        "independenceDeclaration": "I did not author the dossier or its evidence pack and reviewed the cited evidence independently.",
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


def _artifact(
    path: Path, raw: bytes, role: str, dossier_id: str | None = None
) -> dict[str, Any]:
    result = {
        "relativePath": path.name if role == "input" else "/".join(path.parts[-2:]),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "sizeBytes": len(raw),
        "role": role,
    }
    if dossier_id is not None:
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
