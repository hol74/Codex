from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


def write_e14_post2005_scope_activation(
    contract_path: str | Path,
    proposal_path: str | Path,
    final_queue_path: str | Path,
    review_audit_path: str | Path,
    taxonomy_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_raw, contract = _read(contract_path)
    proposal_file, proposal_raw, proposal = _read(proposal_path)
    queue_file, queue_raw, queue = _read(final_queue_path)
    review_file, review_raw, review = _read(review_audit_path)
    actual = {
        "finalReviewedQueueSha256": _sha(queue_raw),
        "reviewIngestionAuditSha256": _sha(review_raw),
        "taxonomyProposalSha256": _sha(proposal_raw),
    }
    expected_policy = {
        "allDossiersMustBeIndependentlyAccepted": True,
        "candidateGenerationRemainsForbidden": True,
        "dataAcquisitionNotPerformedByGate": True,
        "legacyTaxonomyRemainsUnchanged": True,
        "outerOosRemainsClosed": True,
        "sourceAcquisitionRequiresSeparatePreregistration": True,
    }
    manifests = {item["dossierId"]: item for item in queue.get("dossiers", [])}
    accepted = {"accept-by-independent-receipt", "accept-by-targeted-independent-receipt"}
    controls = proposal.get("proposedBankingHardNegativeControls", [])
    if (
        contract.get("contractId") != "e14-post2005-scope-activation-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("policy") != expected_policy
        or contract.get("readinessDecision") != "READY_TO_ACTIVATE_SEPARATELY_VERSIONED_POST_2005_SCOPE"
        or proposal.get("proposedTaxonomyId") != "us-financial-stress-post2005-v1"
        or proposal.get("activation", {}).get("active") is not False
        or queue.get("status") != "TARGETED_REVIEW_COMPLETE_ALL_ACCEPTED"
        or len(manifests) != 2
        or any(item.get("reviewStatus") not in accepted for item in manifests.values())
        or review.get("status") != "POST_2005_REVIEW_ACCEPTED_SEPARATE_ACTIVATION_GATE_REQUIRED"
        or review.get("decision", {}).get("separateActivationGateAuthorized") is not True
        or review.get("decision", {}).get("scopeActivated") is not False
        or len(controls) != 2
    ):
        raise DatasetValidationError("E14.7h scope activation inputs are invalid or not fully accepted.")

    activated_controls = []
    for control in controls:
        dossier_id = next((key for key in manifests if manifests[key]["fileName"] == control["dossier"]["fileName"]), None)
        if dossier_id is None:
            raise DatasetValidationError("E14.7h accepted dossier is not bound to the proposal.")
        manifest = manifests[dossier_id]
        revised = {**control, "dossier": {key: manifest[key] for key in ("fileName", "sha256", "sizeBytes")}, "reviewStatus": "accepted-by-independent-review"}
        if dossier_id.endswith("archegos-contained-2021-banking-credit"):
            revised["lastMonth"] = "2021-06-01"
        activated_controls.append(revised)

    taxonomy = {
        **proposal,
        "artifactType": "E14Post2005FinancialStressTaxonomy",
        "taxonomyId": proposal["proposedTaxonomyId"],
        "status": "POST_2005_SCOPE_ACTIVE_SOURCE_PREREGISTRATION_REQUIRED",
        "proposedBankingHardNegativeControls": activated_controls,
        "activation": {
            "active": True,
            "labelsAccepted": True,
            "independentReviewComplete": True,
            "sourceAcquisitionAuthorized": False,
            "featureFoundationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
        },
    }
    taxonomy.pop("proposedTaxonomyId", None)
    taxonomy_path = Path(taxonomy_output_path).resolve()
    audit_path = Path(output_path).resolve()
    if taxonomy_path.exists() or audit_path.exists():
        raise DatasetValidationError("Immutable E14.7h output already exists.")
    taxonomy_path = _write(taxonomy_path, taxonomy)
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005ScopeActivationAudit",
        "status": "POST_2005_SCOPE_ACTIVE_SOURCE_PREREGISTRATION_REQUIRED",
        "inputs": {"activationContract": _artifact(contract_file, contract_raw), "taxonomyProposal": _artifact(proposal_file, proposal_raw), "finalReviewedQueue": _artifact(queue_file, queue_raw), "reviewIngestionAudit": _artifact(review_file, review_raw)},
        "outputs": {"activeTaxonomy": _artifact(taxonomy_path, taxonomy_path.read_bytes())},
        "inventory": {"positiveEpisodeCount": len(proposal["positiveEpisodeReferences"]), "inheritedHardNegativeCount": len(proposal["inheritedHardNegativeReferences"]), "acceptedBankingControlCount": len(activated_controls)},
        "checks": {"allDossiersAccepted": True, "revisedDossierHashPropagated": True, "legacyTaxonomyUnchanged": True, "sourceObservationsRead": False, "outerOosRead": False},
        "protocol": {"scopeActivated": True, "labelsAccepted": True, "observationsAcquired": 0, "sourceAcquisitionAuthorized": False, "featureFoundationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False},
        "decision": {"post2005ScopeActivated": True, "nextAllowedAction": "Preregister a source-acquisition manifest for the active post-2005 scope; do not acquire observations yet"},
        "implementation": {"module": "regime_eval.e14_post2005_scope_activation", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    return taxonomy_path, _write(audit_path, audit)


def _read(path: str | Path) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7h input is not valid JSON: {source}") from error


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14.7h output exists: {path}") from error
    return path
