from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


TAXONOMY_ID = "us-financial-stress-mechanism-aware-v4"
FOUNDATION_STATUS = "FOUNDATION_MERGE_READY_MORE_EVIDENCE_REQUIRED"
OUTPUT_STATUS = "TAXONOMY_V4_VERSIONED_MORE_HARD_NEGATIVES_REQUIRED"
MONTH_POLICY = (
    "Mechanism-month labels are authoritative and remain independent. Aggregate month state is a view "
    "using positive > hard-negative > ambiguous > unlabeled and cannot erase mixed mechanism states."
)


def write_e14_taxonomy_v4(
    contract_path: str | Path,
    taxonomy_v3_path: str | Path,
    foundation_proposal_path: str | Path,
    foundation_gate_audit_path: str | Path,
    proposal_schema_path: str | Path,
    taxonomy_schema_path: str | Path,
    label_audit_contract_path: str | Path,
    mechanism_contract_path: str | Path,
    taxonomy_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 taxonomy v4 contract")
    v3_file, v3_bytes, v3 = _read_json(taxonomy_v3_path, "financial taxonomy v3")
    proposal_file, proposal_bytes, proposal = _read_json(foundation_proposal_path, "foundation proposal")
    gate_file, gate_bytes, gate = _read_json(foundation_gate_audit_path, "foundation gate audit")
    proposal_schema_file, proposal_schema_bytes, proposal_schema = _read_json(
        proposal_schema_path, "foundation proposal schema"
    )
    taxonomy_schema_file, taxonomy_schema_bytes, taxonomy_schema = _read_json(
        taxonomy_schema_path, "taxonomy v4 schema"
    )
    label_contract_file, label_contract_bytes, label_contract = _read_json(
        label_audit_contract_path, "label audit contract"
    )
    mechanism_file, mechanism_bytes, mechanism_contract = _read_json(
        mechanism_contract_path, "mechanism contract"
    )
    _validate_inputs(
        contract,
        v3,
        proposal,
        gate,
        proposal_schema,
        taxonomy_schema,
        label_contract,
        mechanism_contract,
        v3_bytes,
        proposal_bytes,
        gate_bytes,
        proposal_schema_bytes,
        taxonomy_schema_bytes,
        label_contract_bytes,
        mechanism_bytes,
    )

    taxonomy_output = Path(taxonomy_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    if taxonomy_output.exists() or audit_output.exists():
        raise DatasetValidationError("Immutable E14 taxonomy v4 output already exists.")

    taxonomy = _materialize_taxonomy(v3, proposal, gate, contract, proposal_bytes, gate_bytes)
    coverage = _coverage(taxonomy, contract)
    conflicts = _same_mechanism_conflicts(taxonomy)
    proposal_rows_preserved = _proposal_rows_preserved(taxonomy, proposal)
    duplicate_ids = _duplicates(
        episode["id"] for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]
    )
    if coverage != proposal["coverage"] or conflicts or not proposal_rows_preserved or duplicate_ids:
        raise DatasetValidationError("E14 taxonomy v4 materialization violates the frozen foundation proposal.")

    taxonomy_raw = _json_bytes(taxonomy)
    report = {
        "schemaVersion": 1,
        "artifactType": "E14TaxonomyV4MaterializationAudit",
        "status": OUTPUT_STATUS,
        "inputs": {
            "materializationContract": _artifact(contract_file, contract_bytes),
            "taxonomyV3": _artifact(v3_file, v3_bytes),
            "foundationProposal": _artifact(proposal_file, proposal_bytes),
            "foundationGateAudit": _artifact(gate_file, gate_bytes),
            "proposalSchema": _artifact(proposal_schema_file, proposal_schema_bytes),
            "taxonomyV4Schema": _artifact(taxonomy_schema_file, taxonomy_schema_bytes),
            "labelAuditContract": _artifact(label_contract_file, label_contract_bytes),
            "mechanismContract": _artifact(mechanism_file, mechanism_bytes),
        },
        "output": _artifact(taxonomy_output, taxonomy_raw),
        "inventory": {
            "inheritedEpisodeCount": len(v3["episodes"]),
            "addedPositiveMechanismEpisodeCount": sum(
                item["state"] == "positive" for item in proposal["dossierLabels"]
            ),
            "addedHardNegativeMechanismEpisodeCount": sum(
                item["state"] == "hard-negative" for item in proposal["dossierLabels"]
            ),
            "taxonomyEpisodeCount": len(taxonomy["episodes"]),
            "taxonomyHardNegativeEntryCount": len(taxonomy["hardNegativeEpisodes"]),
            "foundationEvidenceCount": len(taxonomy["foundationEvidence"]),
            "independentPositiveEpisodeCount": coverage["combinedPositiveEpisodeCount"],
            "independentHardNegativeEpisodeCount": coverage["combinedHardNegativeEpisodeCount"],
            "sameMechanismMonthConflictCount": len(conflicts),
        },
        "coverage": coverage,
        "checks": {
            "taxonomyV3HashPreserved": hashlib.sha256(v3_file.read_bytes()).hexdigest()
            == contract["inputHashes"]["taxonomyV3Sha256"],
            "foundationGateAuthorizedMerge": True,
            "proposalCoveragePreserved": coverage == proposal["coverage"],
            "proposalMechanismMonthRowsPreserved": proposal_rows_preserved,
            "independentEventIdentityExplicit": all(
                episode.get("independentEventId")
                for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]
            ),
            "episodeIdsUnique": not duplicate_ids,
            "sameMechanismMonthStatesConsistent": not conflicts,
            "crossMechanismMixedStatesPreserved": True,
            "unlabeledNeverPromotedToHardNegative": True,
            "candidateGenerationClosed": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "existingTaxonomyMutated": False,
            "newTaxonomyVersionWritten": True,
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "candidateGenerated": False,
            "promotionPerformed": False,
        },
        "decision": {
            "taxonomyV4Ready": True,
            "positiveCoverageSufficient": coverage["positiveThresholdsSatisfied"],
            "hardNegativeCoverageSufficient": coverage["hardNegativeThresholdsSatisfied"],
            "additionalHardNegativeResearchRequired": True,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_taxonomy_v4",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    taxonomy_written = _write_new_bytes(taxonomy_output, taxonomy_raw, "E14 taxonomy v4")
    return taxonomy_written, _write_new_json(audit_output, report, "E14 taxonomy v4 audit")


def _validate_inputs(
    contract: Any,
    v3: Any,
    proposal: Any,
    gate: Any,
    proposal_schema: Any,
    taxonomy_schema: Any,
    label_contract: Any,
    mechanism_contract: Any,
    v3_bytes: bytes,
    proposal_bytes: bytes,
    gate_bytes: bytes,
    proposal_schema_bytes: bytes,
    taxonomy_schema_bytes: bytes,
    label_contract_bytes: bytes,
    mechanism_bytes: bytes,
) -> None:
    actual_hashes = {
        "taxonomyV3Sha256": hashlib.sha256(v3_bytes).hexdigest(),
        "foundationProposalSha256": hashlib.sha256(proposal_bytes).hexdigest(),
        "foundationGateAuditSha256": hashlib.sha256(gate_bytes).hexdigest(),
        "proposalSchemaSha256": hashlib.sha256(proposal_schema_bytes).hexdigest(),
        "taxonomyV4SchemaSha256": hashlib.sha256(taxonomy_schema_bytes).hexdigest(),
        "labelAuditContractSha256": hashlib.sha256(label_contract_bytes).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_bytes).hexdigest(),
    }
    policy = contract.get("materializationPolicy", {}) if isinstance(contract, dict) else {}
    authorization = contract.get("authorizationPolicy", {}) if isinstance(contract, dict) else {}
    required_policy = {
        "versioningMode": "create-new-file-never-mutate-v3",
        "proposalEntryGranularity": "one-entry-per-dossier-and-mechanism",
        "independentEventIdentity": "hypothesisId-for-proposal-id-for-inherited",
        "mechanismMonthStatesRemainIndependent": True,
        "crossMechanismMixedStatesAllowed": True,
        "sameMechanismMonthOpposingStatesForbidden": True,
        "unlabeledNeverBecomesHardNegative": True,
        "aggregateMonthStateIsViewOnly": True,
    }
    required_authorization = {
        "taxonomyV4MaterializationAuthorized": True,
        "taxonomyV3MutationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    proposal_artifact = gate.get("inputs", {}).get("foundationProposal", {})
    if (
        contract.get("contractId") != "e14-taxonomy-v4-materialization-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("requiredFoundationStatus") != FOUNDATION_STATUS
        or contract.get("requiredGroundTruthId") != "us-financial-stress-tristate-v3"
        or contract.get("outputGroundTruthId") != TAXONOMY_ID
        or contract.get("expectedInheritedEpisodeCount") != 8
        or contract.get("expectedProposalDossierCount") != 12
        or policy != required_policy
        or authorization != required_authorization
        or contract.get("expectedStatus") != OUTPUT_STATUS
        or v3.get("schemaVersion") != 3
        or v3.get("groundTruthId") != contract.get("requiredGroundTruthId")
        or len(v3.get("episodes", [])) != contract.get("expectedInheritedEpisodeCount")
        or proposal.get("artifactType") != "E14LabelFoundationProposal"
        or proposal.get("proposalId") != "e14-label-foundation-proposal-v1"
        or len(proposal.get("dossierLabels", [])) != contract.get("expectedProposalDossierCount")
        or gate.get("status") != contract.get("requiredFoundationStatus")
        or gate.get("decision", {}).get("foundationMergeAuthorized") is not True
        or gate.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or gate.get("decision", {}).get("groundTruthMutationAuthorizedInThisStep") is not False
        or gate.get("inventory", {}).get("sameMechanismMonthConflictCount") != 0
        or gate.get("inventory", {}).get("taxonomyMergeConflictCount") != 0
        or gate.get("coverage") != proposal.get("coverage")
        or proposal_artifact.get("sha256") != actual_hashes["foundationProposalSha256"]
        or proposal_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-label-foundation-proposal-v1.json"
        or taxonomy_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-financial-stress-taxonomy-v4.json"
        or taxonomy_schema.get("properties", {}).get("groundTruthId", {}).get("const") != TAXONOMY_ID
        or mechanism_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or label_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or any(
            label_contract.get("requirements", {}).get(key) != value
            for key, value in contract.get("coverageThresholds", {}).items()
        )
        or proposal.get("coverage", {}).get("positiveThresholdsSatisfied") is not True
        or proposal.get("coverage", {}).get("hardNegativeThresholdsSatisfied") is not False
    ):
        raise DatasetValidationError("E14 taxonomy v4 inputs or contract are invalid.")


def _materialize_taxonomy(
    v3: dict[str, Any],
    proposal: dict[str, Any],
    gate: dict[str, Any],
    contract: dict[str, Any],
    proposal_bytes: bytes,
    gate_bytes: bytes,
) -> dict[str, Any]:
    inherited_episodes = [_inherited_episode(item) for item in v3["episodes"]]
    inherited_negatives = [_inherited_episode(item) for item in v3["hardNegativeEpisodes"]]
    proposed = [_proposal_episode(item) for item in proposal["dossierLabels"]]
    positive = [item for item in proposed if item["financialState"] == "positive"]
    hard_negative = [item for item in proposed if item["financialState"] == "hard-negative"]
    all_episodes = inherited_episodes + positive
    all_negatives = inherited_negatives + hard_negative
    all_months = [item["firstMonth"] for item in all_episodes + all_negatives]
    all_last_months = [item["lastMonth"] for item in all_episodes + all_negatives]

    taxonomy = {
        "schemaVersion": 4,
        "groundTruthId": TAXONOMY_ID,
        "label": "US-relevant mechanism-aware financial stress with reviewed tri-state evidence",
        "geography": v3["geography"],
        "frequency": "monthly",
        "coverageFrom": min(all_months),
        "coverageTo": max([v3["coverageTo"], *all_last_months]),
        "derivedFrom": v3["groundTruthId"],
        "foundation": {
            "versionedAt": contract["frozenAt"],
            "proposalId": proposal["proposalId"],
            "proposalSha256": hashlib.sha256(proposal_bytes).hexdigest(),
            "gateStatus": gate["status"],
            "gateAuditSha256": hashlib.sha256(gate_bytes).hexdigest(),
            "sourceQueueSha256": proposal["sourceQueueSha256"],
        },
        "stateDefinitions": copy.deepcopy(v3["stateDefinitions"]),
        "monthResolutionPolicy": MONTH_POLICY,
        "mechanisms": copy.deepcopy(v3["mechanisms"]),
        "sources": copy.deepcopy(v3["sources"]),
        "episodes": sorted(all_episodes, key=_episode_key),
        "hardNegativeEpisodes": sorted(all_negatives, key=_episode_key),
        "foundationEvidence": copy.deepcopy(proposal["dossierLabels"]),
        "coverage": copy.deepcopy(proposal["coverage"]),
        "governance": {
            "independentEpisodeCountingKey": "independentEventId",
            "proposalEntryGranularity": "one-entry-per-dossier-and-mechanism",
            "taxonomyV3MutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "outerOosAuthorized": False,
            "additionalHardNegativeResearchRequired": True,
        },
        "limitations": copy.deepcopy(v3["limitations"]) + [
            "The v4 foundation is mechanism-aware: aggregate month state is a view and cannot replace mechanism-level labels.",
            "Multiple mechanism entries sharing an independentEventId count as one independent event for coverage.",
            "Hard-negative coverage remains below the frozen threshold; this taxonomy cannot authorize candidate generation.",
        ],
    }
    return taxonomy


def _inherited_episode(episode: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(episode)
    result["independentEventId"] = episode["id"]
    result["foundationOrigin"] = "inherited-v3"
    return result


def _proposal_episode(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["dossierId"],
        "name": item["hypothesisId"],
        "firstMonth": item["firstMonth"],
        "lastMonth": item["lastMonth"],
        "financialState": item["state"],
        "mechanisms": [item["mechanism"]],
        "sourceIds": [],
        "validationRole": "foundation-v4",
        "independentEventId": item["hypothesisId"],
        "foundationOrigin": "accepted-e14-dossier",
        "foundationEvidence": {
            "dossierId": item["dossierId"],
            "dossierSha256": item["dossierSha256"],
        },
    }


def _coverage(taxonomy: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    mechanisms = contract["requiredMechanisms"]
    positives: dict[str, set[str]] = {mechanism: set() for mechanism in mechanisms}
    negatives: dict[str, set[str]] = {mechanism: set() for mechanism in mechanisms}
    all_positive: set[str] = set()
    all_negative: set[str] = set()
    for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]:
        state = episode["financialState"]
        if state not in {"positive", "hard-negative"}:
            continue
        event_id = episode["independentEventId"]
        target = positives if state == "positive" else negatives
        (all_positive if state == "positive" else all_negative).add(event_id)
        for mechanism in episode["mechanisms"]:
            target[mechanism].add(event_id)
    thresholds = contract["coverageThresholds"]
    mechanism_coverage = [
        {
            "mechanism": mechanism,
            "combinedPositiveEpisodeCount": len(positives[mechanism]),
            "combinedHardNegativeEpisodeCount": len(negatives[mechanism]),
            "positiveThresholdSatisfied": len(positives[mechanism])
            >= thresholds["minimumFullPositiveEpisodesPerMechanism"],
            "hardNegativeThresholdSatisfied": len(negatives[mechanism])
            >= thresholds["minimumHardNegativeEpisodesPerMechanism"],
        }
        for mechanism in mechanisms
    ]
    positive_ok = len(all_positive) >= thresholds["minimumFullPositiveEpisodes"] and all(
        item["positiveThresholdSatisfied"] for item in mechanism_coverage
    )
    negative_ok = len(all_negative) >= thresholds["minimumHardNegativeEpisodes"] and all(
        item["hardNegativeThresholdSatisfied"] for item in mechanism_coverage
    )
    return {
        "combinedPositiveEpisodeCount": len(all_positive),
        "combinedHardNegativeEpisodeCount": len(all_negative),
        "mechanismCoverage": mechanism_coverage,
        "positiveThresholdsSatisfied": positive_ok,
        "hardNegativeThresholdsSatisfied": negative_ok,
        "coverageThresholdsSatisfied": positive_ok and negative_ok,
    }


def _same_mechanism_conflicts(taxonomy: dict[str, Any]) -> list[dict[str, Any]]:
    states: dict[tuple[str, str], set[str]] = defaultdict(set)
    for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]:
        if episode["financialState"] not in {"positive", "hard-negative"}:
            continue
        for month in _months(episode["firstMonth"], episode["lastMonth"]):
            for mechanism in episode["mechanisms"]:
                states[(month, mechanism)].add(episode["financialState"])
    return [
        {"month": key[0], "mechanism": key[1], "states": sorted(values)}
        for key, values in sorted(states.items())
        if len(values) > 1
    ]


def _proposal_rows_preserved(taxonomy: dict[str, Any], proposal: dict[str, Any]) -> bool:
    actual = set()
    for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]:
        if episode.get("foundationOrigin") != "accepted-e14-dossier":
            continue
        for month in _months(episode["firstMonth"], episode["lastMonth"]):
            actual.add((month, episode["mechanisms"][0], episode["financialState"], episode["id"]))
    expected = {
        (item["month"], item["mechanism"], item["state"], dossier_id)
        for item in proposal["monthlyMechanismLabels"]
        for dossier_id in item["dossierIds"]
    }
    return actual == expected


def _months(first: str, last: str) -> list[str]:
    start, end = date.fromisoformat(first), date.fromisoformat(last)
    values = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
    return values


def _episode_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return item["firstMonth"], item["lastMonth"], item["id"]


def _duplicates(values: Any) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_new_bytes(path: Path, payload: bytes, label: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{path}'.") from exc
    return path


def _write_new_json(path: Path, payload: dict[str, Any], label: str) -> Path:
    return _write_new_bytes(path, _json_bytes(payload), label)
