from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "POST_2005_POLICY_REDESIGN_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
ITEM_IDS = [
    "cross-g5-monthly-release-replacement-v1",
    "bank-fdic-publication-vintage-policy-v1",
]


def write_e14_post2005_policy_redesign_proposal(
    contract_path: str | Path,
    vintage_fitness_audit_path: str | Path,
    vintage_remediation_audit_path: str | Path,
    scope_plan_path: str | Path,
    fitness_plan_path: str | Path,
    redesign_evidence_path: str | Path,
    redesign_plan_path: str | Path,
    redesign_schema_path: str | Path,
    independent_review_schema_path: str | Path,
    proposal_output_path: str | Path,
    dossier_output_dir: str | Path,
    queue_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, ...]:
    labels = (
        "redesign contract", "vintage fitness audit", "vintage remediation audit",
        "scope plan", "fitness plan", "redesign evidence", "redesign plan",
        "redesign schema", "independent review schema",
    )
    paths = (
        contract_path, vintage_fitness_audit_path, vintage_remediation_audit_path,
        scope_plan_path, fitness_plan_path, redesign_evidence_path, redesign_plan_path,
        redesign_schema_path, independent_review_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, fitness, remediation, scope, fitness_plan, evidence, plan, schema, review_schema = [item[2] for item in artifacts]
    hash_names = (
        "vintageFitnessAuditSha256", "vintageRemediationAuditSha256", "scopePlanSha256",
        "fitnessPlanSha256", "redesignEvidenceSha256", "redesignPlanSha256",
        "redesignSchemaSha256", "independentReviewSchemaSha256",
    )
    actual_hashes = {name: _sha(raw) for name, (_, raw, _) in zip(hash_names, artifacts[1:])}
    _validate_inputs(contract, fitness, remediation, scope, fitness_plan, evidence, plan, schema, review_schema, actual_hashes)

    proposal_output = Path(proposal_output_path).resolve()
    dossier_dir = Path(dossier_output_dir).resolve()
    queue_output = Path(queue_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    dossier_paths = [dossier_dir / f"e14-post2005-policy-redesign-dossier-{item_id}.json" for item_id in ITEM_IDS]
    targets = [proposal_output, *dossier_paths, queue_output, audit_output]
    if any(path.exists() for path in targets):
        raise DatasetValidationError("Immutable E14.7n output already exists.")

    proposal = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignProposal",
        "proposalId": "e14-post2005-policy-redesign-proposal-v1",
        "status": "AWAITING_INDEPENDENT_REVIEW",
        "preservedReadyMechanisms": plan["preservedReadyMechanisms"],
        "proposalItems": plan["redesignProposals"],
        "governance": {
            "legacyFitnessAuditImmutable": True,
            "legacyRemediationAuditImmutable": True,
            "acceptedLabelsUnchanged": True,
            "proposalDoesNotActivatePolicy": True,
            "proposalDoesNotAuthorizeRequestCatalog": True,
            "proposalDoesNotAuthorizeAcquisition": True,
            "proposalDoesNotAuthorizeTransformation": True,
            "independentReviewRequired": True,
        },
    }
    _validate_proposal(proposal, schema)
    proposal_raw = _json_bytes(proposal)

    dossier_outputs: list[tuple[Path, bytes, dict[str, Any]]] = []
    evidence_by_item = {
        ITEM_IDS[0]: {
            "replacementSource": evidence["replacementSource"],
            "requiredReviewFindings": [
                "G.5 has one unique dated release for every required pre-taper calendar month",
                "every selected legacy release contains Broad and OITP contemporaneously",
                "the 2019-02-04 methodology break is exact and no backcast is treated as event-time",
                "monthly cadence supports the proposed changes without importing daily H.10 semantics",
            ],
        },
        ITEM_IDS[1]: {
            "fdicAvailabilityEvidence": evidence["fdicAvailabilityEvidence"],
            "requiredReviewFindings": [
                "actual publication proof is required for every eligible QBP quarter",
                "quarter-end metadata cannot establish availability",
                "Q3 2025 is eligible from 2025-11-24 and Q4 2025 is not eligible at the cutoff",
                "forward-fill uses only the latest actually published QBP with explicit stale age",
            ],
        },
    }
    proposal_by_id = {item["proposalItemId"]: item for item in plan["redesignProposals"]}
    for path, item_id in zip(dossier_paths, ITEM_IDS):
        dossier = {
            "schemaVersion": 1,
            "artifactType": "E14Post2005PolicyRedesignDossier",
            "dossierId": f"e14-post2005-policy-redesign-dossier-{item_id}",
            "proposalItem": proposal_by_id[item_id],
            "evidence": evidence_by_item[item_id],
            "reviewPolicy": plan["reviewRequirements"],
            "reviewStatus": "awaiting-independent-review",
        }
        raw = _json_bytes(dossier)
        dossier_outputs.append((path, raw, dossier))

    queue = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignReviewQueue",
        "queueId": "e14-post2005-policy-redesign-review-queue-v1",
        "status": "AWAITING_INDEPENDENT_REVIEW",
        "proposalAuthor": plan["proposalAuthor"],
        "proposal": _artifact(proposal_output, proposal_raw),
        "dossiers": [
            {
                "dossierId": dossier["dossierId"], **_artifact(path, raw),
                "reviewStatus": "awaiting-independent-review",
            }
            for path, raw, dossier in dossier_outputs
        ],
        "reviewSchema": _artifact(artifacts[8][0], artifacts[8][1]),
        "requirements": plan["reviewRequirements"],
        "receipts": [],
    }
    queue_raw = _json_bytes(queue)
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005PolicyRedesignProposalAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw) for name, (file, raw, _) in zip(
                ("redesignContract", "vintageFitnessAudit", "vintageRemediationAudit", "scopePlan", "fitnessPlan", "redesignEvidence", "redesignPlan", "redesignSchema", "independentReviewSchema"),
                artifacts,
            )
        },
        "inventory": {
            "preservedReadyMechanismCount": 2, "redesignProposalItemCount": 2,
            "replacementSourceCount": 1, "queuedDossierCount": 2,
            "independentReviewReceiptCount": 0,
        },
        "checks": {
            "allInputHashesExact": True,
            "readyMechanismsPreservedExactly": True,
            "h10RetiredExactly": True,
            "g5ReplacementProviderPrimary": True,
            "g5PreTaperCalendarComplete": True,
            "g5MethodologyBreakExplicit": True,
            "silentCrossRegimeSpliceForbidden": True,
            "fdicActualPublicationProofRequired": True,
            "fdicQuarterEndAvailabilityForbidden": True,
            "proposalAndDossiersHashBound": True,
            "selfAcceptanceForbidden": True,
        },
        "outputs": {
            "proposal": _artifact(proposal_output, proposal_raw),
            "dossiers": [_artifact(path, raw) for path, raw, _ in dossier_outputs],
            "independentReviewQueue": _artifact(queue_output, queue_raw),
        },
        "protocol": {
            "metadataOnly": True, "seriesObservationsDownloaded": False,
            "policyActivated": False, "requestCatalogGenerated": False,
            "featuresTransformed": 0, "candidatesGenerated": 0,
            "evaluationPerformed": False, "outerOosRead": False,
        },
        "decision": {
            "proposalMaterialized": True,
            "independentReviewRequired": True,
            "independentReviewHandoffAuthorized": True,
            "policyActivationAuthorized": False,
            "requestCatalogGenerationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_policy_redesign",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }

    _write_raw(proposal_output, proposal_raw)
    for path, raw, _ in dossier_outputs:
        _write_raw(path, raw)
    _write_raw(queue_output, queue_raw)
    _write_raw(audit_output, _json_bytes(audit))
    return tuple(targets)


def _validate_inputs(
    contract: dict[str, Any], fitness: dict[str, Any], remediation: dict[str, Any],
    scope: dict[str, Any], fitness_plan: dict[str, Any], evidence: dict[str, Any],
    plan: dict[str, Any], schema: dict[str, Any], review_schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    items = plan.get("redesignProposals", [])
    source = evidence.get("replacementSource", {})
    fdic = evidence.get("fdicAvailabilityEvidence", {})
    if (
        contract.get("contractId") != "e14-post2005-policy-redesign-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or plan.get("planId") != "e14-post2005-policy-redesign-plan-v1"
        or plan.get("authorizationPolicy") != contract.get("authorizationPolicy")
        or [item.get("proposalItemId") for item in items] != contract.get("expectedProposalItemIds")
        or plan.get("preservedReadyMechanisms") != contract.get("expectedPreservedReadyMechanisms")
        or fitness.get("decision", {}).get("readyMechanisms") != plan.get("preservedReadyMechanisms")
        or remediation.get("decision", {}).get("policyRedesignRequired") is not True
        or remediation.get("decision", {}).get("sourceAcquisitionAuthorized") is not False
        or scope.get("cutoffInclusive") != "2006-01-01"
        or fitness_plan.get("authorizationPolicy", {}).get("featureTransformationAuthorized") is not False
        or source.get("sourceId") not in contract.get("expectedReplacementSourceIds", [])
        or source.get("observedReleaseMonthsBeforeTaper") != contract.get("expectedG5PreTaperMonthCount")
        or source.get("missingReleaseMonthsBeforeTaper") != []
        or source.get("methodologyBoundary", {}).get("effectiveReleaseDate") != contract.get("expectedMethodologyBoundary")
        or source.get("methodologyBoundary", {}).get("silentSpliceForbidden") is not True
        or fdic.get("latestEligibleActualPublicationDate") != "2025-11-24"
        or fdic.get("currentArchiveLinkDoesNotBackdateAvailability") is not True
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-policy-redesign-proposal-v1.json"
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
    ):
        raise DatasetValidationError("E14.7n policy-redesign inputs are invalid.")


def _validate_proposal(proposal: dict[str, Any], schema: dict[str, Any]) -> None:
    if (
        set(proposal) != set(schema.get("properties", {}))
        or not set(schema.get("required", [])).issubset(proposal)
        or proposal.get("proposalId") != "e14-post2005-policy-redesign-proposal-v1"
        or len(proposal.get("proposalItems", [])) != 2
        or proposal.get("governance", {}).get("proposalDoesNotAuthorizeAcquisition") is not True
    ):
        raise DatasetValidationError("E14.7n proposal violates the frozen schema.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7n {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write_raw(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14.7n output exists: {path}") from error
