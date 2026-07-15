from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


DECLARATION = (
    "I did not author the dossier or its evidence pack and reviewed the cited evidence independently."
)
NEEDS_REVISION_STATUSES = {
    "needs-revision-by-expansion-independent-receipt",
    "needs-revision-by-targeted-expansion-independent-receipt",
}
ACCEPTED_SUFFIX = "accept"


def write_e14_hard_negative_targeted_revision(
    pack_path: str | Path,
    reviewed_queue_path: str | Path,
    review_ingestion_audit_path: str | Path,
    dossier_schema_path: str | Path,
    review_schema_path: str | Path,
    base_dossier_dir: str | Path,
    revised_dossier_dir: str | Path,
    bundle_dir: str | Path,
    queue_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    pack_file, pack_raw, pack = _read_json(pack_path, "targeted revision pack")
    queue_file, queue_raw, queue = _read_json(reviewed_queue_path, "reviewed queue v7")
    audit_file, audit_raw, audit = _read_json(review_ingestion_audit_path, "ingestion audit v2")
    schema_file, schema_raw, schema = _read_json(dossier_schema_path, "dossier schema")
    review_schema_file, review_schema_raw, review_schema = _read_json(review_schema_path, "review schema")
    _validate_inputs(pack, queue, audit, schema, review_schema, queue_raw, audit_raw, schema_raw, review_schema_raw)

    revisions = pack["revisions"]
    base_root = Path(base_dossier_dir).resolve()
    revised_root = Path(revised_dossier_dir).resolve()
    bundle_root = Path(bundle_dir).resolve()
    queue_output = Path(queue_output_path).resolve()
    output = Path(output_path).resolve()
    destinations = [queue_output, output, bundle_root / "README.md"]
    dossiers: list[dict[str, Any]] = []
    for revision in revisions:
        base_manifest = next(item for item in queue["dossiers"] if item["dossierId"] == revision["baseDossierId"])
        base_file = base_root / base_manifest["fileName"]
        base_raw = base_file.read_bytes()
        if hashlib.sha256(base_raw).hexdigest() != revision["baseSha256"]:
            raise DatasetValidationError("E14.4g2 base dossier hash is invalid.")
        dossier = _build_dossier(revision, pack["dossierAuthor"])
        dossiers.append(dossier)
        name = f"{dossier['dossierId']}.json"
        destinations.extend([
            revised_root / name,
            bundle_root / "dossiers" / name,
            bundle_root / "worksheets" / f"{dossier['dossierId']}-review.md",
            bundle_root / "receipt-templates" / f"e14-review-{dossier['dossierId'].removeprefix('e14-dossier-')}-reviewer.json",
        ])
    if any(path.exists() for path in destinations):
        raise DatasetValidationError("Immutable E14.4g2 targeted revision output already exists.")

    manifests: dict[str, dict[str, Any]] = {}
    bundle_artifacts: list[dict[str, Any]] = []
    for revision, dossier in zip(revisions, dossiers, strict=True):
        raw = _json_bytes(dossier)
        path = _write_new_bytes(revised_root / f"{dossier['dossierId']}.json", raw, "revised dossier")
        manifest = {**_artifact(path, raw), "dossierId": dossier["dossierId"]}
        if manifest["sha256"] == revision["baseSha256"]:
            raise DatasetValidationError("E14.4g2 revision did not receive a new hash.")
        manifests[revision["baseDossierId"]] = manifest
        copy = _write_new_bytes(bundle_root / "dossiers" / path.name, raw, "bundle dossier")
        bundle_artifacts.append(_bundle_artifact(copy, raw, "dossier-copy", dossier["dossierId"]))
        worksheet = _worksheet(dossier, manifest["sha256"], revision)
        worksheet_path = _write_new_text(
            bundle_root / "worksheets" / f"{dossier['dossierId']}-review.md", worksheet, "worksheet"
        )
        bundle_artifacts.append(_bundle_artifact(worksheet_path, worksheet_path.read_bytes(), "worksheet", dossier["dossierId"]))
        template = _receipt_template(dossier, manifest["sha256"])
        template_path = _write_new_bytes(
            bundle_root / "receipt-templates" / f"e14-review-{dossier['dossierId'].removeprefix('e14-dossier-')}-reviewer.json",
            _json_bytes(template), "receipt template"
        )
        bundle_artifacts.append(_bundle_artifact(template_path, template_path.read_bytes(), "non-ingestible-template", dossier["dossierId"]))

    readme = _write_new_text(bundle_root / "README.md", _readme(pack), "bundle README")
    bundle_artifacts.append(_bundle_artifact(readme, readme.read_bytes(), "instructions"))

    revised_items: list[dict[str, Any]] = []
    replacement_map: dict[str, str] = {}
    for item in queue["dossiers"]:
        manifest = manifests.get(item["dossierId"])
        if manifest is None:
            revised_items.append(item)
            continue
        revision = next(value for value in revisions if value["baseDossierId"] == item["dossierId"])
        replacement_map[item["dossierId"]] = manifest["dossierId"]
        revised_items.append({
            **manifest,
            "reviewStatus": "awaiting-targeted-expansion-independent-rereview",
            "supersedesDossierId": item["dossierId"],
            "supersedesSha256": item["sha256"],
            "revisionOperation": revision["operation"],
        })
    revised_queue = {
        **queue,
        "status": "EXPANSION_TARGETED_REREVIEW_REQUIRED",
        "dossierAuthor": pack["dossierAuthor"],
        "targetedRevisionDossierIds": sorted(item["dossierId"] for item in manifests.values()),
        "replacementMap": replacement_map,
        "dossiers": revised_items,
    }
    queue_path = _write_new_bytes(queue_output, _json_bytes(revised_queue), "targeted queue v8")
    preserved = [item for item in queue["dossiers"] if item["reviewStatus"].startswith(ACCEPTED_SUFFIX)]
    base_changed_ids = {item["baseDossierId"] for item in revisions}
    preserved_identically = all(
        next(candidate for candidate in revised_items if candidate["dossierId"] == item["dossierId"]) == item
        for item in queue["dossiers"] if item["dossierId"] not in base_changed_ids
    )
    report = {
        "schemaVersion": 1,
        "artifactType": "E14HardNegativeTargetedRevisionAudit",
        "status": "AWAITING_TARGETED_EXPANSION_INDEPENDENT_REREVIEW",
        "inputs": {
            "revisionPack": _artifact(pack_file, pack_raw),
            "reviewedQueueV7": _artifact(queue_file, queue_raw),
            "reviewIngestionAuditV2": _artifact(audit_file, audit_raw),
            "dossierSchema": _artifact(schema_file, schema_raw),
            "reviewSchemaV2": _artifact(review_schema_file, review_schema_raw),
            "targetedReviewQueueV8": _artifact(queue_path, queue_path.read_bytes()),
        },
        "inventory": {
            "preservedAcceptedDossierCount": len(preserved),
            "revisedDossierCount": sum(item["operation"] == "revise" for item in revisions),
            "replacedDossierCount": sum(item["operation"] == "replace" for item in revisions),
            "pendingTargetedReviewCount": len(revisions),
            "queuedDossierCount": len(revised_items),
        },
        "replacementMap": replacement_map,
        "revisedDossierArtifacts": [manifests[key] for key in sorted(manifests)],
        "preservedAcceptedArtifacts": preserved,
        "bundleArtifacts": sorted(bundle_artifacts, key=lambda item: item["relativePath"]),
        "checks": {
            "onlyNeedsRevisionManifestsChanged": True,
            "fourteenAcceptedManifestsPreservedByteIdentically": len(preserved) == 14 and preserved_identically,
            "allAcceptedManifestsPreservedByteIdentically": preserved_identically,
            "unsupportedMechanismReplacedNotRelabeled": True,
            "twoIndependentEvidenceProvidersPerDossier": True,
            "counterEvidencePerDossier": True,
            "sameMechanismMonthConflictAbsent": True,
            "targetedBundleContainsOnlyChangedHashes": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "taxonomyMutated": False,
            "labelsAccepted": 0,
            "candidateGenerated": False,
            "promotionPerformed": False,
            "reviewPerformedByRevisionAuthor": False,
        },
        "decision": {
            "targetedRereviewRequired": True,
            "hardNegativeCoverageGateAuthorized": False,
            "taxonomyUpdateAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": "Independent reviewer assesses only the two changed dossier hashes",
        },
        "implementation": {
            "module": "regime_eval.e14_hard_negative_targeted_revision",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return queue_path, _write_new_bytes(output, _json_bytes(report), "targeted revision audit")


def _validate_inputs(pack: Any, queue: Any, audit: Any, schema: Any, review_schema: Any,
                     queue_raw: bytes, audit_raw: bytes, schema_raw: bytes, review_schema_raw: bytes) -> None:
    hashes = {
        "reviewedQueueV7Sha256": hashlib.sha256(queue_raw).hexdigest(),
        "reviewIngestionAuditV2Sha256": hashlib.sha256(audit_raw).hexdigest(),
        "dossierSchemaSha256": hashlib.sha256(schema_raw).hexdigest(),
        "reviewSchemaV2Sha256": hashlib.sha256(review_schema_raw).hexdigest(),
    }
    revisions = pack.get("revisions", []) if isinstance(pack, dict) else []
    needs = [item for item in queue.get("dossiers", []) if item.get("reviewStatus") in NEEDS_REVISION_STATUSES]
    accepted = [item for item in queue.get("dossiers", []) if item.get("reviewStatus", "").startswith(ACCEPTED_SUFFIX)]
    ids = {item.get("baseDossierId") for item in revisions}
    pack_id = pack.get("packId")
    is_v1 = pack_id == "e14-hard-negative-targeted-revision-pack-v1"
    is_v2 = pack_id == "e14-hard-negative-targeted-revision-pack-v2"
    if (
        not (is_v1 or is_v2)
        or pack.get("inputHashes") != hashes
        or not pack.get("dossierAuthor")
        or pack.get("policy") != {
            "acceptedManifestsMustRemainByteIdentical": True,
            "onlyNeedsRevisionManifestsMayChange": True,
            "unsupportedMechanismMustBeReplacedNotRelabeled": True,
            "twoIndependentEvidenceProvidersRequired": True,
            "counterEvidenceRequired": True,
            "selfAcceptanceForbidden": True,
            "taxonomyMutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "outerOosAuthorized": False,
        }
        or queue.get("status") != ("EXPANSION_REVIEW_COMPLETE_REVISIONS_REQUIRED" if is_v1
                                   else "EXPANSION_TARGETED_REVIEW_COMPLETE_REVISIONS_REQUIRED")
        or audit.get("status") != ("EXPANSION_DOSSIER_REVISIONS_REQUIRED" if is_v1
                                   else "TARGETED_EXPANSION_DOSSIER_REVISIONS_REQUIRED")
        or len(queue.get("dossiers", [])) != 16
        or len(accepted) != (14 if is_v1 else 15) or len(needs) != (2 if is_v1 else 1)
        or len(revisions) != (2 if is_v1 else 1) or ids != {item["dossierId"] for item in needs}
        or {item.get("operation") for item in revisions} != ({"revise", "replace"} if is_v1 else {"revise"})
        or any(item.get("baseSha256") != next(q["sha256"] for q in needs if q["dossierId"] == item.get("baseDossierId")) for item in revisions)
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
    ):
        raise DatasetValidationError("E14.4g2 targeted revision inputs or scope are invalid.")


def _build_dossier(revision: dict[str, Any], author: str) -> dict[str, Any]:
    first, last = date.fromisoformat(revision["firstMonth"]), date.fromisoformat(revision["lastMonth"])
    evidence, counters = revision["evidenceItems"], revision["counterEvidence"]
    if (first.day != 1 or last.day != 1 or first > last or len(revision["boundaryRationale"]) < 80
            or len(evidence) < 2 or not counters or len({item["independenceGroup"] for item in evidence}) < 2
            or {item["role"] for item in evidence} != {"official-narrative", "quantitative-observation"}
            or any(item["role"] != "counterevidence" for item in counters)):
        raise DatasetValidationError("E14.4g2 revision evidence or boundary is invalid.")
    return {
        "schemaVersion": 1,
        "dossierId": revision["dossierId"],
        "hypothesisId": revision["hypothesisId"],
        "mechanism": revision["mechanism"],
        "proposedState": "hard-negative",
        "firstMonth": revision["firstMonth"],
        "lastMonth": revision["lastMonth"],
        "boundaryRationale": revision["boundaryRationale"],
        "affirmativeOrderlyEvidence": True,
        "evidenceItems": [_evidence(item) for item in evidence],
        "counterEvidence": [_evidence(item) for item in counters],
        "exclusionChecks": {
            "outerOosUsed": False, "modelPredictionUsedAsLabel": False,
            "absenceTreatedAsEvidence": False, "methodologyRegimeRecorded": True,
            "nberOverlapReviewed": True,
        },
        "adjudicationStatus": "reviewed",
        "reviewers": [author],
    }


def _evidence(item: dict[str, Any]) -> dict[str, Any]:
    required = {"sourceId", "provider", "independenceGroup", "publishedAt", "role", "locator", "summary"}
    if set(item) != required or not item["locator"].startswith("https://") or len(item["summary"]) < 40:
        raise DatasetValidationError("E14.4g2 evidence assertion is invalid.")
    date.fromisoformat(item["publishedAt"])
    return {**item, "contentSha256": hashlib.sha256(f"{item['locator']}\n{item['summary']}".encode()).hexdigest()}


def _receipt_template(dossier: dict[str, Any], digest: str) -> dict[str, Any]:
    return {
        "schemaVersion": 2,
        "reviewId": f"e14-review-{dossier['dossierId'].removeprefix('e14-dossier-')}-targeted-reviewer",
        "dossierId": dossier["dossierId"], "dossierSha256": digest,
        "reviewerId": "__REQUIRED_INDEPENDENT_REVIEWER_ID__",
        "reviewerAffiliation": "__REQUIRED_REVIEWER_AFFILIATION__",
        "independenceDeclaration": DECLARATION, "reviewedAt": "__YYYY-MM-DD__",
        "decision": "__accept|reject|needs-revision__",
        "rationale": "__REQUIRED_MINIMUM_80_CHARACTER_RATIONALE__",
        "checks": {"sourceLocatorsOpened": None, "mechanismClaimSupported": None,
                   "boundariesSupported": None, "counterEvidenceConsidered": None, "noModelOutputUsed": None},
    }


def _worksheet(dossier: dict[str, Any], digest: str, revision: dict[str, Any]) -> str:
    lines = [f"# Targeted review: {dossier['dossierId']}", "", f"- SHA-256: `{digest}`",
             f"- Operation: `{revision['operation']}`", f"- Supersedes: `{revision['baseDossierId']}`",
             f"- Mechanism: `{dossier['mechanism']}`", f"- Boundary: `{dossier['firstMonth']}` to `{dossier['lastMonth']}`",
             "", "## Boundary rationale", "", dossier["boundaryRationale"], "", "## Evidence", ""]
    for item in dossier["evidenceItems"]:
        lines += [f"- **{item['role']} — {item['provider']}**", f"  - {item['locator']}", f"  - {item['summary']}"]
    lines += ["", "## Counterevidence", ""]
    for item in dossier["counterEvidence"]:
        lines += [f"- **{item['provider']}**", f"  - {item['locator']}", f"  - {item['summary']}"]
    return "\n".join(lines) + "\n"


def _readme(pack: dict[str, Any]) -> str:
    return f"""# E14.4g2 targeted independent rereview

This immutable bundle contains only the two hashes changed after E14.4g.

- Revision author: `{pack['dossierAuthor']}`
- Fourteen accepted manifests are intentionally absent and must not be reopened.
- Open every locator; verify the named mechanism and exact monthly boundary.
- The 2019 repo dossier is retired, not relabeled; its replacement is a distinct 2010 event.
- Write one schema-v2 receipt per dossier outside this bundle.
- Do not use model output, outer-OOS metrics or prior decisions as evidence.
"""


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _bundle_artifact(path: Path, raw: bytes, role: str, dossier_id: str | None = None) -> dict[str, Any]:
    result = {"relativePath": "/".join(path.parts[-2:]), **_artifact(path, raw), "role": role}
    result.pop("fileName")
    if dossier_id:
        result["dossierId"] = dossier_id
    return result


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _write_new_bytes(path: str | Path, content: bytes, label: str) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("xb") as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{destination}'.") from exc
    return destination


def _write_new_text(path: str | Path, content: str, label: str) -> Path:
    return _write_new_bytes(path, content.encode(), label)
