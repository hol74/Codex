from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_policy_redesign_review_remediation import (
    AUTHORIZATION_POLICY as REMEDIATION_AUTHORIZATION_POLICY,
    COUNTER_IDS,
    DECLARATION,
    DOSSIER_IDS,
    FINDING_IDS,
    _validate_completed_receipt_contract,
)


STATUS = "POST_2005_POLICY_REDESIGN_EXTERNAL_REVIEW_HANDOFF_READY"
QUEUE_SHA = "b14f22a31abf197c1bf3227abfa35c9449003ccef81e52b1b25f583035bceb33"
REMEDIATION_AUDIT_SHA = "b4d70cfb47f90e942cda0c2effe317e57e3e3b287fb962c8dc52921c8054b8ab"
EVIDENCE_SHA = "6de9c7eb1cc16f8bcf8e44caf59cf9654583010ca271367e1f55950bcaabb6b3"
REVIEW_SCHEMA_SHA = "e0c6a1f4f2cf897552c4bf451849498e0785611c405890eac0fc8b7cc8c51a4a"
REMEDIATION_PLAN_SHA = "fb6dc44263d0e283cac14db802dff17a85ed3377d629bc3001efcbaa8e147e3c"
HANDOFF_PLAN_SHA = "69c580022cccdab897f6bb5dc46577881a76ad51ed87acfa98785331527eb989"
HANDOFF_SCHEMA_SHA = "d87b7ecf31ef7acdfc783bf30626595df93ba1c08672bc34082fc955d50b9eea"
BUNDLE_RULES = {
    "proposalCopiedByteIdentically": True,
    "queueV2CopiedByteIdentically": True,
    "dossiersCopiedByteIdentically": True,
    "evidenceContractCopiedByteIdentically": True,
    "dedicatedReviewSchemaCopiedByteIdentically": True,
    "remediationAuditCopiedByteIdentically": True,
    "oneWorksheetPerDossier": True,
    "oneNonIngestibleTemplatePerDossier": True,
    "templatesBindExactQueueEvidenceSchemaAndDossierHashes": True,
    "templatesEnumerateAllRequiredFindingsAndCounterEvidence": True,
    "completedReceiptsStoredOutsideBundle": True,
    "bundleGeneratorCannotReview": True,
}
AUTHORIZATION_POLICY = {
    "handoffBundlePublicationAuthorized": True,
    "independentReviewExecutionAuthorized": True,
    "reviewPerformedByBundleGenerator": False,
    "receiptIngestionAuthorized": False,
    "policyActivationAuthorized": False,
    "requestCatalogGenerationAuthorized": False,
    "sourceAcquisitionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
NEXT_ACTION = (
    "A genuinely independent reviewer copies each template outside the immutable "
    "bundle, opens every provider-primary locator, completes every finding and "
    "counterevidence assessment, and returns two authentic receipts; ingestion "
    "and policy activation remain separate gates"
)
RECEIPT_OUTPUT_CONVENTION = {
    "directory": "completed-policy-redesign-receipts-v1/",
    "fileName": "e14-policy-redesign-review-<dossier-slug>-<reviewer-id>.json",
}


def write_e14_post2005_policy_redesign_review_handoff(
    contract_path: str | Path,
    proposal_path: str | Path,
    review_queue_v2_path: str | Path,
    remediation_audit_path: str | Path,
    dossier_dir: str | Path,
    evidence_contract_path: str | Path,
    dedicated_review_schema_path: str | Path,
    remediation_plan_path: str | Path,
    handoff_plan_path: str | Path,
    handoff_audit_schema_path: str | Path,
    bundle_dir: str | Path,
    audit_output_path: str | Path,
) -> Path:
    labels = (
        "handoff contract", "policy-redesign proposal", "review queue v2",
        "review remediation audit", "evidence contract", "dedicated review schema",
        "review remediation plan", "handoff plan", "handoff audit schema",
    )
    paths = (
        contract_path, proposal_path, review_queue_v2_path, remediation_audit_path,
        evidence_contract_path, dedicated_review_schema_path, remediation_plan_path,
        handoff_plan_path, handoff_audit_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, proposal, queue, remediation_audit, evidence, review_schema, remediation_plan, handoff_plan, handoff_schema = (
        item[2] for item in artifacts
    )
    dossiers = _load_dossiers(queue, dossier_dir)
    dossier_by_id = {item[0]["dossierId"]: item for item in dossiers}
    hashes = {
        "proposalSha256": _sha(artifacts[1][1]),
        "reviewQueueV2Sha256": _sha(artifacts[2][1]),
        "reviewRemediationAuditSha256": _sha(artifacts[3][1]),
        "crossG5DossierSha256": _sha(dossier_by_id[DOSSIER_IDS[0]][1]) if DOSSIER_IDS[0] in dossier_by_id else "",
        "bankFdicDossierSha256": _sha(dossier_by_id[DOSSIER_IDS[1]][1]) if DOSSIER_IDS[1] in dossier_by_id else "",
        "evidenceContractSha256": _sha(artifacts[4][1]),
        "dedicatedReviewSchemaSha256": _sha(artifacts[5][1]),
        "reviewRemediationPlanSha256": _sha(artifacts[6][1]),
        "handoffPlanSha256": _sha(artifacts[7][1]),
        "handoffAuditSchemaSha256": _sha(artifacts[8][1]),
    }
    _validate_inputs(
        contract, proposal, queue, remediation_audit, evidence, review_schema,
        remediation_plan, handoff_plan, handoff_schema, dossiers, hashes, artifacts,
    )

    root = Path(bundle_dir).resolve()
    audit_output = Path(audit_output_path).resolve()
    staging = root.parent / f".{root.name}.staging"
    dossier_root = Path(dossier_dir).resolve()
    input_files = {item[0] for item in artifacts}
    if (
        audit_output in input_files
        or root in input_files
        or audit_output == root
        or audit_output.is_relative_to(root)
        or root == dossier_root
        or root.is_relative_to(dossier_root)
    ):
        raise DatasetValidationError("E14.7q output topology overlaps immutable inputs or bundle contents.")
    if root.exists() or staging.exists() or audit_output.exists():
        raise DatasetValidationError("Immutable E14.7q handoff output already exists.")

    evidence_by_id = {item["dossierId"]: item for item in evidence["reviewItems"]}
    contents: dict[str, tuple[bytes, str, str | None]] = {
        "proposal/" + artifacts[1][0].name: (artifacts[1][1], "policy-redesign-proposal", None),
        "queue/" + artifacts[2][0].name: (artifacts[2][1], "review-queue-v2", None),
        "provenance/" + artifacts[3][0].name: (artifacts[3][1], "review-remediation-audit", None),
        "evidence/" + artifacts[4][0].name: (artifacts[4][1], "evidence-contract", None),
        "schema/" + artifacts[5][0].name: (artifacts[5][1], "dedicated-review-schema", None),
    }
    for dossier, raw, manifest in dossiers:
        dossier_id = dossier["dossierId"]
        contents["dossiers/" + manifest["fileName"]] = (raw, "dossier-copy", dossier_id)
        worksheet = _worksheet(dossier, manifest, evidence_by_id[dossier_id], hashes)
        contents[f"worksheets/{dossier_id}-review.md"] = (worksheet.encode("utf-8"), "worksheet", dossier_id)
        template = _receipt_template(dossier_id, manifest["sha256"], evidence_by_id[dossier_id], hashes)
        template_raw = _json_bytes(template)
        contents[f"receipt-templates/{dossier_id}-review-template.json"] = (template_raw, "non-ingestible-template", dossier_id)
        _prove_template_contract(template, dossier_id, manifest["sha256"], hashes)
    readme = _readme(contract).encode("utf-8")
    contents["README.md"] = (readme, "instructions", None)
    if len(contents) != 12:
        raise DatasetValidationError("E14.7q bundle inventory is not exact.")

    bundle_artifacts = [
        _bundle_artifact(relative_path, raw, role, dossier_id)
        for relative_path, (raw, role, dossier_id) in contents.items()
    ]
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignReviewHandoffAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("handoffContract", "policyRedesignProposal", "reviewQueueV2", "reviewRemediationAudit", "evidenceContract", "dedicatedReviewSchema", "reviewRemediationPlan", "handoffPlan", "handoffAuditSchema"),
                artifacts,
            )
        },
        "inventory": {
            "bundleArtifactCount": len(bundle_artifacts),
            "dossierCount": 2,
            "worksheetCount": 2,
            "receiptTemplateCount": 2,
            "evidenceItemCount": 7,
            "counterEvidenceItemCount": 2,
            "requiredFindingCount": 8,
            "independentReviewReceiptCount": 0,
        },
        "bundleArtifacts": sorted(bundle_artifacts, key=lambda item: item["relativePath"]),
        "checks": {
            "allInputHashesExact": True,
            "allCrossBindingsExact": True,
            "proposalCopiedByteIdentically": True,
            "queueV2CopiedByteIdentically": True,
            "dossiersCopiedByteIdentically": True,
            "evidenceContractCopiedByteIdentically": True,
            "dedicatedReviewSchemaCopiedByteIdentically": True,
            "remediationAuditCopiedByteIdentically": True,
            "oneWorksheetPerDossier": True,
            "oneNonIngestibleTemplatePerDossier": True,
            "templatesBindExactQueueEvidenceSchemaAndDossierHashes": True,
            "templatesEnumerateAllRequiredFindingsAndCounterEvidence": True,
            "placeholderTemplatesFailDedicatedContract": True,
            "syntheticCompletionsPassDedicatedContract": True,
            "pathTraversalRejected": True,
            "selfReviewNotPerformed": True,
        },
        "protocol": {
            "bundlePublishedFromValidatedStaging": True,
            "reviewPerformedByBundleGenerator": False,
            "receiptsCreated": 0,
            "receiptContentIngested": False,
            "requestCatalogGenerated": False,
            "seriesObservationsDownloaded": False,
            "featuresTransformed": 0,
            "candidatesGenerated": 0,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "handoffReady": True,
            "independentReviewExecutionAuthorized": True,
            "reviewComplete": False,
            "receiptIngestionAuthorized": False,
            "policyActivationAuthorized": False,
            "requestCatalogGenerationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": NEXT_ACTION,
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_policy_redesign_review_handoff",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    audit_raw = _json_bytes(audit)
    _publish_bundle_atomically(staging, root, contents)
    try:
        _write_new(audit_output, audit_raw)
    except Exception:
        raise
    return audit_output


def _validate_inputs(
    contract: dict[str, Any], proposal: dict[str, Any], queue: dict[str, Any],
    remediation_audit: dict[str, Any], evidence: dict[str, Any], review_schema: dict[str, Any],
    remediation_plan: dict[str, Any], handoff_plan: dict[str, Any], handoff_schema: dict[str, Any],
    dossiers: list[tuple[dict[str, Any], bytes, dict[str, Any]]], hashes: dict[str, str],
    artifacts: list[tuple[Path, bytes, dict[str, Any]]],
) -> None:
    ids = [item[0]["dossierId"] for item in dossiers]
    dossier_manifests = [item[2] for item in dossiers]
    if (
        contract.get("contractId") != "e14-post2005-policy-redesign-review-handoff-contract-v1"
        or contract.get("inputHashes") != hashes
        or hashes.get("reviewQueueV2Sha256") != QUEUE_SHA
        or hashes.get("reviewRemediationAuditSha256") != REMEDIATION_AUDIT_SHA
        or hashes.get("evidenceContractSha256") != EVIDENCE_SHA
        or hashes.get("dedicatedReviewSchemaSha256") != REVIEW_SCHEMA_SHA
        or hashes.get("reviewRemediationPlanSha256") != REMEDIATION_PLAN_SHA
        or hashes.get("handoffPlanSha256") != HANDOFF_PLAN_SHA
        or hashes.get("handoffAuditSchemaSha256") != HANDOFF_SCHEMA_SHA
        or contract.get("expectedDossierIds") != DOSSIER_IDS
        or contract.get("expectedQueueId") != queue.get("queueId")
        or contract.get("expectedEvidenceContractId") != evidence.get("evidenceId")
        or contract.get("expectedReviewSchemaId") != review_schema.get("$id")
        or contract.get("bundleRules") != BUNDLE_RULES
        or contract.get("receiptOutputConvention") != RECEIPT_OUTPUT_CONVENTION
        or contract.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or contract.get("expectedBundleArtifactCount") != 12
        or contract.get("expectedStatus") != STATUS
        or contract.get("nextAllowedAction") != NEXT_ACTION
        or handoff_plan.get("bundleRules") != BUNDLE_RULES
        or handoff_plan.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or handoff_plan.get("expectedBundleArtifactCount") != 12
        or handoff_plan.get("expectedStatus") != STATUS
        or handoff_plan.get("nextAllowedAction") != NEXT_ACTION
        or proposal.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or queue.get("queueId") != "e14-post2005-policy-redesign-review-queue-v2"
        or queue.get("status") != "AWAITING_INDEPENDENT_REVIEW_HANDOFF"
        or queue.get("receipts") != []
        or queue.get("proposal") != _artifact(artifacts[1][0], artifacts[1][1])
        or queue.get("dossiers") != dossier_manifests
        or queue.get("evidenceContract") != _artifact(artifacts[4][0], artifacts[4][1])
        or queue.get("reviewSchema") != _artifact(artifacts[5][0], artifacts[5][1])
        or ids != DOSSIER_IDS or len(ids) != len(set(ids))
        or remediation_audit.get("status") != "POST_2005_POLICY_REDESIGN_REVIEW_CONTRACT_REMEDIATED_AWAITING_HANDOFF"
        or remediation_audit.get("outputs", {}).get("reviewQueueV2") != _artifact(artifacts[2][0], artifacts[2][1])
        or remediation_audit.get("decision", {}).get("independentReviewHandoffAuthorized") is not True
        or remediation_audit.get("decision", {}).get("receiptIngestionAuthorized") is not False
        or remediation_plan.get("authorizationPolicy") != REMEDIATION_AUTHORIZATION_POLICY
        or evidence.get("evidenceId") != "e14-post2005-policy-redesign-review-remediation-evidence-v1"
        or [item.get("dossierId") for item in evidence.get("reviewItems", [])] != DOSSIER_IDS
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-policy-redesign-independent-review-v1.json"
        or review_schema.get("properties", {}).get("dossierId", {}).get("enum") != DOSSIER_IDS
        or handoff_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-policy-redesign-review-handoff-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7q handoff inputs are invalid.")


def _worksheet(dossier: dict[str, Any], manifest: dict[str, Any], evidence: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        f"# Independent review worksheet: {dossier['dossierId']}", "",
        f"- Dossier SHA-256: `{manifest['sha256']}`",
        f"- Queue v2 SHA-256: `{QUEUE_SHA}`",
        f"- Evidence contract SHA-256: `{EVIDENCE_SHA}`",
        f"- Review schema SHA-256: `{REVIEW_SCHEMA_SHA}`", "",
        "## Required findings", "",
    ]
    for finding in evidence["requiredFindings"]:
        lines.extend([f"- [ ] `{finding['findingId']}`: {finding['statement']}"])
    lines.extend(["", "## Provider-primary evidence to open", ""])
    for item in evidence["evidenceItems"]:
        lines.extend([
            f"### {item['role']}", "", f"- Provider: {item['provider']}",
            f"- Locator: {item['locator']}",
            f"- Assertion digest (not a page-content digest): `{item['assertionSha256']}`",
            "", item["assertion"], "",
        ])
    lines.extend(["## Counterevidence to open and assess", ""])
    for item in evidence["counterEvidence"]:
        lines.extend([
            f"### {item['counterEvidenceId']}: {item['role']}", "",
            f"- Provider: {item['provider']}", f"- Locator: {item['locator']}",
            "", item["summary"], "",
        ])
    lines.extend([
        "## Reviewer checklist", "",
        "- [ ] I did not author the proposal, dossier, evidence contract, or review materials.",
        "- [ ] I opened every locator above, including repeated locators used for distinct roles.",
        "- [ ] I assessed every named finding and counterevidence item.",
        "- [ ] I used no model output, LOEO score, evaluation result, or outer-OOS information.",
        "- [ ] I copied the template outside this immutable bundle before editing it.", "",
    ])
    return "\n".join(lines)


def _receipt_template(dossier_id: str, dossier_sha: str, evidence: dict[str, Any], hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "reviewId": "__REQUIRED_POLICY_REDESIGN_REVIEW_ID__",
        "dossierId": dossier_id,
        "dossierSha256": dossier_sha,
        "queueId": "e14-post2005-policy-redesign-review-queue-v2",
        "queueSha256": QUEUE_SHA,
        "evidenceContractId": "e14-post2005-policy-redesign-review-remediation-evidence-v1",
        "evidenceContractSha256": EVIDENCE_SHA,
        "reviewSchemaId": "https://macro-regime.local/schemas/e14-policy-redesign-independent-review-v1.json",
        "reviewSchemaSha256": REVIEW_SCHEMA_SHA,
        "reviewerId": "__REQUIRED_INDEPENDENT_REVIEWER_ID__",
        "reviewerAffiliation": "__REQUIRED_REVIEWER_AFFILIATION__",
        "independenceDeclaration": DECLARATION,
        "reviewedAt": "__YYYY-MM-DD__",
        "decision": "__accept|reject|needs-revision__",
        "rationale": "__REQUIRED_RATIONALE_MINIMUM_100_CHARACTERS__",
        "findingAssessments": [
            {"findingId": item["findingId"], "supported": None, "rationale": "__REQUIRED_FINDING_RATIONALE_MINIMUM_20_CHARACTERS__"}
            for item in evidence["requiredFindings"]
        ],
        "counterEvidenceAssessments": [
            {"counterEvidenceId": item["counterEvidenceId"], "considered": None, "rationale": "__REQUIRED_COUNTEREVIDENCE_RATIONALE_MINIMUM_20_CHARACTERS__"}
            for item in evidence["counterEvidence"]
        ],
        "checks": {
            "providerPrimaryLocatorsOpened": None,
            "proposalSemanticsSupported": None,
            "methodologyOrAvailabilityBoundarySupported": None,
            "counterEvidenceConsidered": None,
            "noModelOutputUsed": None,
        },
    }


def _prove_template_contract(template: dict[str, Any], dossier_id: str, dossier_sha: str, hashes: dict[str, str]) -> None:
    validation_hashes = {
        "crossG5DossierSha256": hashes["crossG5DossierSha256"],
        "bankFdicDossierSha256": hashes["bankFdicDossierSha256"],
        "remediationEvidenceSha256": EVIDENCE_SHA,
        "dedicatedReviewSchemaSha256": REVIEW_SCHEMA_SHA,
    }
    try:
        _validate_completed_receipt_contract(template, dossier_id, QUEUE_SHA, validation_hashes)
    except DatasetValidationError:
        pass
    else:
        raise DatasetValidationError("E14.7q placeholder template unexpectedly passes the dedicated contract.")
    completed = json.loads(json.dumps(template))
    completed["reviewId"] = f"e14-policy-redesign-review-{dossier_id.removeprefix('e14-post2005-policy-redesign-dossier-')}-reviewer"
    completed["reviewerId"] = "independent-reviewer"
    completed["reviewerAffiliation"] = "independent-review-affiliation"
    completed["reviewedAt"] = "2026-07-16"
    completed["decision"] = "accept"
    completed["rationale"] = "Synthetic completion used only to prove that this non-ingestible template has a valid path under the dedicated contract; it is not an authentic receipt."
    for item in completed["findingAssessments"]:
        item["supported"] = True
        item["rationale"] = "The provider-primary evidence supports this required finding."
    for item in completed["counterEvidenceAssessments"]:
        item["considered"] = True
        item["rationale"] = "The named limitation was considered against the proposal semantics."
    for key in completed["checks"]:
        completed["checks"][key] = True
    _validate_completed_receipt_contract(completed, dossier_id, QUEUE_SHA, validation_hashes)


def _readme(contract: dict[str, Any]) -> str:
    convention = RECEIPT_OUTPUT_CONVENTION
    return f"""# E14.7q policy-redesign independent review handoff

This immutable bundle contains no completed receipt and records no review decision.

## Required workflow

1. Confirm that you did not author the proposal, dossiers, evidence contract, or review materials.
2. Read the byte-identical proposal, queue v2, dossier, evidence contract, and dedicated schema.
3. Open every locator in the matching worksheet, including a repeated locator when it supports a distinct evidence or counterevidence role.
4. Copy the matching JSON from `receipt-templates/` outside this bundle; never edit any bundle file in place.
5. Replace every placeholder and null, preserve every frozen ID and hash, and assess all named findings and counterevidence.
6. Save the authentic completed receipt in `{convention['directory']}` using `{convention['fileName']}`.
7. Do not consult model output, LOEO scores, evaluation results, or outer-OOS outcomes.

Templates are intentionally invalid until completed by a genuinely independent reviewer. Receipt ingestion and policy activation require later, separate gates.
"""


def _load_dossiers(queue: dict[str, Any], directory: str | Path) -> list[tuple[dict[str, Any], bytes, dict[str, Any]]]:
    root = Path(directory).resolve()
    result = []
    for manifest in queue.get("dossiers", []):
        name = manifest.get("fileName", "")
        if not _safe_basename(name):
            raise DatasetValidationError("E14.7q dossier path is invalid.")
        file = (root / name).resolve()
        if not file.is_relative_to(root):
            raise DatasetValidationError("E14.7q dossier path escapes its source directory.")
        source, raw, dossier = _read(file, "policy-redesign dossier")
        if source.parent != root or _sha(raw) != manifest.get("sha256") or len(raw) != manifest.get("sizeBytes") or dossier.get("dossierId") != manifest.get("dossierId"):
            raise DatasetValidationError("E14.7q dossier hash or content is invalid.")
        result.append((dossier, raw, manifest))
    return result


def _publish_bundle_atomically(staging: Path, root: Path, contents: dict[str, tuple[bytes, str, str | None]]) -> None:
    staging.parent.mkdir(parents=True, exist_ok=True)
    try:
        staging.mkdir()
        for relative_path, (raw, _, _) in contents.items():
            relative = Path(relative_path)
            destination = (staging / relative).resolve()
            if relative.is_absolute() or ".." in relative.parts or not destination.is_relative_to(staging):
                raise DatasetValidationError("E14.7q bundle destination path is invalid.")
            _write_new(destination, raw)
        try:
            staging.rename(root)
        except PermissionError:
            root.mkdir()
            try:
                for relative_path, (raw, _, _) in contents.items():
                    destination = (root / Path(relative_path)).resolve()
                    if not destination.is_relative_to(root):
                        raise DatasetValidationError("E14.7q fallback destination path is invalid.")
                    _write_new(destination, raw)
            except Exception:
                if root.exists() and root.parent == staging.parent:
                    shutil.rmtree(root)
                raise
            shutil.rmtree(staging)
    except Exception:
        if staging.exists() and staging.parent == root.parent and staging.name == f".{root.name}.staging":
            shutil.rmtree(staging)
        raise


def _safe_basename(name: Any) -> bool:
    return isinstance(name, str) and bool(name) and Path(name).name == name and "/" not in name and "\\" not in name and not Path(name).is_absolute() and ".." not in Path(name).parts


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        return file, raw, payload
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise DatasetValidationError(f"E14.7q {label} is not valid UTF-8 JSON: {file}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _bundle_artifact(relative_path: str, raw: bytes, role: str, dossier_id: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {"relativePath": relative_path, "role": role, "sha256": _sha(raw), "sizeBytes": len(raw)}
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
        raise DatasetValidationError(f"Immutable E14.7q handoff output already exists: {path}") from error
