from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


PROPOSAL_SHA = "d88716b411e22332545422086521d2987232e293dc92c78b9a426bbeb10a019a"
PROPOSAL_AUDIT_SHA = "a477ffe7ed6731bf92ab260740baada0e1976fffb525dbb0416669d900fb4fe0"
QUEUE_SHA = "dd639fbf829afb10df69d7260ee56e66c57779e2a205b55c71bf97180db35f10"
INGESTION_AUDIT_SHA = "e27fd8c5c2e34170ea292fc47bd32ce12aff1eb75008a3c20583a75be91c5914"
BASE_TAXONOMY_SHA = "3f69670e43315904e47a9bcae1957c62d780665b047355230198bb7a129e9d58"
SCOPE_ACTIVATION_AUDIT_SHA = "77b38fe8be5c6fa235d4d68437ae0c184fa70eab7ea23d5839def575c112e9db"
REDESIGN_PLAN_SHA = "232b64e624e2514bbd1bc810b7bb332a94afbed65724911686a0a2f1b027ffaa"
PLAN_SHA = "94c7efa8f78118c5cd6983e601b769987c89571da4535461c4f4561dde600e87"
SCHEMA_SHA = "978a77c7bc89704032c4999045b0ec1e60e1db6506792ac236c6d0fd9d6db71e"
DOSSIER_IDS = [
    "e14-post2005-policy-redesign-dossier-cross-g5-monthly-release-replacement-v1",
    "e14-post2005-policy-redesign-dossier-bank-fdic-publication-vintage-policy-v1",
]
ACTIVATION_POLICY = {
    "allRedesignDossiersMustBeAuthenticallyAccepted": True,
    "baseScopeAndAcceptedLabelsRemainUnchanged": True,
    "policyOverlayMustBeSeparatelyVersioned": True,
    "legacyH10ArtifactsCannotSatisfyRedesignedCrossBorderPolicy": True,
    "g5MethodologyRegimesMustRemainSeparated": True,
    "fdicEligibilityRequiresProviderPrimaryActualPublicationProof": True,
    "requestCatalogGenerationAuthorizedByGate": True,
    "requestCatalogNotGeneratedByGate": True,
    "sourceAcquisitionNotPerformedOrAuthorizedByGate": True,
    "featureTransformationRemainsForbidden": True,
    "candidateGenerationRemainsForbidden": True,
    "evaluationRemainsForbidden": True,
    "outerOosRemainsClosed": True,
}
AUTHORIZATION_POLICY = {
    "policyActivationAuthorized": True,
    "sourceManifestAndRequestCatalogPreregistrationAuthorized": True,
    "requestCatalogGenerationAuthorized": True,
    "requestCatalogGenerationPerformedByActivation": False,
    "sourceAcquisitionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
NEXT_ACTION = (
    "Preregister a versioned post-2005 source-acquisition manifest and request "
    "catalog bound to the active source-vintage policy v2; do not acquire observations yet"
)
STATUS = "POST_2005_REDESIGNED_POLICY_ACTIVE_REQUEST_CATALOG_PREREGISTRATION_REQUIRED"


def write_e14_post2005_policy_redesign_activation(
    contract_path: str | Path,
    proposal_path: str | Path,
    proposal_audit_path: str | Path,
    reviewed_queue_path: str | Path,
    review_ingestion_audit_path: str | Path,
    base_active_taxonomy_path: str | Path,
    scope_activation_audit_path: str | Path,
    policy_redesign_plan_path: str | Path,
    activation_plan_path: str | Path,
    activation_audit_schema_path: str | Path,
    active_policy_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    labels = (
        "activation contract", "policy-redesign proposal", "policy-redesign proposal audit",
        "reviewed queue v3", "review ingestion audit", "base active taxonomy",
        "scope activation audit", "policy-redesign plan", "activation plan",
        "activation audit schema",
    )
    paths = (
        contract_path, proposal_path, proposal_audit_path, reviewed_queue_path,
        review_ingestion_audit_path, base_active_taxonomy_path,
        scope_activation_audit_path, policy_redesign_plan_path,
        activation_plan_path, activation_audit_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, proposal, proposal_audit, queue, ingestion_audit, base_taxonomy, scope_audit, redesign_plan, plan, schema = (item[2] for item in artifacts)
    hashes = {
        "policyRedesignProposalSha256": _sha(artifacts[1][1]),
        "policyRedesignProposalAuditSha256": _sha(artifacts[2][1]),
        "reviewedQueueV3Sha256": _sha(artifacts[3][1]),
        "reviewIngestionAuditSha256": _sha(artifacts[4][1]),
        "baseActiveTaxonomySha256": _sha(artifacts[5][1]),
        "scopeActivationAuditSha256": _sha(artifacts[6][1]),
        "policyRedesignPlanSha256": _sha(artifacts[7][1]),
        "activationPlanSha256": _sha(artifacts[8][1]),
        "activationAuditSchemaSha256": _sha(artifacts[9][1]),
    }
    _validate_inputs(contract, proposal, proposal_audit, queue, ingestion_audit, base_taxonomy, scope_audit, redesign_plan, plan, schema, hashes, artifacts)

    active_policy_output = Path(active_policy_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    expected_names = (
        "e14-post2005-active-source-vintage-policy-v2.json",
        "e14-post2005-policy-redesign-activation-audit-v1.json",
    )
    protected_parent = artifacts[4][0].parent
    protected_roots = (
        protected_parent / "completed-policy-redesign-receipts-v1",
        protected_parent / "e14-post2005-policy-redesign-dossiers-v1",
        protected_parent / "e14-post2005-policy-redesign-review-handoff-v1",
    )
    outputs = (active_policy_output, audit_output)
    if (
        tuple(output.name for output in outputs) != expected_names
        or any(output.exists() for output in outputs)
        or active_policy_output == audit_output
        or any(output in {item[0] for item in artifacts} for output in outputs)
        or any(output.is_relative_to(root.resolve()) for output in outputs for root in protected_roots)
    ):
        raise DatasetValidationError("E14.7s activation output path is invalid, occupied, or overlaps protected evidence.")

    dossiers = {item["dossierId"]: item for item in queue["dossiers"]}
    receipts = {item["dossierId"]: item for item in queue["receipts"]}
    active_items = []
    for item in proposal["proposalItems"]:
        dossier_id = f"e14-post2005-policy-redesign-dossier-{item['proposalItemId']}"
        active_items.append({
            **item,
            "proposalStatus": "active-by-separate-reviewed-policy-gate",
            "review": {
                "dossier": dossiers[dossier_id],
                "receipt": receipts[dossier_id],
            },
        })

    active_policy = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignActivePolicy",
        "policyId": "e14-post2005-active-source-vintage-policy-v2",
        "status": STATUS,
        "scope": "post-2005-financial-stress-research-only",
        "activatedFromProposal": _artifact(artifacts[1][0], artifacts[1][1]),
        "reviewAuthorization": {
            "reviewedQueueV3": _artifact(artifacts[3][0], artifacts[3][1]),
            "reviewIngestionAudit": _artifact(artifacts[4][0], artifacts[4][1]),
        },
        "baseActiveTaxonomy": _artifact(artifacts[5][0], artifacts[5][1]),
        "preservedReadyMechanisms": proposal["preservedReadyMechanisms"],
        "activePolicyItems": active_items,
        "governance": {
            "activatedBySeparateVersionedGate": True,
            "independentReviewComplete": True,
            "proposalBytesUnchanged": True,
            "legacyFitnessAuditImmutable": True,
            "legacyRemediationAuditImmutable": True,
            "g5MethodologyRegimesRemainSeparate": True,
            "fdicActualPublicationProofRequired": True,
            "legacyH10ManifestAndSnapshotNotValidForPolicyV2": True,
        },
        "authorization": {
            "active": True,
            "sourceManifestAndRequestCatalogPreregistrationAuthorized": True,
            "requestCatalogGenerationAuthorized": True,
            "requestCatalogGenerated": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
        },
        "nextAllowedAction": NEXT_ACTION,
    }
    active_policy_raw = _json_bytes(active_policy)
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignActivationAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("activationContract", "policyRedesignProposal", "policyRedesignProposalAudit", "reviewedQueueV3", "reviewIngestionAudit", "baseActiveTaxonomy", "scopeActivationAudit", "policyRedesignPlan", "activationPlan", "activationAuditSchema"),
                artifacts,
            )
        },
        "outputs": {"activePolicy": _artifact(active_policy_output, active_policy_raw)},
        "inventory": {
            "proposalItemCount": len(active_items),
            "acceptedDossierCount": len(dossiers),
            "authenticIndependentReceiptCount": len(receipts),
            "preservedReadyMechanismCount": len(proposal["preservedReadyMechanisms"]),
        },
        "checks": {
            "allInputHashesExact": True,
            "reviewedQueueBoundToProposal": True,
            "reviewedQueueBoundToIngestionAudit": True,
            "allDossiersAcceptedByAuthenticIndependentReceipts": True,
            "proposalItemsBoundToAcceptedDossiers": True,
            "g5MethodologySeparationPreserved": True,
            "fdicPublicationProofPolicyPreserved": True,
            "legacyArtifactsUnchanged": True,
            "baseScopeAndAcceptedLabelsUnchanged": True,
            "legacyH10ManifestAndSnapshotNotReused": True,
            "sourceObservationsRead": False,
            "outerOosRead": False,
        },
        "protocol": {
            "policyActivated": True,
            "requestCatalogGenerated": False,
            "requestCatalogGenerationAuthorized": True,
            "observationsAcquired": 0,
            "featuresTransformed": 0,
            "candidatesGenerated": 0,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "post2005PolicyRedesignActivated": True,
            "sourceManifestAndRequestCatalogPreregistrationAuthorized": True,
            "requestCatalogGenerationAuthorized": True,
            "requestCatalogGenerationPerformed": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": NEXT_ACTION,
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_policy_redesign_activation",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_activation_audit(audit)
    _write_pair(active_policy_output, active_policy_raw, audit_output, _json_bytes(audit))
    return active_policy_output, audit_output


def _validate_inputs(
    contract: dict[str, Any], proposal: dict[str, Any], proposal_audit: dict[str, Any],
    queue: dict[str, Any], ingestion_audit: dict[str, Any], base_taxonomy: dict[str, Any],
    scope_audit: dict[str, Any], redesign_plan: dict[str, Any], plan: dict[str, Any],
    schema: dict[str, Any],
    hashes: dict[str, str], artifacts: list[tuple[Path, bytes, dict[str, Any]]],
) -> None:
    canonical_hashes = {
        "policyRedesignProposalSha256": PROPOSAL_SHA,
        "policyRedesignProposalAuditSha256": PROPOSAL_AUDIT_SHA,
        "reviewedQueueV3Sha256": QUEUE_SHA,
        "reviewIngestionAuditSha256": INGESTION_AUDIT_SHA,
        "baseActiveTaxonomySha256": BASE_TAXONOMY_SHA,
        "scopeActivationAuditSha256": SCOPE_ACTIVATION_AUDIT_SHA,
        "policyRedesignPlanSha256": REDESIGN_PLAN_SHA,
        "activationPlanSha256": PLAN_SHA,
        "activationAuditSchemaSha256": SCHEMA_SHA,
    }
    dossier_ids = [item.get("dossierId") for item in queue.get("dossiers", [])]
    receipt_ids = [item.get("dossierId") for item in queue.get("receipts", [])]
    proposal_item_ids = [
        f"e14-post2005-policy-redesign-dossier-{item.get('proposalItemId', '')}"
        for item in proposal.get("proposalItems", [])
    ]
    if (
        contract.get("contractId") != "e14-post2005-policy-redesign-activation-contract-v1"
        or contract.get("inputHashes") != hashes
        or hashes != canonical_hashes
        or contract.get("expectedProposalId") != "e14-post2005-policy-redesign-proposal-v1"
        or contract.get("expectedReviewedQueueId") != "e14-post2005-policy-redesign-reviewed-queue-v3"
        or contract.get("expectedActivePolicyId") != "e14-post2005-active-source-vintage-policy-v2"
        or contract.get("expectedDossierIds") != DOSSIER_IDS
        or contract.get("activationPolicy") != ACTIVATION_POLICY
        or contract.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or contract.get("nextAllowedAction") != NEXT_ACTION
        or plan.get("expectedProposalId") != contract.get("expectedProposalId")
        or plan.get("expectedReviewedQueueId") != contract.get("expectedReviewedQueueId")
        or plan.get("expectedActivePolicyId") != contract.get("expectedActivePolicyId")
        or plan.get("expectedDossierIds") != DOSSIER_IDS
        or plan.get("activationPolicy") != ACTIVATION_POLICY
        or plan.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or plan.get("nextAllowedAction") != NEXT_ACTION
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-policy-redesign-activation-audit-v1.json"
        or proposal.get("proposalId") != "e14-post2005-policy-redesign-proposal-v1"
        or proposal.get("status") != "AWAITING_INDEPENDENT_REVIEW"
        or proposal.get("governance", {}).get("proposalDoesNotActivatePolicy") is not True
        or proposal_audit.get("status") != "POST_2005_POLICY_REDESIGN_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
        or proposal_audit.get("outputs", {}).get("proposal") != _artifact(artifacts[1][0], artifacts[1][1])
        or proposal_audit.get("inputs", {}).get("redesignPlan") != _artifact(artifacts[7][0], artifacts[7][1])
        or redesign_plan.get("redesignProposals") != proposal.get("proposalItems")
        or queue.get("queueId") != "e14-post2005-policy-redesign-reviewed-queue-v3"
        or queue.get("status") != "REVIEW_COMPLETE_ALL_ACCEPTED_SEPARATE_POLICY_ACTIVATION_GATE_REQUIRED"
        or queue.get("proposal") != _artifact(artifacts[1][0], artifacts[1][1])
        or dossier_ids != DOSSIER_IDS
        or len(receipt_ids) != 2 or sorted(receipt_ids) != sorted(DOSSIER_IDS)
        or len({item.get("reviewId") for item in queue.get("receipts", [])}) != 2
        or proposal_item_ids != DOSSIER_IDS
        or any(item.get("reviewStatus") != "accept-by-authentic-independent-receipt" for item in queue.get("dossiers", []))
        or any(item.get("decision") != "accept" for item in queue.get("receipts", []))
        or ingestion_audit.get("status") != "POST_2005_POLICY_REDESIGN_REVIEW_ACCEPTED_SEPARATE_ACTIVATION_GATE_REQUIRED"
        or ingestion_audit.get("outputs", {}).get("reviewedQueueV3") != _artifact(artifacts[3][0], artifacts[3][1])
        or ingestion_audit.get("receiptArtifacts") != queue.get("receipts")
        or ingestion_audit.get("inventory", {}).get("acceptedCount") != 2
        or ingestion_audit.get("decision", {}).get("allDossiersAccepted") is not True
        or ingestion_audit.get("decision", {}).get("separatePolicyActivationGateAuthorized") is not True
        or ingestion_audit.get("decision", {}).get("policyActivated") is not False
        or any(ingestion_audit.get("decision", {}).get(key) is not False for key in (
            "sourceAcquisitionAuthorized", "featureTransformationAuthorized",
            "candidateGenerationAuthorized", "evaluationAuthorized", "outerOosAuthorized",
        ))
        or ingestion_audit.get("protocol", {}).get("requestCatalogGenerated") is not False
        or ingestion_audit.get("protocol", {}).get("seriesObservationsDownloaded") is not False
        or ingestion_audit.get("protocol", {}).get("featuresTransformed") != 0
        or ingestion_audit.get("protocol", {}).get("candidatesGenerated") != 0
        or base_taxonomy.get("taxonomyId") != "us-financial-stress-post2005-v1"
        or base_taxonomy.get("status") != "POST_2005_SCOPE_ACTIVE_SOURCE_PREREGISTRATION_REQUIRED"
        or base_taxonomy.get("activation", {}).get("active") is not True
        or base_taxonomy.get("activation", {}).get("labelsAccepted") is not True
        or any(base_taxonomy.get("activation", {}).get(key) is not False for key in (
            "sourceAcquisitionAuthorized", "featureFoundationAuthorized",
            "candidateGenerationAuthorized", "evaluationAuthorized", "outerOosAuthorized",
        ))
        or scope_audit.get("status") != "POST_2005_SCOPE_ACTIVE_SOURCE_PREREGISTRATION_REQUIRED"
        or scope_audit.get("outputs", {}).get("activeTaxonomy") != _artifact(artifacts[5][0], artifacts[5][1])
        or scope_audit.get("decision", {}).get("post2005ScopeActivated") is not True
    ):
        raise DatasetValidationError("E14.7s policy-activation inputs are invalid or not fully accepted.")


def _validate_activation_audit(audit: dict[str, Any]) -> None:
    top_keys = {"schemaVersion", "artifactType", "status", "inputs", "outputs", "inventory", "checks", "protocol", "decision", "implementation"}
    input_keys = {"activationContract", "policyRedesignProposal", "policyRedesignProposalAudit", "reviewedQueueV3", "reviewIngestionAudit", "baseActiveTaxonomy", "scopeActivationAudit", "policyRedesignPlan", "activationPlan", "activationAuditSchema"}
    artifact_keys = {"fileName", "sha256", "sizeBytes"}
    expected_inventory = {
        "proposalItemCount": 2,
        "acceptedDossierCount": 2,
        "authenticIndependentReceiptCount": 2,
        "preservedReadyMechanismCount": 2,
    }
    expected_checks = {
        "allInputHashesExact": True,
        "reviewedQueueBoundToProposal": True,
        "reviewedQueueBoundToIngestionAudit": True,
        "allDossiersAcceptedByAuthenticIndependentReceipts": True,
        "proposalItemsBoundToAcceptedDossiers": True,
        "g5MethodologySeparationPreserved": True,
        "fdicPublicationProofPolicyPreserved": True,
        "legacyArtifactsUnchanged": True,
        "baseScopeAndAcceptedLabelsUnchanged": True,
        "legacyH10ManifestAndSnapshotNotReused": True,
        "sourceObservationsRead": False,
        "outerOosRead": False,
    }
    expected_protocol = {
        "policyActivated": True,
        "requestCatalogGenerated": False,
        "requestCatalogGenerationAuthorized": True,
        "observationsAcquired": 0,
        "featuresTransformed": 0,
        "candidatesGenerated": 0,
        "evaluationPerformed": False,
        "outerOosRead": False,
    }
    expected_decision = {
        "post2005PolicyRedesignActivated": True,
        "sourceManifestAndRequestCatalogPreregistrationAuthorized": True,
        "requestCatalogGenerationAuthorized": True,
        "requestCatalogGenerationPerformed": False,
        "sourceAcquisitionAuthorized": False,
        "featureTransformationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "evaluationAuthorized": False,
        "outerOosAuthorized": False,
        "nextAllowedAction": NEXT_ACTION,
    }
    artifacts = list(audit.get("inputs", {}).values()) + list(audit.get("outputs", {}).values())
    if (
        set(audit) != top_keys
        or audit.get("schemaVersion") != 1
        or audit.get("artifactType") != "E14Post2005PolicyRedesignActivationAudit"
        or audit.get("status") != STATUS
        or set(audit.get("inputs", {})) != input_keys
        or set(audit.get("outputs", {})) != {"activePolicy"}
        or any(not isinstance(item, dict) or set(item) != artifact_keys or not item.get("fileName") or not isinstance(item.get("sizeBytes"), int) or item["sizeBytes"] < 1 or not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64 for item in artifacts)
        or audit.get("inventory") != expected_inventory
        or audit.get("checks") != expected_checks
        or audit.get("protocol") != expected_protocol
        or audit.get("decision") != expected_decision
        or set(audit.get("implementation", {})) != {"module", "sourceSha256"}
        or audit.get("implementation", {}).get("module") != "regime_eval.e14_post2005_policy_redesign_activation"
        or not isinstance(audit.get("implementation", {}).get("sourceSha256"), str)
        or len(audit["implementation"]["sourceSha256"]) != 64
    ):
        raise DatasetValidationError("E14.7s generated activation audit violates its closed schema contract.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        return file, raw, payload
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise DatasetValidationError(f"E14.7s {label} is not valid UTF-8 JSON: {file}") from error


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
        raise DatasetValidationError(f"Immutable E14.7s activation output already exists: {path}") from error


def _write_pair(first_path: Path, first_raw: bytes, second_path: Path, second_raw: bytes) -> None:
    created: list[Path] = []
    try:
        _write_new(first_path, first_raw)
        created.append(first_path)
        _write_new(second_path, second_raw)
        created.append(second_path)
    except (DatasetValidationError, OSError) as error:
        for path in reversed(created):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        if isinstance(error, DatasetValidationError):
            raise
        raise DatasetValidationError("E14.7s output pair could not be published atomically.") from error
