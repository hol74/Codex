from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "POST_2005_TAXONOMY_PROPOSAL_AWAITING_INDEPENDENT_REVIEW"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]


def write_e14_post2005_taxonomy_proposal(
    contract_path: str | Path,
    taxonomy_v5_path: str | Path,
    scope_feasibility_audit_path: str | Path,
    scope_plan_path: str | Path,
    source_evidence_path: str | Path,
    proposal_plan_path: str | Path,
    proposal_schema_path: str | Path,
    dossier_schema_path: str | Path,
    review_schema_path: str | Path,
    proposal_output_path: str | Path,
    dossier_output_dir: str | Path,
    queue_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path, Path]:
    labels = (
        "proposal contract", "taxonomy v5", "scope-feasibility audit",
        "scope plan", "source evidence", "proposal plan", "proposal schema",
        "dossier schema", "review schema",
    )
    paths = (
        contract_path, taxonomy_v5_path, scope_feasibility_audit_path,
        scope_plan_path, source_evidence_path, proposal_plan_path,
        proposal_schema_path, dossier_schema_path, review_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (
        (_, _, contract), (taxonomy_file, taxonomy_raw, taxonomy),
        (_, _, feasibility), (_, _, scope_plan), (_, _, source_evidence),
        (_, _, plan), (_, _, proposal_schema), (_, _, dossier_schema),
        (review_schema_file, review_schema_raw, review_schema),
    ) = artifacts
    hashes = {
        "taxonomyV5Sha256": _sha(artifacts[1][1]),
        "scopeFeasibilityAuditV1Sha256": _sha(artifacts[2][1]),
        "scopePlanV1Sha256": _sha(artifacts[3][1]),
        "sourceEvidenceV1Sha256": _sha(artifacts[4][1]),
        "proposalPlanV1Sha256": _sha(artifacts[5][1]),
        "proposalSchemaV1Sha256": _sha(artifacts[6][1]),
        "dossierSchemaV1Sha256": _sha(artifacts[7][1]),
        "reviewSchemaV2Sha256": _sha(artifacts[8][1]),
    }
    _validate_governance(
        contract, taxonomy, feasibility, scope_plan, source_evidence, plan,
        proposal_schema, dossier_schema, review_schema, hashes,
    )

    cutoff = date.fromisoformat(plan["cutoffInclusive"])
    positives = _scope_entries(taxonomy["episodes"], cutoff, "positive")
    inherited_negatives = _scope_entries(
        taxonomy["hardNegativeEpisodes"], cutoff, "hard-negative"
    )
    assertions = _assertions(plan)
    dossiers = _build_dossiers(plan, assertions)

    proposal_path = Path(proposal_output_path).resolve()
    dossier_dir = Path(dossier_output_dir).resolve()
    dossier_paths = [dossier_dir / f"{item['dossierId']}.json" for item in dossiers]
    queue_path = Path(queue_output_path).resolve()
    audit_path = Path(audit_output_path).resolve()
    outputs = [proposal_path, queue_path, audit_path, *dossier_paths]
    if any(path.exists() for path in outputs):
        raise DatasetValidationError("Immutable E14.7f output already exists.")

    dossier_raw = [_json_bytes(item) for item in dossiers]
    dossier_artifacts = [
        _artifact(path, raw) for path, raw in zip(dossier_paths, dossier_raw, strict=True)
    ]
    new_controls = [
        {
            "proposalEntryId": f"e14-post2005-control-{item['hypothesisId']}-v1",
            "independentEventId": item["hypothesisId"],
            "mechanism": item["mechanism"],
            "financialState": "hard-negative",
            "firstMonth": item["firstMonth"],
            "lastMonth": item["lastMonth"],
            "dossier": artifact,
            "reviewStatus": "awaiting-independent-review",
        }
        for item, artifact in zip(dossiers, dossier_artifacts, strict=True)
    ]
    proposal = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005FinancialStressTaxonomyProposal",
        "proposalId": plan["proposalId"],
        "proposedTaxonomyId": plan["proposedTaxonomyId"],
        "scopeId": plan["scopeId"],
        "cutoffInclusive": plan["cutoffInclusive"],
        "status": STATUS,
        "legacyTaxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
        "positiveEpisodeReferences": positives,
        "inheritedHardNegativeReferences": inherited_negatives,
        "proposedBankingHardNegativeControls": new_controls,
        "activation": {
            "active": False,
            "labelsAccepted": False,
            "independentReviewComplete": False,
            "sourceAcquisitionAuthorized": False,
            "featureFoundationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
        },
    }
    _validate_counts(contract, proposal)
    proposal_raw = _json_bytes(proposal)

    queue = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005IndependentReviewQueue",
        "queueId": plan["reviewQueueId"],
        "status": "AWAITING_INDEPENDENT_REVIEW",
        "taxonomyProposal": _artifact(proposal_path, proposal_raw),
        "reviewSchema": _artifact(review_schema_file, review_schema_raw),
        "dossierAuthor": plan["dossierAuthor"],
        "requirements": plan["independentReviewPolicy"],
        "dossiers": [
            {
                **artifact,
                "dossierId": dossier["dossierId"],
                "reviewStatus": "awaiting-independent-review",
            }
            for dossier, artifact in zip(dossiers, dossier_artifacts, strict=True)
        ],
        "receipts": [],
    }
    queue_raw = _json_bytes(queue)
    all_ids = _proposal_ids(proposal)
    legacy_ids = {
        item["independentEventId"]
        for item in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]
    }
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005TaxonomyProposalAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("proposalContract", "taxonomyV5", "scopeFeasibilityAuditV1",
                 "scopePlanV1", "sourceEvidenceV1", "proposalPlanV1",
                 "proposalSchemaV1", "dossierSchemaV1", "reviewSchemaV2"),
                artifacts,
            )
        },
        "outputs": {
            "taxonomyProposal": _artifact(proposal_path, proposal_raw),
            "independentReviewQueue": _artifact(queue_path, queue_raw),
            "dossiers": dossier_artifacts,
        },
        "inventory": {
            "positiveReferenceCount": len(positives),
            "inheritedHardNegativeReferenceCount": len(inherited_negatives),
            "newBankingControlCount": len(new_controls),
            "queuedDossierCount": len(dossiers),
            "independentReviewReceiptCount": 0,
        },
        "checks": {
            "allInputHashesExact": True,
            "proposalIdentifiersUnique": len(all_ids) == len(set(all_ids)),
            "proposalIdentifiersDoNotReuseLegacyEventIds": not set(all_ids) & legacy_ids,
            "dossiersHashBound": True,
            "queueHashBoundToProposalAndDossiers": True,
            "selfAcceptancePrevented": True,
            "taxonomyV5Unchanged": _sha(taxonomy_file.read_bytes()) == hashes["taxonomyV5Sha256"],
            "post2005ScopeInactive": True,
            "legacyE14Closed": True,
        },
        "protocol": {
            "metadataOnly": True,
            "seriesObservationDownloaded": False,
            "datasetRead": False,
            "loeoScoreRead": False,
            "outerFeatureRowCountUsed": 0,
            "taxonomyV5Mutated": False,
            "labelsAccepted": 0,
            "candidateGenerated": False,
            "candidateEvaluated": False,
        },
        "decision": {
            "proposalMaterialized": True,
            "independentReviewRequired": True,
            "post2005ScopeActivated": False,
            "taxonomyMutationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureFoundationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_post2005_taxonomy_proposal",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    if not all(audit["checks"].values()):
        raise DatasetValidationError("E14.7f proposal identity or immutability check failed.")

    for path, raw in zip(dossier_paths, dossier_raw, strict=True):
        _write_new(path, raw)
    _write_new(proposal_path, proposal_raw)
    _write_new(queue_path, queue_raw)
    _write_new(audit_path, _json_bytes(audit))
    return proposal_path, queue_path, audit_path


def _validate_governance(
    contract: dict[str, Any], taxonomy: dict[str, Any], feasibility: dict[str, Any],
    scope_plan: dict[str, Any], source_evidence: dict[str, Any], plan: dict[str, Any],
    proposal_schema: dict[str, Any], dossier_schema: dict[str, Any],
    review_schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    forbidden = (
        "post2005ScopeActivationAuthorized", "sourceAcquisitionAuthorized",
        "featureFoundationMaterializationAuthorized", "taxonomyMutationAuthorized",
        "candidateGenerationAuthorized", "candidateEvaluationAuthorized",
        "outerOosAuthorized", "promotionAuthorized",
    )
    auth = contract.get("authorizationPolicy", {})
    identity_policy = {
        "newProposalIdRequired": True,
        "newTaxonomyIdRequired": True,
        "newProposalEntryIdsRequired": True,
        "legacyEventIdsReferenceOnly": True,
        "taxonomyV5MustRemainByteIdentical": True,
    }
    review_policy = {
        "dossiersMustBeHashBound": True,
        "queueMustBeWriteOnce": True,
        "selfAcceptanceForbidden": True,
        "bothBankingControlsRequireIndependentReceipt": True,
        "proposalCannotActivateScope": True,
    }
    scope_candidates = {
        item["independentEventId"]: item
        for item in scope_plan.get("bankingHardNegativeCandidates", [])
    }
    blueprints = {
        item["hypothesisId"]: item
        for item in plan.get("bankingHardNegativeBlueprints", [])
    }
    known_sources = {
        item["sourceId"] for item in source_evidence.get("documentaryEvidence", [])
    } | {item["sourceId"] for item in source_evidence.get("sources", [])}
    assertion_sources = {
        item.get("sourceId") for item in plan.get("evidenceAssertions", [])
    }
    candidate_roster_exact = (
        set(scope_candidates) == set(blueprints)
        and all(
            blueprints[key].get("mechanism") == source.get("mechanism")
            and blueprints[key].get("firstMonth") == source.get("firstMonth")
            and blueprints[key].get("lastMonth") == source.get("lastMonth")
            for key, source in scope_candidates.items()
        )
    )
    invalid = (
        contract.get("contractId") != "e14-post2005-taxonomy-proposal-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or contract.get("identityPolicy") != identity_policy
        or contract.get("reviewPolicy") != review_policy
        or auth.get("taxonomyProposalMaterializationAuthorized") is not True
        or auth.get("independentReviewQueueWriteAuthorized") is not True
        or any(auth.get(key) is not False for key in forbidden)
        or taxonomy.get("schemaVersion") != 5
        or feasibility.get("status")
        != "POST_2005_SCOPE_FEASIBLE_TAXONOMY_PROPOSAL_PREREGISTRATION_AUTHORIZED"
        or feasibility.get("decision", {}).get("post2005ScopeActivated") is not False
        or scope_plan.get("scopeId") != "e14-post-2005-research-scope-proposal-v1"
        or source_evidence.get("networkPolicy")
        != "provider-metadata-only-no-series-observation-download"
        or plan.get("planId") != "e14-post2005-taxonomy-proposal-plan-v1"
        or plan.get("scopeId") != scope_plan.get("scopeId")
        or plan.get("cutoffInclusive") != "2006-01-01"
        or proposal_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-post2005-taxonomy-proposal-v1.json"
        or dossier_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
        or review_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or plan.get("independentReviewPolicy", {}).get("selfAcceptanceForbidden") is not True
        or plan.get("independentReviewPolicy", {}).get("minimumIndependentReviewers") != 1
        or not candidate_roster_exact
        or not assertion_sources <= known_sources
    )
    if invalid:
        raise DatasetValidationError("E14.7f inputs or governance are invalid.")


def _scope_entries(items: list[dict[str, Any]], cutoff: date, state: str) -> list[dict[str, Any]]:
    result = []
    for item in items:
        if date.fromisoformat(item["firstMonth"]) < cutoff or not item["mechanisms"]:
            continue
        original = item["independentEventId"]
        mechanism_key = "-and-".join(item["mechanisms"]) or "context-only"
        result.append({
            "proposalEntryId": f"e14-post2005-{state}-{original}-{mechanism_key}-v1",
            "legacyIndependentEventId": original,
            "mechanisms": item["mechanisms"],
            "financialState": state,
            "firstMonth": item["firstMonth"],
            "lastMonth": item["lastMonth"],
            "referenceStatus": "legacy-v5-label-referenced-not-copied",
        })
    return sorted(result, key=lambda item: item["proposalEntryId"])


def _assertions(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for item in plan.get("evidenceAssertions", []):
        try:
            date.fromisoformat(item["publishedAt"])
        except (KeyError, TypeError, ValueError) as error:
            raise DatasetValidationError("E14.7f evidence date is invalid.") from error
        if (
            item.get("id") in result
            or item.get("role") not in {
                "official-narrative", "quantitative-observation", "counterevidence"
            }
            or not str(item.get("locator", "")).startswith("https://")
            or len(item.get("summary", "")) < 40
        ):
            raise DatasetValidationError("E14.7f evidence assertion is invalid.")
        result[item["id"]] = item
    return result


def _build_dossiers(plan: dict[str, Any], assertions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    dossiers = []
    for blueprint in plan.get("bankingHardNegativeBlueprints", []):
        evidence = [assertions[item] for item in blueprint.get("evidenceIds", [])]
        counters = [assertions[item] for item in blueprint.get("counterEvidenceIds", [])]
        if (
            blueprint.get("mechanism") != "banking-credit"
            or blueprint.get("proposedState") != "hard-negative"
            or len(evidence) < 2 or not counters
            or len({item["independenceGroup"] for item in evidence}) < 2
            or not {"official-narrative", "quantitative-observation"}
            <= {item["role"] for item in evidence}
            or any(item["role"] != "counterevidence" for item in counters)
            or len(blueprint.get("boundaryRationale", "")) < 80
        ):
            raise DatasetValidationError("E14.7f dossier blueprint is invalid.")
        dossiers.append({
            "schemaVersion": 1,
            "dossierId": blueprint["dossierId"],
            "hypothesisId": blueprint["hypothesisId"],
            "mechanism": "banking-credit",
            "proposedState": "hard-negative",
            "firstMonth": blueprint["firstMonth"],
            "lastMonth": blueprint["lastMonth"],
            "boundaryRationale": blueprint["boundaryRationale"],
            "affirmativeOrderlyEvidence": True,
            "evidenceItems": [_evidence_payload(item) for item in evidence],
            "counterEvidence": [_evidence_payload(item) for item in counters],
            "exclusionChecks": {
                "outerOosUsed": False,
                "modelPredictionUsedAsLabel": False,
                "absenceTreatedAsEvidence": False,
                "methodologyRegimeRecorded": True,
                "nberOverlapReviewed": True,
            },
            "adjudicationStatus": "reviewed",
            "reviewers": [plan["dossierAuthor"]],
        })
    if len(dossiers) != 2 or len({item["hypothesisId"] for item in dossiers}) != 2:
        raise DatasetValidationError("E14.7f requires two independent banking dossiers.")
    return sorted(dossiers, key=lambda item: item["dossierId"])


def _evidence_payload(item: dict[str, Any]) -> dict[str, Any]:
    payload = {key: item[key] for key in (
        "sourceId", "provider", "independenceGroup", "publishedAt", "role",
        "locator", "summary",
    )}
    payload["contentSha256"] = _sha(f"{item['locator']}\n{item['summary']}".encode("utf-8"))
    return payload


def _validate_counts(contract: dict[str, Any], proposal: dict[str, Any]) -> None:
    positive = Counter()
    negative = Counter()
    for item in proposal["positiveEpisodeReferences"]:
        positive.update(item["mechanisms"])
    for item in proposal["inheritedHardNegativeReferences"]:
        negative.update(item["mechanisms"])
    for item in proposal["proposedBankingHardNegativeControls"]:
        negative.update([item["mechanism"]])
    if (
        dict(positive) != contract["expectedPositiveEpisodeCounts"]
        or dict(negative) != contract["expectedHardNegativeEpisodeCounts"]
        or len(proposal["proposedBankingHardNegativeControls"])
        != contract["expectedNewBankingDossierCount"]
    ):
        raise DatasetValidationError("E14.7f proposal coverage does not match the frozen contract.")


def _proposal_ids(proposal: dict[str, Any]) -> list[str]:
    return [
        *[item["proposalEntryId"] for item in proposal["positiveEpisodeReferences"]],
        *[item["proposalEntryId"] for item in proposal["inheritedHardNegativeReferences"]],
        *[item["proposalEntryId"] for item in proposal["proposedBankingHardNegativeControls"]],
    ]


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        return file, raw, json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7f {label} is not valid UTF-8 JSON: {file}") from error


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
        raise DatasetValidationError(f"Immutable E14.7f output already exists: {path}") from error
