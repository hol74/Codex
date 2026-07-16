from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "POST_2005_POLICY_REDESIGN_HANDOFF_BLOCKED_SCHEMA_ID_INCOMPATIBILITY"
EXPECTED_AUTHORIZATION_POLICY = {
    "handoffReadinessAuditAuthorized": True,
    "bundlePublicationAuthorized": False,
    "receiptTemplatePublicationAuthorized": False,
    "receiptIngestionAuthorized": False,
    "policyActivationAuthorized": False,
    "requestCatalogGenerationAuthorized": False,
    "sourceAcquisitionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
EXPECTED_NEXT_ACTION = (
    "Version a dedicated independent-review schema that accepts the exact immutable "
    "policy-redesign dossier IDs and matches their evidence semantics, or version the "
    "proposal and dossiers with schema-compatible canonical IDs; then repeat this "
    "handoff gate without mutating E14.7n"
)
EXPECTED_PLAN_NEXT_ACTION = (
    "Version a dedicated independent-review schema that accepts the exact immutable "
    "policy-redesign dossier IDs, or version the proposal and dossiers with "
    "schema-compatible canonical IDs; then repeat this handoff gate without mutating E14.7n"
)


def write_e14_post2005_policy_redesign_handoff_audit(
    contract_path: str | Path,
    proposal_path: str | Path,
    review_queue_path: str | Path,
    proposal_audit_path: str | Path,
    review_schema_path: str | Path,
    dossier_dir: str | Path,
    handoff_evidence_path: str | Path,
    handoff_plan_path: str | Path,
    handoff_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "handoff contract", "policy-redesign proposal", "review queue",
        "proposal audit", "review schema v2", "handoff evidence",
        "handoff plan", "handoff audit schema",
    )
    paths = (
        contract_path, proposal_path, review_queue_path, proposal_audit_path,
        review_schema_path, handoff_evidence_path, handoff_plan_path,
        handoff_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, proposal, queue, proposal_audit, review_schema, evidence, plan, audit_schema = (
        item[2] for item in artifacts
    )
    dossiers = _load_dossiers(queue, dossier_dir)
    dossier_by_id = {item[0]["dossierId"]: item for item in dossiers}
    expected_ids = contract.get("expectedQueuedDossierIds", [])
    hashes = {
        "proposalSha256": _sha(artifacts[1][1]),
        "reviewQueueSha256": _sha(artifacts[2][1]),
        "proposalAuditSha256": _sha(artifacts[3][1]),
        "crossG5DossierSha256": _sha(dossier_by_id[expected_ids[0]][1]) if len(expected_ids) == 2 and expected_ids[0] in dossier_by_id else "",
        "bankFdicDossierSha256": _sha(dossier_by_id[expected_ids[1]][1]) if len(expected_ids) == 2 and expected_ids[1] in dossier_by_id else "",
        "reviewSchemaV2Sha256": _sha(artifacts[4][1]),
        "handoffEvidenceSha256": _sha(artifacts[5][1]),
        "handoffPlanSha256": _sha(artifacts[6][1]),
        "handoffSchemaSha256": _sha(artifacts[7][1]),
    }
    _validate_inputs(
        contract, proposal, queue, proposal_audit, review_schema, evidence,
        plan, audit_schema, dossiers, hashes, artifacts,
    )

    pattern = review_schema["properties"]["dossierId"]["pattern"]
    assessments = []
    for dossier, _, manifest in dossiers:
        dossier_id = dossier["dossierId"]
        id_compatible = re.fullmatch(pattern, dossier_id) is not None
        has_counterevidence = isinstance(dossier.get("counterEvidence"), list) and bool(dossier["counterEvidence"])
        assessments.append({
            "dossierId": dossier_id,
            "dossierSha256": manifest["sha256"],
            "reviewSchemaDossierIdPattern": pattern,
            "dossierIdSchemaCompatible": id_compatible,
            "completedSchemaV2ReceiptPossible": id_compatible and has_counterevidence,
            "hasEvidenceItems": isinstance(dossier.get("evidenceItems"), list) and bool(dossier["evidenceItems"]),
            "hasCounterEvidence": has_counterevidence,
            "aliasingAuthorized": False,
            "status": "BLOCKED_SCHEMA_AND_EVIDENCE_CONTRACT_INCOMPATIBLE",
        })

    output = Path(output_path).resolve()
    if output.exists():
        raise DatasetValidationError("Immutable E14.7o handoff audit output already exists.")
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignHandoffAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("handoffContract", "policyRedesignProposal", "reviewQueue", "proposalAudit", "reviewSchemaV2", "handoffEvidence", "handoffPlan", "handoffAuditSchema"),
                artifacts,
            )
        },
        "inventory": {
            "queuedDossierCount": len(dossiers),
            "schemaCompatibleDossierCount": sum(item["dossierIdSchemaCompatible"] for item in assessments),
            "schemaIncompatibleDossierCount": sum(not item["dossierIdSchemaCompatible"] for item in assessments),
            "bundleArtifactCount": 0,
            "worksheetCount": 0,
            "receiptTemplateCount": 0,
            "independentReviewReceiptCount": 0,
        },
        "compatibilityAssessments": assessments,
        "checks": {
            "allInputHashesExact": True,
            "proposalQueueAndDossiersHashBound": True,
            "queueProposalManifestMatchesBytes": True,
            "proposalItemsMatchDossiers": True,
            "reviewSchemaDossierIdPatternChecked": True,
            "allQueuedDossierIdsSchemaCompatible": False,
            "reviewSchemaEvidenceSemanticsCompatible": False,
            "aliasesForbidden": True,
            "misleadingBundleSuppressed": True,
            "immutableE14nOutputsUnchanged": True,
        },
        "protocol": {
            "metadataOnly": True,
            "bundlePublished": False,
            "worksheetsPublished": 0,
            "receiptTemplatesPublished": 0,
            "reviewPerformedByGate": False,
            "requestCatalogGenerated": False,
            "seriesObservationsDownloaded": False,
            "featuresTransformed": 0,
            "candidatesGenerated": 0,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "handoffReadinessComplete": True,
            "handoffReady": False,
            "schemaRevisionRequired": True,
            "evidenceContractRevisionRequired": True,
            "bundlePublicationAuthorized": False,
            "receiptTemplatePublicationAuthorized": False,
            "receiptIngestionAuthorized": False,
            "policyActivationAuthorized": False,
            "requestCatalogGenerationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": EXPECTED_NEXT_ACTION,
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_policy_redesign_handoff",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _write_new(output, _json_bytes(audit))
    return output


def _validate_inputs(
    contract: dict[str, Any], proposal: dict[str, Any], queue: dict[str, Any],
    proposal_audit: dict[str, Any], review_schema: dict[str, Any], evidence: dict[str, Any],
    plan: dict[str, Any], audit_schema: dict[str, Any],
    dossiers: list[tuple[dict[str, Any], bytes, dict[str, Any]]],
    hashes: dict[str, str], artifacts: list[tuple[Path, bytes, dict[str, Any]]],
) -> None:
    ids = [item[0]["dossierId"] for item in dossiers]
    pattern = review_schema.get("properties", {}).get("dossierId", {}).get("pattern")
    proposal_items = {item["proposalItemId"]: item for item in proposal.get("proposalItems", [])}
    dossier_items_match = all(
        dossier.get("proposalItem") == proposal_items.get(dossier.get("proposalItem", {}).get("proposalItemId"))
        for dossier, _, _ in dossiers
    )
    queue_proposal = queue.get("proposal", {})
    proposal_artifact = _artifact(artifacts[1][0], artifacts[1][1])
    queue_outputs = proposal_audit.get("outputs", {})
    policy = plan.get("authorizationPolicy")
    expected_dossier_outputs = [
        _artifact(Path(manifest["fileName"]), raw)
        for _, raw, manifest in dossiers
    ]
    semantic = evidence.get("semanticCompatibility", {})
    aliasing = evidence.get("aliasingPolicy", {})
    if (
        contract.get("contractId") != "e14-post2005-policy-redesign-handoff-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or contract.get("authorizationPolicy") != EXPECTED_AUTHORIZATION_POLICY
        or policy != EXPECTED_AUTHORIZATION_POLICY
        or contract.get("nextAllowedAction") != EXPECTED_NEXT_ACTION
        or plan.get("nextAllowedAction") != EXPECTED_PLAN_NEXT_ACTION
        or contract.get("expectedCompatibleDossierCount") != 0
        or contract.get("expectedIncompatibleDossierCount") != 2
        or proposal.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or queue.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or queue.get("receipts") != []
        or ids != contract.get("expectedQueuedDossierIds")
        or len(ids) != len(set(ids)) or len(ids) != 2
        or queue_proposal != proposal_artifact
        or proposal_audit.get("status") != "POST_2005_POLICY_REDESIGN_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
        or queue_outputs.get("proposal") != proposal_artifact
        or queue_outputs.get("independentReviewQueue") != _artifact(artifacts[2][0], artifacts[2][1])
        or queue_outputs.get("dossiers") != expected_dossier_outputs
        or not dossier_items_match
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or pattern != "^e14-dossier-[a-z0-9-]+$"
        or pattern != contract.get("expectedReviewSchemaDossierIdPattern")
        or any(re.fullmatch(pattern, dossier_id) is not None for dossier_id in ids)
        or evidence.get("schemaIncompatibleQueuedDossierIds") != ids
        or evidence.get("schemaCompatibleQueuedDossierIds") != []
        or evidence.get("queuedDossierIds") != ids
        or evidence.get("reviewSchemaDossierIdPattern") != pattern
        or semantic != {
            "queuedDossiersContainEvidenceItems": False,
            "queuedDossiersContainCounterEvidence": False,
            "reviewSchemaRequiresCounterEvidenceConsideredTrue": True,
            "g5MethodologyBoundaryHasDedicatedHashBoundLocator": False,
            "fdicQ4CutoffExclusionHasDedicatedHashBoundLocator": False,
        }
        or aliasing != {
            "aliasDossierIdsAuthorized": False,
            "reason": "A schema-compatible alias would no longer equal the immutable dossierId in the review queue and therefore could not bind an authentic receipt to the queued dossier.",
        }
        or evidence.get("requiredDisposition") != "BLOCK_HANDOFF_AND_VERSION_THE_REVIEW_SCHEMA_EVIDENCE_CONTRACT_OR_THE_PROPOSAL_DOSSIERS"
        or plan.get("expectedStatus") != STATUS
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-policy-redesign-handoff-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7o policy-redesign handoff inputs are invalid.")


def _load_dossiers(queue: dict[str, Any], directory: str | Path) -> list[tuple[dict[str, Any], bytes, dict[str, Any]]]:
    root = Path(directory).resolve()
    result = []
    for manifest in queue.get("dossiers", []):
        name = manifest.get("fileName", "")
        if not name or Path(name).name != name:
            raise DatasetValidationError("E14.7o dossier path is invalid.")
        path = root / name
        file, raw, dossier = _read(path, "policy-redesign dossier")
        if (
            _sha(raw) != manifest.get("sha256")
            or len(raw) != manifest.get("sizeBytes")
            or dossier.get("dossierId") != manifest.get("dossierId")
            or dossier.get("artifactType") != "E14Post2005PolicyRedesignDossier"
            or dossier.get("reviewStatus") != "awaiting-independent-review"
            or file.parent != root
        ):
            raise DatasetValidationError("E14.7o dossier hash or content is invalid.")
        result.append((dossier, raw, manifest))
    return result


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        return file, raw, payload
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise DatasetValidationError(f"E14.7o {label} is not valid UTF-8 JSON: {file}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


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
        raise DatasetValidationError(f"Immutable E14.7o handoff audit output already exists: {path}") from error
