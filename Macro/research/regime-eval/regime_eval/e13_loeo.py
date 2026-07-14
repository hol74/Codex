from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from statistics import fmean
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .dimensional_baseline import _add_years
from .ground_truth import validate_recession_truth
from .metrics import binary_metrics
from .stress import validate_stress_truth


FINANCIAL_CODES = (
    "VIX_MONTHLY_MAX",
    "SPY_MONTHLY_MAX_DRAWDOWN",
    "HYG_MONTHLY_MAX_DRAWDOWN",
    "HY_OAS",
)
RECESSION_CODES = ("SAHM", "INDPRO_YOY", "YC_10Y2Y")


def write_e13_loeo_report(
    dataset_path: str | Path,
    plan_path: str | Path,
    stress_truth_path: str | Path,
    recession_truth_path: str | Path,
    protocol_path: str | Path,
    manifest_path: str | Path,
    foundation_lock_path: str | Path,
    evaluation_contract_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    stress_file, stress_bytes, stress = _read_json(stress_truth_path, "stress truth")
    recession_file, recession_bytes, recession = _read_json(recession_truth_path, "recession truth")
    protocol_file, protocol_bytes, protocol = _read_json(protocol_path, "E13 protocol")
    manifest_file, manifest_bytes, manifest = _read_json(manifest_path, "E13 generated manifest")
    lock_file, lock_bytes, lock = _read_json(foundation_lock_path, "E12 foundation lock")
    contract_file, contract_bytes, contract = _read_json(evaluation_contract_path, "E13 LOEO contract")
    _, stress_episodes = validate_stress_truth(stress)
    recession_periods = validate_recession_truth(recession)
    _validate_contract(
        dataset.sha256, plan_bytes, protocol_bytes, protocol, manifest_bytes, manifest,
        lock_bytes, lock, contract,
    )

    all_rows = sorted(dataset.rows, key=lambda item: item["asOfDate"])
    inner_keys, fold_reports = _inner_dates(all_rows, plan)
    inner_set = set(inner_keys)
    financial_episodes = _financial_episode_inventory(inner_keys, stress_episodes)
    recession_episodes = _recession_episode_inventory(inner_keys, recession_periods)
    curated_controls = _financial_controls(inner_keys, stress_episodes)

    financial_candidates = []
    recession_candidates = []
    for candidate in manifest["candidates"]:
        if candidate["task"] == "financial-stress-signal":
            scores = {
                row["asOfDate"]: _financial_score(row, candidate["parameters"]["aggregator"])
                for row in all_rows if row["asOfDate"] in inner_set
            }
            financial_candidates.append(
                _evaluate_financial_candidate(candidate, inner_keys, scores, financial_episodes, curated_controls)
            )
        else:
            all_scores = _recession_scores(all_rows, candidate["parameters"]["aggregator"])
            scores = {key: all_scores[key] for key in inner_keys}
            recession_candidates.append(
                _evaluate_recession_candidate(candidate, inner_keys, scores, recession_episodes)
            )

    payload = {
        "reportVersion": 1,
        "reportType": "E13LeaveOneEpisodeOutEvaluation",
        "status": "evaluated-no-shortlist",
        "inputs": {
            "dataset": _artifact(dataset.path, dataset.path.read_bytes()),
            "walkForwardPlan": _artifact(plan_file, plan_bytes),
            "stressGroundTruth": _artifact(stress_file, stress_bytes),
            "recessionGroundTruth": _artifact(recession_file, recession_bytes),
            "protocol": _artifact(protocol_file, protocol_bytes),
            "generatedManifest": _artifact(manifest_file, manifest_bytes),
            "foundationLock": _artifact(lock_file, lock_bytes),
            "evaluationContract": _artifact(contract_file, contract_bytes),
        },
        "protocol": {
            "scope": "nested-inner-validation-only",
            "method": "leave-one-episode-out-within-inner-validation",
            "thresholdSelection": "other episodes plus curated non-financial controls; never held-out labels",
            "minimumEpisodes": contract["minimumObservableEpisodesPerTask"],
            "outerTestRowCountUsed": 0,
            "shortlistProduced": False,
        },
        "coverage": {
            "foldCount": len(fold_reports),
            "uniqueInnerRowCount": len(inner_keys),
            "from": inner_keys[0],
            "to": inner_keys[-1],
            "financialEpisodeCount": len(financial_episodes),
            "recessionEpisodeCount": len(recession_episodes),
            "financialControlMonthCount": len(curated_controls),
        },
        "episodeInventory": {
            "financialStress": financial_episodes,
            "recession": recession_episodes,
        },
        "tasks": {
            "financial-stress-signal": {
                "status": "LOEO_COMPLETE" if len(financial_episodes) >= 3 else "INSUFFICIENT_EPISODES",
                "candidateCount": len(financial_candidates),
                "candidates": financial_candidates,
            },
            "recession-signal": {
                "status": "LOEO_COMPLETE" if len(recession_episodes) >= 3 else "INSUFFICIENT_EPISODES",
                "candidateCount": len(recession_candidates),
                "candidates": recession_candidates,
            },
        },
        "folds": fold_reports,
        "implementation": {
            "module": "regime_eval.e13_loeo",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def apply_persistence(scores: list[float], threshold: float, entry_months: int, recovery_months: int) -> list[bool]:
    active = False
    above = below = 0
    output = []
    for score in scores:
        if score >= threshold:
            above += 1
            below = 0
        else:
            below += 1
            above = 0
        if not active and above >= entry_months:
            active = True
        elif active and below >= recovery_months:
            active = False
        output.append(active)
    return output


def _evaluate_financial_candidate(
    candidate: dict[str, Any],
    keys: list[str],
    scores: dict[str, float],
    episodes: list[dict[str, Any]],
    controls: list[str],
) -> dict[str, Any]:
    parameters = candidate["parameters"]
    if len(episodes) < 3:
        return _ineligible(candidate, len(episodes))
    episode_months = {item["episodeId"]: set(item["observedMonths"]) for item in episodes}
    leaveouts = []
    for held_out in episodes:
        held_id = held_out["episodeId"]
        train_positive = sorted(set().union(*(
            months for episode_id, months in episode_months.items() if episode_id != held_id
        )))
        threshold, training = _select_threshold(
            keys, scores, train_positive, controls, parameters
        )
        states = _states(keys, scores, threshold, parameters)
        held_months = held_out["observedMonths"]
        held_actual = {key: True for key in held_months}
        held_predicted = {key: states[key] for key in held_months}
        held_metrics = binary_metrics(held_actual, held_predicted)
        control_fp = sum(states[key] for key in controls)
        leaveouts.append({
            "heldOutEpisodeId": held_id,
            "heldOutMonthCount": len(held_months),
            "selectedThreshold": threshold,
            "trainingMetrics": training,
            "heldOutHit": any(held_predicted.values()),
            "heldOutRecall": held_metrics["recall"],
            "controlFalsePositiveRate": round(control_fp / len(controls), 8) if controls else None,
        })
    recalls = [float(item["heldOutRecall"]) for item in leaveouts if item["heldOutRecall"] is not None]
    thresholds = [float(item["selectedThreshold"]) for item in leaveouts]
    return {
        "candidateId": candidate["candidateId"],
        "task": candidate["task"],
        "status": "LOEO_EVALUATED",
        "parameters": parameters,
        "complexityScore": _complexity(parameters),
        "episodeCount": len(episodes),
        "leaveouts": leaveouts,
        "aggregate": {
            "episodeHitRate": round(sum(item["heldOutHit"] for item in leaveouts) / len(leaveouts), 8),
            "meanEpisodeRecall": round(fmean(recalls), 8),
            "worstEpisodeRecall": round(min(recalls), 8),
            "meanControlFalsePositiveRate": round(fmean(
                float(item["controlFalsePositiveRate"]) for item in leaveouts
                if item["controlFalsePositiveRate"] is not None
            ), 8) if controls else None,
            "thresholdRange": round(max(thresholds) - min(thresholds), 8),
        },
    }


def _evaluate_recession_candidate(
    candidate: dict[str, Any], keys: list[str], scores: dict[str, float], episodes: list[dict[str, Any]]
) -> dict[str, Any]:
    del keys, scores
    if len(episodes) < 3:
        return _ineligible(candidate, len(episodes))
    raise DatasetValidationError("E13 recession LOEO implementation requires a foundation with at least three episodes.")


def _ineligible(candidate: dict[str, Any], episode_count: int) -> dict[str, Any]:
    return {
        "candidateId": candidate["candidateId"],
        "task": candidate["task"],
        "status": "INSUFFICIENT_EPISODES",
        "parameters": candidate["parameters"],
        "episodeCount": episode_count,
        "requiredEpisodeCount": 3,
        "reason": "LOEO cannot estimate cross-episode generalization with fewer than three observable episodes.",
        "leaveouts": [],
        "aggregate": None,
    }


def _select_threshold(
    keys: list[str], scores: dict[str, float], positives: list[str], controls: list[str], parameters: dict[str, Any]
) -> tuple[float, dict[str, Any]]:
    universe = sorted(set(positives) | set(controls))
    if not positives or not controls:
        raise DatasetValidationError("E13 LOEO threshold selection requires positive episodes and curated controls.")
    best: tuple[tuple[float, float, float, float], float, dict[str, Any]] | None = None
    for threshold in parameters["thresholdCandidates"]:
        states = _states(keys, scores, float(threshold), parameters)
        actual = {key: key in positives for key in universe}
        predicted = {key: states[key] for key in universe}
        metrics = binary_metrics(actual, predicted)
        f1 = float(metrics["f1"] or 0.0)
        recall = float(metrics["recall"] or 0.0)
        precision = float(metrics["precision"] or 0.0)
        rank = (f1, recall, precision, -abs(float(threshold) - 0.5))
        if best is None or rank > best[0]:
            best = (rank, float(threshold), metrics)
    assert best is not None
    return best[1], best[2]


def _states(keys: list[str], scores: dict[str, float], threshold: float, parameters: dict[str, Any]) -> dict[str, bool]:
    values = apply_persistence(
        [scores[key] for key in keys], threshold,
        int(parameters["entryPersistenceMonths"]), int(parameters["recoveryPersistenceMonths"]),
    )
    return dict(zip(keys, values, strict=True))


def _financial_score(row: dict[str, Any], aggregator: str) -> float:
    values = _values(row)
    missing = [code for code in FINANCIAL_CODES if code not in values]
    if missing:
        raise DatasetValidationError(f"E13 financial row lacks base inputs: {missing}.")
    severities = [
        _clip01((values["VIX_MONTHLY_MAX"] - 18.0) / 42.0),
        _clip01(values["SPY_MONTHLY_MAX_DRAWDOWN"] / 25.0),
        _clip01(values["HYG_MONTHLY_MAX_DRAWDOWN"] / 15.0),
        _clip01((values["HY_OAS"] - 2.0) / 4.0),
    ]
    if "SOFR_EFFR_MONTHLY_MAX" in values:
        severities.append(_clip01(values["SOFR_EFFR_MONTHLY_MAX"] / 200.0))
    if aggregator == "noisy-or":
        score = 1.0 - math.prod(1.0 - value for value in severities)
    elif aggregator == "top-two-mean":
        score = fmean(sorted(severities, reverse=True)[:2])
    else:
        raise DatasetValidationError(f"Unsupported E13 financial aggregator '{aggregator}'.")
    return round(score, 8)


def _recession_scores(rows: list[dict[str, Any]], aggregator: str) -> dict[str, float]:
    history: list[float] = []
    output = {}
    for row in rows:
        values = _values(row)
        missing = [code for code in RECESSION_CODES if code not in values]
        if missing:
            raise DatasetValidationError(f"E13 recession row lacks inputs: {missing}.")
        curve = values["YC_10Y2Y"]
        minimum = min((history + [curve])[-24:])
        components = [
            _clip01(values["SAHM"] / 0.5),
            _clip01((1.0 - values["INDPRO_YOY"]) / 7.0),
            _clip01(-minimum / 0.75) * _clip01((curve - minimum) / 1.0),
        ]
        if aggregator == "max-confirmation":
            score = 0.65 * max(components) + 0.35 * fmean(components)
        elif aggregator == "weighted-hazard":
            score = 0.5 * components[0] + 0.3 * components[1] + 0.2 * components[2]
        else:
            raise DatasetValidationError(f"Unsupported E13 recession aggregator '{aggregator}'.")
        output[row["asOfDate"]] = round(_clip01(score), 8)
        history.append(curve)
    return output


def _inner_dates(rows: list[dict[str, Any]], plan: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    available = {row["asOfDate"] for row in rows}
    folds = plan.get("folds")
    inner_years = int(plan.get("config", {}).get("testYears", 0))
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds) or inner_years <= 0:
        raise DatasetValidationError("E13 walk-forward plan is invalid.")
    unique: set[str] = set()
    reports = []
    for fold in sorted(folds, key=lambda item: item["number"]):
        train_to = date.fromisoformat(fold["train_to"])
        test_from = date.fromisoformat(fold["test_from"])
        if train_to >= test_from:
            raise DatasetValidationError("E13 outer train/test windows overlap.")
        inner_from = _add_years(train_to, -inner_years)
        selected = sorted(key for key in available if inner_from < date.fromisoformat(key) <= train_to)
        if not selected or any(date.fromisoformat(key) >= test_from for key in selected):
            raise DatasetValidationError("E13 attempted to use an outer test row.")
        unique.update(selected)
        reports.append({
            "number": fold["number"], "innerValidationFrom": selected[0],
            "innerValidationTo": selected[-1], "innerValidationRowCount": len(selected),
            "outerTestFrom": fold["test_from"], "outerTestTo": fold["test_to"],
            "outerTestRowCountUsed": 0,
        })
    return sorted(unique), reports


def _financial_episode_inventory(keys: list[str], episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for episode in episodes:
        if "financial_stress" not in episode["labels"]:
            continue
        observed = [key for key in keys if episode["first"] <= _month(key) <= episode["last"]]
        if observed:
            output.append({
                "episodeId": episode["id"], "validationRole": episode["validationRole"],
                "observedMonths": observed,
            })
    return output


def _recession_episode_inventory(keys: list[str], periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for period in periods:
        observed = [key for key in keys if period["first"] <= _month(key) <= period["trough"]]
        if observed:
            output.append({"episodeId": period["name"], "observedMonths": observed})
    return output


def _financial_controls(keys: list[str], episodes: list[dict[str, Any]]) -> list[str]:
    return [
        key for key in keys
        if any(episode["first"] <= _month(key) <= episode["last"] and "financial_stress" not in episode["labels"] for episode in episodes)
        and not any(episode["first"] <= _month(key) <= episode["last"] and "financial_stress" in episode["labels"] for episode in episodes)
    ]


def _validate_contract(
    dataset_sha: str, plan_bytes: bytes, protocol_bytes: bytes, protocol: Any,
    manifest_bytes: bytes, manifest: Any, lock_bytes: bytes, lock: Any, contract: Any,
) -> None:
    lock_sha = hashlib.sha256(lock_bytes).hexdigest()
    if (
        not isinstance(lock, dict) or lock.get("status") != "frozen"
        or protocol.get("protocolId") != "e13-candidate-generation-protocol-v1"
        or protocol.get("foundationLockSha256") != lock_sha
        or lock.get("hashes", {}).get("datasetSha256") != dataset_sha
        or lock.get("hashes", {}).get("walkForwardPlanSha256") != hashlib.sha256(plan_bytes).hexdigest()
    ):
        raise DatasetValidationError("E13 LOEO foundation bindings do not match.")
    if (
        not isinstance(manifest, dict) or manifest.get("status") != "generated-not-evaluated"
        or manifest.get("candidateCount") != 16 or len(manifest.get("candidates", [])) != 16
        or manifest.get("outerOosOpened") is not False
        or manifest.get("protocol", {}).get("sha256") != hashlib.sha256(protocol_bytes).hexdigest()
        or manifest.get("foundationLockSha256") != lock_sha
        or any(candidate.get("lifecycleStatus") != "research-generated" for candidate in manifest["candidates"])
    ):
        raise DatasetValidationError("E13 generated manifest is invalid or not bound to the protocol.")
    if (
        not isinstance(contract, dict)
        or contract.get("contractId") != "e13-loeo-evaluation-contract-v1"
        or contract.get("protocolSha256") != hashlib.sha256(protocol_bytes).hexdigest()
        or contract.get("generatedManifestSha256") != hashlib.sha256(manifest_bytes).hexdigest()
        or contract.get("foundationLockSha256") != lock_sha
        or contract.get("minimumObservableEpisodesPerTask") != 3
        or contract.get("thresholdSelection", {}).get("heldOutLabelsForbidden") is not True
        or "fewer than three" not in str(contract.get("insufficientEvidencePolicy"))
        or "Forbidden" not in str(contract.get("outerOosPolicy"))
        or contract.get("shortlistProduced") is not False
    ):
        raise DatasetValidationError("E13 LOEO evaluation contract is invalid.")


def _complexity(parameters: dict[str, Any]) -> int:
    aggregator = 2 if parameters["aggregator"] in {"noisy-or", "max-confirmation"} else 1
    return aggregator + int(parameters["entryPersistenceMonths"]) + int(parameters["recoveryPersistenceMonths"])


def _values(row: dict[str, Any]) -> dict[str, float]:
    return {
        str(item["seriesCode"]): float(item["value"])
        for item in row.get("macroObservations", [])
        if item.get("seriesCode") and item.get("value") is not None
    }


def _month(value: str) -> date:
    return date.fromisoformat(value).replace(day=1)


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
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
        raise DatasetValidationError(f"Immutable E13 LOEO report exists: '{destination}'.") from exc
    return destination
