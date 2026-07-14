from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


PROPOSAL_POLICY = (
    "Mechanism-month labels remain independent; aggregate state uses positive > hard-negative > "
    "ambiguous > unlabeled without erasing mechanism detail."
)
ACCEPTED_STATUSES = {
    "accept-by-independent-receipt",
    "accept-by-targeted-independent-receipt",
}


def write_e14_label_foundation_gate(
    contract_path: str | Path,
    reviewed_queue_path: str | Path,
    targeted_ingestion_audit_path: str | Path,
    taxonomy_path: str | Path,
    dossier_schema_path: str | Path,
    proposal_schema_path: str | Path,
    label_audit_contract_path: str | Path,
    mechanism_contract_path: str | Path,
    positive_dossier_dir: str | Path,
    hard_negative_dossier_dir: str | Path,
    revised_dossier_dir: str | Path,
    proposal_output_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 label foundation contract")
    queue_file, queue_bytes, queue = _read_json(reviewed_queue_path, "E14 reviewed queue v5")
    audit_file, audit_bytes, audit = _read_json(targeted_ingestion_audit_path, "E14 targeted ingestion audit")
    taxonomy_file, taxonomy_bytes, taxonomy = _read_json(taxonomy_path, "financial taxonomy v3")
    dossier_schema_file, dossier_schema_bytes, dossier_schema = _read_json(dossier_schema_path, "dossier schema")
    proposal_schema_file, proposal_schema_bytes, proposal_schema = _read_json(proposal_schema_path, "proposal schema")
    label_contract_file, label_contract_bytes, label_contract = _read_json(
        label_audit_contract_path, "label audit contract"
    )
    mechanism_file, mechanism_bytes, mechanism_contract = _read_json(
        mechanism_contract_path, "mechanism contract"
    )
    _validate_inputs(
        contract, queue, audit, taxonomy, dossier_schema, proposal_schema, label_contract,
        mechanism_contract, queue_bytes, audit_bytes, taxonomy_bytes, dossier_schema_bytes,
        proposal_schema_bytes, label_contract_bytes, mechanism_bytes,
    )
    dossiers = _load_accepted_dossiers(
        queue, positive_dossier_dir, hard_negative_dossier_dir, revised_dossier_dir
    )

    proposal_path = Path(proposal_output_path).resolve()
    output = Path(output_path).resolve()
    if proposal_path.exists() or output.exists():
        raise DatasetValidationError("Immutable E14 label foundation output already exists.")

    dossier_labels = [_dossier_label(dossier, manifest) for dossier, manifest in dossiers]
    monthly = _monthly_mechanism_labels(dossier_labels)
    proposal_conflicts = _conflicts(monthly)
    existing_monthly = _taxonomy_monthly_labels(taxonomy)
    merge_conflicts = _merge_conflicts(monthly, existing_monthly)
    aggregate = _aggregate_monthly_labels(monthly, contract["monthPrecedence"])
    coverage = _coverage(taxonomy, dossier_labels, contract)
    required = set(contract["requiredMechanisms"])
    positive_mechanisms = {item["mechanism"] for item in dossier_labels if item["state"] == "positive"}
    negative_mechanisms = {item["mechanism"] for item in dossier_labels if item["state"] == "hard-negative"}
    structural_ready = not proposal_conflicts and not merge_conflicts and positive_mechanisms == required \
        and negative_mechanisms == required

    proposal = {
        "schemaVersion": 1,
        "artifactType": "E14LabelFoundationProposal",
        "proposalId": "e14-label-foundation-proposal-v1",
        "sourceQueueSha256": hashlib.sha256(queue_bytes).hexdigest(),
        "monthResolutionPolicy": PROPOSAL_POLICY,
        "dossierLabels": dossier_labels,
        "monthlyMechanismLabels": monthly,
        "aggregateMonthlyLabels": aggregate,
        "coverage": coverage,
    }
    proposal_written = _write_new_json(proposal_path, proposal, "E14 label foundation proposal")

    mixed_months = _mixed_mechanism_months(monthly)
    status = (
        "FOUNDATION_CONFLICTS_BLOCK_MERGE" if not structural_ready
        else "FOUNDATION_MERGE_READY" if coverage["coverageThresholdsSatisfied"]
        else "FOUNDATION_MERGE_READY_MORE_EVIDENCE_REQUIRED"
    )
    report = {
        "schemaVersion": 1,
        "artifactType": "E14LabelFoundationGateAudit",
        "status": status,
        "inputs": {
            "gateContract": _artifact(contract_file, contract_bytes),
            "reviewedQueueV5": _artifact(queue_file, queue_bytes),
            "targetedIngestionAudit": _artifact(audit_file, audit_bytes),
            "taxonomyV3": _artifact(taxonomy_file, taxonomy_bytes),
            "dossierSchema": _artifact(dossier_schema_file, dossier_schema_bytes),
            "proposalSchema": _artifact(proposal_schema_file, proposal_schema_bytes),
            "labelAuditContract": _artifact(label_contract_file, label_contract_bytes),
            "mechanismContract": _artifact(mechanism_file, mechanism_bytes),
            "foundationProposal": _artifact(proposal_written, proposal_written.read_bytes()),
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWrittenToGroundTruth": 0,
            "candidateGenerated": False,
            "existingTaxonomyMutated": False,
            "implicitNegativesCreated": 0,
            "proposalOnly": True,
        },
        "inventory": {
            "acceptedDossierCount": len(dossier_labels),
            "positiveDossierCount": sum(item["state"] == "positive" for item in dossier_labels),
            "hardNegativeDossierCount": sum(item["state"] == "hard-negative" for item in dossier_labels),
            "monthlyMechanismLabelCount": len(monthly),
            "aggregateMonthCount": len(aggregate),
            "mixedMechanismMonthCount": len(mixed_months),
            "sameMechanismMonthConflictCount": len(proposal_conflicts),
            "taxonomyMergeConflictCount": len(merge_conflicts),
        },
        "mixedMechanismMonths": mixed_months,
        "sameMechanismMonthConflicts": proposal_conflicts,
        "taxonomyMergeConflicts": merge_conflicts,
        "coverage": coverage,
        "checks": {
            "allTwelveDossiersIndependentlyAccepted": len(dossier_labels) == 12,
            "allQueueHashesRevalidated": True,
            "sameMechanismMonthStatesConsistent": not proposal_conflicts,
            "crossMechanismMixedStatesPreserved": True,
            "existingTaxonomyMergeConflictFree": not merge_conflicts,
            "allMechanismsHavePositiveDossier": positive_mechanisms == required,
            "allMechanismsHaveHardNegativeDossier": negative_mechanisms == required,
            "unlabeledNeverPromotedToHardNegative": True,
            "duplicateEventMechanismsNotCountedAsIndependentEpisodes": True,
            "groundTruthUnchanged": True,
            "outerOosClosed": True,
        },
        "decision": {
            "foundationProposalValid": structural_ready,
            "foundationMergeAuthorized": structural_ready,
            "coverageSufficientForCandidateGeneration": coverage["coverageThresholdsSatisfied"],
            "additionalHardNegativeResearchRequired": not coverage["hardNegativeThresholdsSatisfied"],
            "groundTruthMutationAuthorizedInThisStep": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": (
                "Resolve label-foundation conflicts before any merge" if not structural_ready
                else "E14.4d version taxonomy v4 from the proposal and continue hard-negative research"
            ),
        },
        "implementation": {
            "module": "regime_eval.e14_label_foundation_gate",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return proposal_written, _write_new_json(output, report, "E14 label foundation gate audit")


def _validate_inputs(
    contract: Any, queue: Any, audit: Any, taxonomy: Any, dossier_schema: Any,
    proposal_schema: Any, label_contract: Any, mechanism_contract: Any,
    queue_bytes: bytes, audit_bytes: bytes, taxonomy_bytes: bytes,
    dossier_schema_bytes: bytes, proposal_schema_bytes: bytes, label_contract_bytes: bytes,
    mechanism_bytes: bytes,
) -> None:
    actual = {
        "reviewedQueueV5Sha256": hashlib.sha256(queue_bytes).hexdigest(),
        "targetedIngestionAuditSha256": hashlib.sha256(audit_bytes).hexdigest(),
        "taxonomyV3Sha256": hashlib.sha256(taxonomy_bytes).hexdigest(),
        "dossierSchemaSha256": hashlib.sha256(dossier_schema_bytes).hexdigest(),
        "proposalSchemaSha256": hashlib.sha256(proposal_schema_bytes).hexdigest(),
        "labelAuditContractSha256": hashlib.sha256(label_contract_bytes).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_bytes).hexdigest(),
    }
    conflicts = contract.get("conflictPolicy", {}) if isinstance(contract, dict) else {}
    authorizations = contract.get("authorizationPolicy", {}) if isinstance(contract, dict) else {}
    queue_statuses = [item.get("reviewStatus") for item in queue.get("dossiers", [])]
    if (
        contract.get("contractId") != "e14-label-foundation-gate-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("readinessDecision") != "READY_TO_BUILD_LABEL_FOUNDATION_PROPOSAL"
        or contract.get("expectedAcceptedDossierCount") != 12
        or not all(conflicts.values()) or not all(authorizations.values())
        or contract.get("monthPrecedence") != ["positive", "hard-negative", "ambiguous", "unlabeled"]
        or queue.get("status") != "REVIEW_COMPLETE_ALL_ACCEPTED"
        or len(queue_statuses) != 12 or any(status not in ACCEPTED_STATUSES for status in queue_statuses)
        or audit.get("status") != "READY_FOR_LABEL_FOUNDATION_GATE"
        or audit.get("inventory", {}).get("totalAcceptedCount") != 12
        or taxonomy.get("groundTruthId") != "us-financial-stress-tristate-v3"
        or dossier_schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
        or proposal_schema.get("$id") != "https://macro-regime.local/schemas/e14-label-foundation-proposal-v1.json"
        or label_contract.get("monthPrecedence") != contract.get("monthPrecedence")
        or any(
            label_contract.get("requirements", {}).get(key) != value
            for key, value in contract.get("coverageThresholds", {}).items()
        )
        or mechanism_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or label_contract.get("candidateGenerationAuthorized") is not False
    ):
        raise DatasetValidationError("E14 label foundation inputs or contract are invalid.")


def _load_accepted_dossiers(
    queue: dict[str, Any], positive_dir: str | Path, hard_negative_dir: str | Path,
    revised_dir: str | Path,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    roots = [Path(path).resolve() for path in (positive_dir, hard_negative_dir, revised_dir)]
    result = []
    for manifest in queue["dossiers"]:
        matches = []
        for root in roots:
            path = root / manifest["fileName"]
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == manifest["sha256"]:
                matches.append(path)
        if len(matches) != 1:
            raise DatasetValidationError("E14 accepted dossier is missing, duplicated or hash-invalid.")
        raw = matches[0].read_bytes()
        dossier = json.loads(raw)
        if (
            len(raw) != manifest["sizeBytes"] or dossier.get("dossierId") != manifest["dossierId"]
            or dossier.get("adjudicationStatus") != "reviewed"
            or dossier.get("proposedState") not in {"positive", "hard-negative"}
        ):
            raise DatasetValidationError("E14 accepted dossier content is invalid.")
        result.append((dossier, manifest))
    return sorted(result, key=lambda pair: pair[0]["dossierId"])


def _dossier_label(dossier: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "dossierId": dossier["dossierId"],
        "dossierSha256": manifest["sha256"],
        "hypothesisId": dossier["hypothesisId"],
        "mechanism": dossier["mechanism"],
        "state": dossier["proposedState"],
        "firstMonth": dossier["firstMonth"],
        "lastMonth": dossier["lastMonth"],
    }


def _months(first: str, last: str) -> list[str]:
    start, end = date.fromisoformat(first), date.fromisoformat(last)
    if start.day != 1 or end.day != 1 or start > end:
        raise DatasetValidationError("E14 dossier month boundary is invalid.")
    values = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
    return values


def _monthly_mechanism_labels(dossiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for item in dossiers:
        for month in _months(item["firstMonth"], item["lastMonth"]):
            groups[(month, item["mechanism"], item["state"])].append(item["dossierId"])
    return [
        {"month": key[0], "mechanism": key[1], "state": key[2], "dossierIds": sorted(ids)}
        for key, ids in sorted(groups.items())
    ]


def _conflicts(monthly: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for item in monthly:
        groups[(item["month"], item["mechanism"])].add(item["state"])
    return [
        {"month": key[0], "mechanism": key[1], "states": sorted(states)}
        for key, states in sorted(groups.items()) if len(states) > 1
    ]


def _taxonomy_monthly_labels(taxonomy: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]:
        state = episode["financialState"]
        for mechanism in episode.get("mechanisms", []):
            for month in _months(episode["firstMonth"], episode["lastMonth"]):
                rows.append({"month": month, "mechanism": mechanism, "state": state, "episodeId": episode["id"]})
    return rows


def _merge_conflicts(proposal: list[dict[str, Any]], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proposed = {(item["month"], item["mechanism"]): item["state"] for item in proposal}
    conflicts = []
    for item in existing:
        state = proposed.get((item["month"], item["mechanism"]))
        if state is not None and state != item["state"]:
            conflicts.append({
                "month": item["month"], "mechanism": item["mechanism"],
                "proposalState": state, "taxonomyState": item["state"], "episodeId": item["episodeId"],
            })
    return sorted(conflicts, key=lambda item: (item["month"], item["mechanism"], item["episodeId"]))


def _aggregate_monthly_labels(monthly: list[dict[str, Any]], precedence: list[str]) -> list[dict[str, Any]]:
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in monthly:
        by_month[item["month"]].append(item)
    rank = {state: index for index, state in enumerate(precedence)}
    return [
        {
            "month": month,
            "state": min((item["state"] for item in rows), key=lambda state: rank[state]),
            "mechanismStates": [
                {"mechanism": item["mechanism"], "state": item["state"]}
                for item in sorted(rows, key=lambda row: (row["mechanism"], row["state"]))
            ],
        }
        for month, rows in sorted(by_month.items())
    ]


def _mixed_mechanism_months(monthly: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in monthly:
        groups[item["month"]].append({"mechanism": item["mechanism"], "state": item["state"]})
    return [
        {"month": month, "mechanismStates": sorted(rows, key=lambda row: row["mechanism"])}
        for month, rows in sorted(groups.items()) if len({row["state"] for row in rows}) > 1
    ]


def _coverage(taxonomy: dict[str, Any], dossiers: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    mechanisms = contract["requiredMechanisms"]
    positive: dict[str, set[str]] = {mechanism: set() for mechanism in mechanisms}
    negative: dict[str, set[str]] = {mechanism: set() for mechanism in mechanisms}
    all_positive, all_negative = set(), set()
    for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]:
        state = episode["financialState"]
        if state not in {"positive", "hard-negative"}:
            continue
        event_id = f"taxonomy:{episode['id']}"
        (all_positive if state == "positive" else all_negative).add(event_id)
        target = positive if state == "positive" else negative
        for mechanism in episode["mechanisms"]:
            target[mechanism].add(event_id)
    for dossier in dossiers:
        event_id = f"proposal:{dossier['hypothesisId']}"
        target = positive if dossier["state"] == "positive" else negative
        (all_positive if dossier["state"] == "positive" else all_negative).add(event_id)
        target[dossier["mechanism"]].add(event_id)
    thresholds = contract["coverageThresholds"]
    mechanism_coverage = []
    for mechanism in mechanisms:
        mechanism_coverage.append({
            "mechanism": mechanism,
            "combinedPositiveEpisodeCount": len(positive[mechanism]),
            "combinedHardNegativeEpisodeCount": len(negative[mechanism]),
            "positiveThresholdSatisfied": len(positive[mechanism]) >= thresholds["minimumFullPositiveEpisodesPerMechanism"],
            "hardNegativeThresholdSatisfied": len(negative[mechanism]) >= thresholds["minimumHardNegativeEpisodesPerMechanism"],
        })
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


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new_json(path: str | Path, payload: dict[str, Any], label: str) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{destination}'.") from exc
    return destination
