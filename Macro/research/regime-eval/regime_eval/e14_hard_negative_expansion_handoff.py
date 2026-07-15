from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "EXPANSION_AWAITING_EXTERNAL_REVIEW"
ACCEPTED_STATUSES = {
    "accept-by-independent-receipt",
    "accept-by-targeted-independent-receipt",
}


def write_e14_hard_negative_expansion_handoff(
    contract_path: str | Path,
    review_queue_path: str | Path,
    curation_audit_path: str | Path,
    expansion_contract_path: str | Path,
    review_schema_path: str | Path,
    dossier_schema_path: str | Path,
    expansion_dossier_dir: str | Path,
    bundle_dir: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14.4f handoff contract")
    queue_file, queue_bytes, queue = _read_json(review_queue_path, "E14.4e review queue v6")
    audit_file, audit_bytes, audit = _read_json(curation_audit_path, "E14.4e curation audit")
    expansion_file, expansion_bytes, expansion_contract = _read_json(
        expansion_contract_path, "E14.4e expansion contract"
    )
    review_file, review_bytes, review_schema = _read_json(
        review_schema_path, "E14 independent review schema v2"
    )
    dossier_file, dossier_bytes, dossier_schema = _read_json(
        dossier_schema_path, "E14 dossier schema"
    )
    _validate_inputs(
        contract,
        queue,
        audit,
        expansion_contract,
        review_schema,
        dossier_schema,
        queue_bytes,
        audit_bytes,
        expansion_bytes,
        review_bytes,
        dossier_bytes,
    )
    dossiers = _load_expansion_dossiers(queue, expansion_dossier_dir)

    root = Path(bundle_dir).resolve()
    output = Path(output_path).resolve()
    if root.exists() or output.exists():
        raise DatasetValidationError("Immutable E14.4f expansion handoff output already exists.")

    artifacts: list[dict[str, Any]] = []
    readme = _readme(contract, len(dossiers))
    readme_path = _write_new_text(root / "README.md", readme, "E14.4f handoff README")
    artifacts.append(_bundle_artifact(root, readme_path, readme_path.read_bytes(), "instructions"))

    locator_count = 0
    dossier_hashes: dict[str, str] = {}
    for dossier, raw, manifest in dossiers:
        dossier_id = dossier["dossierId"]
        dossier_hashes[dossier_id] = manifest["sha256"]
        copy_path = _write_new_bytes(
            root / "dossiers" / manifest["fileName"], raw, "E14.4f dossier copy"
        )
        artifacts.append(_bundle_artifact(root, copy_path, raw, "dossier-copy", dossier_id))

        worksheet = _worksheet(dossier, manifest["sha256"])
        locator_count += len(dossier["evidenceItems"]) + len(dossier["counterEvidence"])
        worksheet_path = _write_new_text(
            root / "worksheets" / f"{dossier_id}-review.md",
            worksheet,
            "E14.4f review worksheet",
        )
        artifacts.append(
            _bundle_artifact(root, worksheet_path, worksheet_path.read_bytes(), "worksheet", dossier_id)
        )

        template = _receipt_template(dossier, manifest["sha256"])
        template_path = _write_new_json(
            root
            / "receipt-templates"
            / f"e14-review-{dossier_id.removeprefix('e14-dossier-')}-reviewer.json",
            template,
            "E14.4f non-ingestible receipt template",
        )
        artifacts.append(
            _bundle_artifact(
                root,
                template_path,
                template_path.read_bytes(),
                "non-ingestible-template",
                dossier_id,
            )
        )

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14HardNegativeExpansionHandoffAudit",
        "status": STATUS,
        "inputs": {
            "handoffContract": _input_artifact(contract_file, contract_bytes),
            "reviewQueueV6": _input_artifact(queue_file, queue_bytes),
            "curationAudit": _input_artifact(audit_file, audit_bytes),
            "expansionContract": _input_artifact(expansion_file, expansion_bytes),
            "reviewSchemaV2": _input_artifact(review_file, review_bytes),
            "dossierSchema": _input_artifact(dossier_file, dossier_bytes),
        },
        "inventory": {
            "preservedAcceptedDossierCount": 12,
            "reopenedAcceptedDossierCount": 0,
            "expansionDossierCount": len(dossiers),
            "dossierCopyCount": len(dossiers),
            "worksheetCount": len(dossiers),
            "receiptTemplateCount": len(dossiers),
            "evidenceLocatorOccurrenceCount": locator_count,
            "independentReviewReceiptCount": 0,
        },
        "expansionDossierHashes": dict(sorted(dossier_hashes.items())),
        "bundleArtifacts": sorted(artifacts, key=lambda item: item["relativePath"]),
        "checks": {
            "queueAndCurationHashesValidated": True,
            "exactlyFourExpansionDossiersIncluded": len(dossiers) == 4,
            "priorAcceptedDossiersExcluded": True,
            "allExpansionDossierHashesValidated": True,
            "allDossiersCopiedByteIdentically": True,
            "oneWorksheetPerExpansionDossier": True,
            "oneNonIngestibleTemplatePerExpansionDossier": True,
            "allEvidenceAndCounterevidenceIncluded": True,
            "completedReceiptDirectorySeparated": True,
            "selfReviewNotPerformed": True,
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsAccepted": 0,
            "taxonomyMutated": False,
            "candidateGenerated": False,
            "promotionPerformed": False,
            "reviewPerformedByBundleGenerator": False,
            "receiptTemplatesInIngestDirectory": False,
        },
        "decision": {
            "handoffReady": True,
            "independentReviewComplete": False,
            "coverageAccepted": False,
            "taxonomyUpdateAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_hard_negative_expansion_handoff",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output, payload, "E14.4f expansion handoff audit")


def _validate_inputs(
    contract: Any,
    queue: Any,
    audit: Any,
    expansion_contract: Any,
    review_schema: Any,
    dossier_schema: Any,
    queue_bytes: bytes,
    audit_bytes: bytes,
    expansion_bytes: bytes,
    review_bytes: bytes,
    dossier_bytes: bytes,
) -> None:
    actual_hashes = {
        "reviewQueueV6Sha256": hashlib.sha256(queue_bytes).hexdigest(),
        "curationAuditSha256": hashlib.sha256(audit_bytes).hexdigest(),
        "expansionContractSha256": hashlib.sha256(expansion_bytes).hexdigest(),
        "reviewSchemaV2Sha256": hashlib.sha256(review_bytes).hexdigest(),
        "dossierSchemaSha256": hashlib.sha256(dossier_bytes).hexdigest(),
    }
    required_rules = {
        "onlyExpansionDossiersIncluded": True,
        "priorAcceptedDossiersNotReopened": True,
        "oneWorksheetPerDossier": True,
        "oneReceiptTemplatePerDossier": True,
        "includeAllEvidenceLocators": True,
        "includeCounterEvidence": True,
        "copyDossiersByteIdentically": True,
        "receiptTemplatesAreNonIngestible": True,
        "reviewerMustOpenSourceLocators": True,
        "reviewerMustNotUseModelOutputs": True,
        "completedReceiptsWrittenOutsideBundle": True,
        "selfAcceptanceForbidden": True,
    }
    required_authorization = {
        "handoffWriteAuthorized": True,
        "reviewByGeneratorAuthorized": False,
        "receiptIngestionAuthorized": False,
        "taxonomyMutationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    required_state = {
        "queueStatus": "EXPANSION_AWAITING_INDEPENDENT_REVIEW",
        "curationStatus": "INDEPENDENT_REVIEW_REQUIRED",
        "preservedAcceptedDossierCount": 12,
        "newDossierCount": 4,
        "newIndependentReviewReceiptCount": 0,
    }
    dossiers = queue.get("dossiers", []) if isinstance(queue, dict) else []
    prior = dossiers[:12]
    expansion = dossiers[12:]
    expansion_ids = sorted(queue.get("expansionDossierIds", [])) if isinstance(queue, dict) else []
    if (
        not isinstance(contract, dict)
        or contract.get("contractId") != "e14-hard-negative-expansion-handoff-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("requiredInputState") != required_state
        or contract.get("bundleRules") != required_rules
        or contract.get("authorizationPolicy") != required_authorization
        or contract.get("expectedStatus") != STATUS
        or queue.get("artifactType") != "E14HardNegativeExpansionReviewQueue"
        or queue.get("status") != required_state["queueStatus"]
        or queue.get("preservedAcceptedDossierCount") != 12
        or queue.get("newDossierCount") != 4
        or len(dossiers) != 16
        or len(prior) != 12
        or any(item.get("reviewStatus") not in ACCEPTED_STATUSES for item in prior)
        or len(expansion) != 4
        or any(item.get("reviewStatus") != "awaiting-expansion-independent-review" for item in expansion)
        or sorted(item.get("dossierId") for item in expansion) != expansion_ids
        or len(set(expansion_ids)) != 4
        or audit.get("artifactType") != "E14HardNegativeExpansionCurationAudit"
        or audit.get("status") != required_state["curationStatus"]
        or audit.get("inventory", {}).get("preservedAcceptedDossierCount") != 12
        or audit.get("inventory", {}).get("newReviewedDossierCount") != 4
        or audit.get("inventory", {}).get("newIndependentReviewReceiptCount") != 0
        or audit.get("decision", {}).get("independentReviewComplete") is not False
        or audit.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or expansion_contract.get("contractId") != "e14-hard-negative-expansion-contract-v1"
        or expansion_contract.get("authorizationPolicy", {}).get("candidateGenerationAuthorized") is not False
        or review_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or dossier_schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
    ):
        raise DatasetValidationError("E14.4f expansion handoff inputs or contract are invalid.")


def _load_expansion_dossiers(
    queue: dict[str, Any], dossier_dir: str | Path
) -> list[tuple[dict[str, Any], bytes, dict[str, Any]]]:
    root = Path(dossier_dir).resolve()
    expansion_ids = set(queue["expansionDossierIds"])
    manifests = [item for item in queue["dossiers"] if item["dossierId"] in expansion_ids]
    if len(manifests) != 4:
        raise DatasetValidationError("E14.4f must hand off exactly four expansion dossiers.")
    result = []
    for manifest in sorted(manifests, key=lambda item: item["dossierId"]):
        file_name = manifest.get("fileName")
        if not isinstance(file_name, str) or Path(file_name).name != file_name:
            raise DatasetValidationError("E14.4f dossier manifest contains an invalid file name.")
        source = root / file_name
        try:
            raw = source.read_bytes()
            dossier = json.loads(raw)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise DatasetValidationError("Cannot read an E14.4f expansion dossier.") from exc
        if (
            hashlib.sha256(raw).hexdigest() != manifest.get("sha256")
            or len(raw) != manifest.get("sizeBytes")
            or dossier.get("dossierId") != manifest.get("dossierId")
            or dossier.get("adjudicationStatus") != "reviewed"
            or dossier.get("proposedState") != "hard-negative"
            or len(dossier.get("evidenceItems", [])) < 2
            or not dossier.get("counterEvidence")
        ):
            raise DatasetValidationError("E14.4f expansion dossier hash or content is invalid.")
        result.append((dossier, raw, manifest))
    return result


def _readme(contract: dict[str, Any], dossier_count: int) -> str:
    convention = contract["receiptOutputConvention"]
    return f"""# E14.4f hard-negative expansion review handoff

This immutable bundle contains exactly {dossier_count} new hard-negative dossiers. The 12 previously accepted dossiers are deliberately excluded and must not be reopened.

## Required workflow

1. Confirm that you did not author any dossier or its evidence pack.
2. Open every evidence and counterevidence locator in the worksheet.
3. Assess only the named mechanism, proposed month and affirmative orderly-state claim.
4. Treat stress in another mechanism during the same month as valid counterevidence, not an automatic conflict.
5. Copy the matching template outside this bundle and complete every placeholder or null value.
6. Choose `accept`, `reject` or `needs-revision` under review schema v2.
7. Save the completed receipt in `{convention['directory']}` using `{convention['fileName']}`.
8. Do not edit dossier copies, worksheets, templates, queue artifacts or this bundle in place.

Templates are intentionally invalid receipts. Model outputs, outer-OOS outcomes and the potential coverage result must not influence the review.
"""


def _worksheet(dossier: dict[str, Any], sha256: str) -> str:
    lines = [
        f"# Expansion review worksheet: {dossier['dossierId']}",
        "",
        f"- Dossier SHA-256: `{sha256}`",
        f"- Independent event: `{dossier['hypothesisId']}`",
        f"- Mechanism under review: `{dossier['mechanism']}`",
        f"- Proposed state: `{dossier['proposedState']}`",
        f"- Boundary: `{dossier['firstMonth']}` to `{dossier['lastMonth']}`",
        "",
        "## Boundary rationale",
        "",
        dossier["boundaryRationale"],
        "",
        "## Evidence to open",
        "",
    ]
    for index, item in enumerate(dossier["evidenceItems"], 1):
        lines.extend(
            [
                f"### Evidence {index}: {item['role']}",
                "",
                f"- Provider: {item['provider']}",
                f"- Independence group: `{item['independenceGroup']}`",
                f"- Published: `{item['publishedAt']}`",
                f"- Locator: {item['locator']}",
                f"- Assertion digest: `{item['contentSha256']}`",
                "",
                item["summary"],
                "",
            ]
        )
    lines.extend(["## Counterevidence to open", ""])
    for index, item in enumerate(dossier["counterEvidence"], 1):
        lines.extend(
            [
                f"### Counterevidence {index}",
                "",
                f"- Provider: {item['provider']}",
                f"- Locator: {item['locator']}",
                f"- Assertion digest: `{item['contentSha256']}`",
                "",
                item["summary"],
                "",
            ]
        )
    lines.extend(
        [
            "## Reviewer decision checklist",
            "",
            "- [ ] I opened every locator above.",
            "- [ ] I am independent from the dossier and pack author.",
            "- [ ] I assessed only the named mechanism and month.",
            "- [ ] I verified affirmative evidence of the proposed orderly state.",
            "- [ ] I considered policy-assisted containment and the counterevidence.",
            "- [ ] I did not use model outputs or potential coverage as evidence.",
            "- [ ] I copied the receipt template outside this immutable bundle.",
            "",
        ]
    )
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
        "rationale": "__REQUIRED_MINIMUM_80_CHARACTER_RATIONALE__",
        "checks": {
            "sourceLocatorsOpened": None,
            "mechanismClaimSupported": None,
            "boundariesSupported": None,
            "counterEvidenceConsidered": True,
            "noModelOutputUsed": True,
        },
    }


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _input_artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {
        "fileName": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "sizeBytes": len(raw),
    }


def _bundle_artifact(
    root: Path,
    path: Path,
    raw: bytes,
    role: str,
    dossier_id: str | None = None,
) -> dict[str, Any]:
    result = {
        "relativePath": path.relative_to(root).as_posix(),
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
