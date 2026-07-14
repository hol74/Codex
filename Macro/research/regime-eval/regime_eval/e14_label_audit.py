from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .e13_loeo import _inner_dates


STATES = {"positive", "hard-negative", "ambiguous", "unlabeled"}


def write_e14_label_audit(
    taxonomy_path: str | Path,
    information_audit_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    contract_path: str | Path,
    output_path: str | Path,
) -> Path:
    taxonomy_file, taxonomy_bytes, taxonomy = _read_json(taxonomy_path, "E14 taxonomy v3")
    info_file, info_bytes, information = _read_json(information_audit_path, "E14 information audit")
    dataset = load_dataset(dataset_path)
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 label-audit contract")
    episodes, hard_negatives = _validate_taxonomy(taxonomy)
    _validate_contract(taxonomy_bytes, info_bytes, information, dataset.sha256, plan_bytes, contract)

    inner_keys, folds = _inner_dates(sorted(dataset.rows, key=lambda item: item["asOfDate"]), plan)
    mechanisms = contract["requiredMechanisms"]
    full_positive = [episode for episode in episodes if episode["financialState"] == "positive"]
    full_ambiguous = [episode for episode in episodes if episode["financialState"] == "ambiguous"]
    inner_positive = [episode for episode in full_positive if _observed(episode, inner_keys)]
    inner_hard_negative = [episode for episode in hard_negatives if _observed(episode, inner_keys)]

    mechanism_gaps = []
    for mechanism in mechanisms:
        full_count = sum(mechanism in episode["mechanisms"] for episode in full_positive)
        inner_count = sum(mechanism in episode["mechanisms"] for episode in inner_positive)
        negative_count = sum(mechanism in episode["mechanisms"] for episode in hard_negatives)
        mechanism_gaps.append({
            "mechanism": mechanism,
            "fullPositiveEpisodeCount": full_count,
            "innerPositiveEpisodeCount": inner_count,
            "hardNegativeEpisodeCount": negative_count,
            "additionalFullPositivesNeeded": max(0, int(contract["requirements"]["minimumFullPositiveEpisodesPerMechanism"]) - full_count),
            "additionalInnerPositivesNeeded": max(0, int(contract["requirements"]["minimumInnerPositiveEpisodesPerMechanism"]) - inner_count),
            "additionalHardNegativesNeeded": max(0, int(contract["requirements"]["minimumHardNegativeEpisodesPerMechanism"]) - negative_count),
        })

    month_states = _month_states(inner_keys, episodes, hard_negatives)
    state_counts = {state: sum(value == state for value in month_states.values()) for state in sorted(STATES)}
    requirements = contract["requirements"]
    checks = {
        "triStateTaxonomy": set(taxonomy["stateDefinitions"]) == STATES,
        "sourceCompleteness": True,
        "noImplicitNegatives": len(hard_negatives) == len(taxonomy["hardNegativeEpisodes"]),
        "minimumFullPositiveEpisodes": len(full_positive) >= int(requirements["minimumFullPositiveEpisodes"]),
        "minimumFullPositiveEpisodesPerMechanism": all(
            item["fullPositiveEpisodeCount"] >= int(requirements["minimumFullPositiveEpisodesPerMechanism"])
            for item in mechanism_gaps
        ),
        "minimumInnerPositiveEpisodesPerMechanism": all(
            item["innerPositiveEpisodeCount"] >= int(requirements["minimumInnerPositiveEpisodesPerMechanism"])
            for item in mechanism_gaps
        ),
        "minimumHardNegativeEpisodes": len(hard_negatives) >= int(requirements["minimumHardNegativeEpisodes"]),
        "minimumHardNegativeEpisodesPerMechanism": all(
            item["hardNegativeEpisodeCount"] >= int(requirements["minimumHardNegativeEpisodesPerMechanism"])
            for item in mechanism_gaps
        ),
        "outerFeatureRowsClosed": True,
    }
    passed = all(checks.values())
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14TriStateLabelAudit",
        "status": contract["passingDecision"] if passed else contract["failingDecision"],
        "inputs": {
            "taxonomyV3": _artifact(taxonomy_file, taxonomy_bytes),
            "informationAudit": _artifact(info_file, info_bytes),
            "dataset": _artifact(dataset.path, dataset.path.read_bytes()),
            "walkForwardPlan": _artifact(plan_file, plan_bytes),
            "contract": _artifact(contract_file, contract_bytes),
        },
        "protocol": {
            "purpose": "label-foundation-readiness-only",
            "datasetFieldsRead": ["asOfDate"],
            "outerFeatureRowCountUsed": 0,
            "candidateGenerated": False,
            "rankingProduced": False,
            "promotionAuthorized": False,
            "implicitNegativesCreated": 0,
        },
        "inventory": {
            "fullPositiveEpisodeCount": len(full_positive),
            "fullAmbiguousEpisodeCount": len(full_ambiguous),
            "fullHardNegativeEpisodeCount": len(hard_negatives),
            "innerPositiveEpisodeCount": len(inner_positive),
            "innerHardNegativeEpisodeCount": len(inner_hard_negative),
            "innerUniqueMonthCount": len(inner_keys),
            "innerMonthStateCounts": state_counts,
            "foldCount": len(folds),
        },
        "mechanismGaps": mechanism_gaps,
        "checks": checks,
        "failedChecks": sorted(key for key, value in checks.items() if not value),
        "decision": {
            "ready": passed,
            "status": contract["passingDecision"] if passed else contract["failingDecision"],
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": "E14.3 historical foundation feasibility and source audit",
        },
        "implementation": {
            "module": "regime_eval.e14_label_audit",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _validate_taxonomy(taxonomy: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if (
        not isinstance(taxonomy, dict) or taxonomy.get("schemaVersion") != 3
        or taxonomy.get("groundTruthId") != "us-financial-stress-tristate-v3"
        or set(taxonomy.get("stateDefinitions", {})) != STATES
        or "positive overrides hard-negative" not in str(taxonomy.get("monthResolutionPolicy"))
    ):
        raise DatasetValidationError("Unsupported E14 financial taxonomy v3.")
    sources = taxonomy.get("sources")
    episodes = taxonomy.get("episodes")
    hard_negatives = taxonomy.get("hardNegativeEpisodes")
    if not isinstance(sources, list) or not isinstance(episodes, list) or not isinstance(hard_negatives, list):
        raise DatasetValidationError("E14 taxonomy collections are invalid.")
    source_ids = {item.get("id") for item in sources}
    if None in source_ids or len(source_ids) != len(sources):
        raise DatasetValidationError("E14 taxonomy source ids are invalid.")
    episode_ids: set[str] = set()
    mechanisms = set(taxonomy.get("mechanisms", {}))
    for episode in [*episodes, *hard_negatives]:
        episode_id = episode.get("id")
        state = episode.get("financialState")
        assigned = episode.get("mechanisms")
        if (
            not isinstance(episode_id, str) or episode_id in episode_ids
            or state not in {"positive", "ambiguous", "hard-negative"}
            or not isinstance(assigned, list) or not set(assigned) <= mechanisms
            or not set(episode.get("sourceIds", [])) <= source_ids
            or date.fromisoformat(episode["firstMonth"]) > date.fromisoformat(episode["lastMonth"])
        ):
            raise DatasetValidationError("E14 taxonomy episode is invalid.")
        if state == "positive" and not assigned:
            raise DatasetValidationError("Positive E14 episodes require at least one mechanism.")
        if state == "ambiguous" and assigned:
            raise DatasetValidationError("Ambiguous E14 episodes cannot assert a financial mechanism.")
        episode_ids.add(episode_id)
    if any(item.get("financialState") != "hard-negative" for item in hard_negatives):
        raise DatasetValidationError("E14 hard-negative collection contains another state.")
    return episodes, hard_negatives


def _validate_contract(
    taxonomy_bytes: bytes, info_bytes: bytes, information: Any, dataset_sha: str,
    plan_bytes: bytes, contract: Any,
) -> None:
    actual = {
        "taxonomyV3Sha256": hashlib.sha256(taxonomy_bytes).hexdigest(),
        "informationAuditSha256": hashlib.sha256(info_bytes).hexdigest(),
        "datasetSha256": dataset_sha,
        "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
    }
    if (
        not isinstance(contract, dict) or contract.get("contractId") != "e14-label-audit-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("monthPrecedence") != ["positive", "hard-negative", "ambiguous", "unlabeled"]
        or "Forbidden" not in str(contract.get("implicitNegativePolicy"))
        or "forbidden" not in str(contract.get("outerOosPolicy"))
        or contract.get("candidateGenerationAuthorized") is not False
    ):
        raise DatasetValidationError("E14 label-audit contract is invalid.")
    if (
        information.get("artifactType") != "E14InformationAudit"
        or information.get("status") != "diagnostic-complete"
        or information.get("protocol", {}).get("outerTestRowCountUsed") != 0
    ):
        raise DatasetValidationError("E14 information audit is invalid.")


def _month_states(
    keys: list[str], episodes: list[dict[str, Any]], hard_negatives: list[dict[str, Any]]
) -> dict[str, str]:
    all_episodes = [*episodes, *hard_negatives]
    order = {"positive": 0, "hard-negative": 1, "ambiguous": 2, "unlabeled": 3}
    output = {}
    for key in keys:
        month = date.fromisoformat(key).replace(day=1)
        states = [
            episode["financialState"] for episode in all_episodes
            if date.fromisoformat(episode["firstMonth"]) <= month <= date.fromisoformat(episode["lastMonth"])
        ]
        output[key] = min(states or ["unlabeled"], key=order.__getitem__)
    return output


def _observed(episode: dict[str, Any], keys: list[str]) -> bool:
    first = date.fromisoformat(episode["firstMonth"])
    last = date.fromisoformat(episode["lastMonth"])
    return any(first <= date.fromisoformat(key).replace(day=1) <= last for key in keys)


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E14 label audit exists: '{destination}'.") from exc
    return destination
