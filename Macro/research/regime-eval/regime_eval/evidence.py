from __future__ import annotations

import hashlib
import json
import random
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics, calibration_table, probability_metrics


def write_model_evidence_report(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    ground_truth_path: str | Path,
    policy_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    truth_file, truth_bytes, truth = _read_json(ground_truth_path, "ground truth")
    policy_file, policy_bytes, policy = _read_json(policy_path, "evidence policy")
    periods = validate_recession_truth(truth)
    _validate_policy(policy)
    _validate_input_hashes(
        policy,
        dataset.sha256,
        hashlib.sha256(evaluation_bytes).hexdigest(),
        hashlib.sha256(plan_bytes).hexdigest(),
        hashlib.sha256(truth_bytes).hexdigest(),
    )
    if (
        not isinstance(evaluation, dict)
        or evaluation.get("schemaVersion") != 1
        or evaluation.get("datasetSha256") != dataset.sha256
        or evaluation.get("modelVersion") != policy["modelVersion"]
        or not isinstance(evaluation.get("rows"), list)
    ):
        raise DatasetValidationError("Evaluation does not match the evidence contract.")

    rows = {item["asOfDate"]: item for item in evaluation["rows"]}
    dataset_dates = {item["asOfDate"] for item in dataset.rows}
    if set(rows) != dataset_dates:
        raise DatasetValidationError("Evaluation dates do not exactly match dataset dates.")
    unique_dates = _unique_test_dates(plan, rows)
    actual = {key: is_recession(key, periods) for key in unique_dates}
    predicted = {key: rows[key]["operationalRegime"] == "DeflationBust" for key in unique_dates}
    probabilities = {key: _recession_probability(rows[key], key) for key in unique_dates}
    positive_episodes = _positive_episode_count(unique_dates, periods)

    requirements = {
        "minimumOutOfSampleRows": _requirement(
            len(unique_dates), policy["evidenceMinimums"]["outOfSampleRows"]
        ),
        "minimumPositiveMonths": _requirement(
            sum(actual.values()), policy["evidenceMinimums"]["positiveMonths"]
        ),
        "minimumPositiveEpisodes": _requirement(
            positive_episodes, policy["evidenceMinimums"]["positiveEpisodes"]
        ),
        "minimumNegativeMonths": _requirement(
            len(actual) - sum(actual.values()), policy["evidenceMinimums"]["negativeMonths"]
        ),
        "freshProspectiveEvidence": {
            "actual": policy["benchmarkScope"] == "fresh-prospective",
            "required": True,
            "passed": policy["benchmarkScope"] == "fresh-prospective",
        },
    }
    statistical_evidence = all(
        item["passed"]
        for key, item in requirements.items()
        if key != "freshProspectiveEvidence"
    )
    fresh = requirements["freshProspectiveEvidence"]["passed"]
    status = (
        "ELIGIBLE_FOR_HUMAN_REVIEW"
        if statistical_evidence and fresh
        else "DEVELOPMENT_ONLY"
        if statistical_evidence
        else "INSUFFICIENT_EVIDENCE"
    )

    report = {
        "reportVersion": 2,
        "reportType": "ModelEvidenceAndPromotion",
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "evaluationFileName": evaluation_file.name,
            "evaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "groundTruthFileName": truth_file.name,
            "groundTruthSha256": hashlib.sha256(truth_bytes).hexdigest(),
            "policyFileName": policy_file.name,
            "policySha256": hashlib.sha256(policy_bytes).hexdigest(),
        },
        "model": {
            "modelId": policy["modelId"],
            "modelVersion": policy["modelVersion"],
            "currentLifecycle": policy["currentLifecycle"],
            "requestedLifecycle": "operational-approved",
        },
        "protocol": {
            "benchmarkScope": policy["benchmarkScope"],
            "probabilityField": "DeflationBust regime probability",
            "decisionField": "operationalRegime == DeflationBust",
            "overlapPolicy": "unique OOS dates; each date scored once",
            "calibrationPolicy": "fixed bins; descriptive when positive support is insufficient",
            "bootstrapPolicy": "deterministic circular moving-block bootstrap",
        },
        "coverage": {
            "rowCount": len(unique_dates),
            "from": unique_dates[0] if unique_dates else None,
            "to": unique_dates[-1] if unique_dates else None,
            "positiveMonthCount": sum(actual.values()),
            "negativeMonthCount": len(actual) - sum(actual.values()),
            "positiveEpisodeCount": positive_episodes,
        },
        "classificationMetrics": binary_metrics(actual, predicted),
        "probabilityMetrics": probability_metrics(actual, probabilities),
        "calibration": calibration_table(actual, probabilities, policy["calibrationBins"]),
        "temporalDiagnostics": _temporal_diagnostics(
            unique_dates, actual, predicted, periods
        ),
        "uncertainty": _bootstrap_intervals(
            unique_dates,
            actual,
            predicted,
            probabilities,
            policy["bootstrap"]["replicates"],
            policy["bootstrap"]["blockMonths"],
            policy["bootstrap"]["seed"],
        ),
        "promotionGate": {
            "status": status,
            "requirements": requirements,
            "technicalGateIsPromotion": False,
            "operationalPromotionAllowed": status == "ELIGIBLE_FOR_HUMAN_REVIEW",
            "humanReviewRequired": True,
            "rationale": (
                "Fresh prospective evidence and preregistered evidence minimums are satisfied."
                if status == "ELIGIBLE_FOR_HUMAN_REVIEW"
                else "Historical development evidence cannot authorize operational promotion."
                if status == "DEVELOPMENT_ONLY"
                else "Positive months or independent episodes are below preregistered minimums."
            ),
        },
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _unique_test_dates(plan: Any, rows: dict[str, dict[str, Any]]) -> list[str]:
    folds = plan.get("folds") if isinstance(plan, dict) else None
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")
    values: set[str] = set()
    for fold in folds:
        start = _iso_date(fold.get("test_from"), "fold.test_from")
        end = _iso_date(fold.get("test_to"), "fold.test_to")
        values.update(key for key in rows if start <= date.fromisoformat(key) <= end)
    if not values:
        raise DatasetValidationError("Evidence report requires out-of-sample rows.")
    return sorted(values)


def _recession_probability(row: dict[str, Any], key: str) -> float:
    values = row.get("probabilities")
    if not isinstance(values, list):
        raise DatasetValidationError(f"Evaluation row {key} has no probability distribution.")
    matches = [item.get("probability") for item in values if item.get("regime") == "DeflationBust"]
    if len(matches) != 1:
        raise DatasetValidationError(f"Evaluation row {key} has no unique DeflationBust probability.")
    value = matches[0]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise DatasetValidationError(f"Evaluation row {key} has invalid DeflationBust probability.")
    return float(value)


def _positive_episode_count(dates: list[str], periods: list[dict[str, Any]]) -> int:
    available = [date.fromisoformat(key).replace(day=1) for key in dates]
    return sum(any(item["first"] <= value <= item["trough"] for value in available) for item in periods)


def _temporal_diagnostics(
    dates: list[str],
    actual: dict[str, bool],
    predicted: dict[str, bool],
    periods: list[dict[str, Any]],
) -> dict[str, Any]:
    false_positive_runs = _runs(
        dates, lambda key: predicted[key] and not actual[key]
    )
    false_negative_runs = _runs(
        dates, lambda key: actual[key] and not predicted[key]
    )
    episodes = []
    parsed = {key: date.fromisoformat(key).replace(day=1) for key in dates}
    for period in periods:
        inside = [key for key in dates if period["first"] <= parsed[key] <= period["trough"]]
        if not inside:
            continue
        first_signal = next((key for key in inside if predicted[key]), None)
        after = [key for key in dates if parsed[key] > period["trough"]]
        first_clear = next((key for key in after if not predicted[key]), None)
        episodes.append({
            "name": period["name"],
            "firstAvailablePositive": inside[0],
            "firstSignal": first_signal,
            "onsetLagMonths": _month_difference(inside[0], first_signal) if first_signal else None,
            "firstClearSignalAfterTrough": first_clear,
            "recoveryLagMonths": (
                _month_difference(period["trough"].isoformat(), first_clear)
                if first_clear else None
            ),
        })
    return {
        "falsePositiveRuns": false_positive_runs,
        "maximumFalsePositiveRunMonths": max((item["rowCount"] for item in false_positive_runs), default=0),
        "falseNegativeRuns": false_negative_runs,
        "maximumFalseNegativeRunMonths": max((item["rowCount"] for item in false_negative_runs), default=0),
        "episodes": episodes,
    }


def _runs(dates: list[str], predicate: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    current: list[str] = []
    for key in dates:
        if predicate(key):
            current.append(key)
        elif current:
            result.append({"from": current[0], "to": current[-1], "rowCount": len(current)})
            current = []
    if current:
        result.append({"from": current[0], "to": current[-1], "rowCount": len(current)})
    return result


def _bootstrap_intervals(
    dates: list[str],
    actual: dict[str, bool],
    predicted: dict[str, bool],
    probabilities: dict[str, float],
    replicates: int,
    block_months: int,
    seed: int,
) -> dict[str, Any]:
    randomizer = random.Random(seed)
    values: dict[str, list[float]] = {
        "recall": [], "precision": [], "f1": [], "brierScore": [], "logLoss": []
    }
    count = len(dates)
    for _ in range(replicates):
        sample: list[str] = []
        while len(sample) < count:
            start = randomizer.randrange(count)
            sample.extend(dates[(start + offset) % count] for offset in range(block_months))
        sample = sample[:count]
        sample_actual = {f"{index}:{key}": actual[key] for index, key in enumerate(sample)}
        sample_predicted = {f"{index}:{key}": predicted[key] for index, key in enumerate(sample)}
        sample_probability = {f"{index}:{key}": probabilities[key] for index, key in enumerate(sample)}
        binary = binary_metrics(sample_actual, sample_predicted)
        probability = probability_metrics(sample_actual, sample_probability)
        for key in ("recall", "precision", "f1"):
            if binary[key] is not None:
                values[key].append(float(binary[key]))
        for key in ("brierScore", "logLoss"):
            values[key].append(float(probability[key]))
    return {
        "method": "deterministic circular moving-block bootstrap",
        "replicates": replicates,
        "blockMonths": block_months,
        "seed": seed,
        "intervalLevel": 0.95,
        "intervals": {
            key: {
                "lower": _quantile(items, 0.025),
                "upper": _quantile(items, 0.975),
                "validReplicates": len(items),
            }
            for key, items in values.items()
        },
    }


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * probability)
    return round(ordered[index], 8)


def _validate_policy(policy: Any) -> None:
    if (
        not isinstance(policy, dict)
        or policy.get("schemaVersion") != 1
        or policy.get("benchmarkScope") not in {"development-diagnostic-only", "fresh-prospective"}
        or policy.get("currentLifecycle") not in {
            "research-baseline", "shadow-candidate", "operational-candidate", "operational-approved"
        }
    ):
        raise DatasetValidationError("Unsupported model evidence policy.")
    minimums = policy.get("evidenceMinimums")
    bootstrap = policy.get("bootstrap")
    if not isinstance(minimums, dict) or any(
        not isinstance(minimums.get(key), int) or minimums[key] < 1
        for key in ("outOfSampleRows", "positiveMonths", "positiveEpisodes", "negativeMonths")
    ):
        raise DatasetValidationError("Evidence minimums must be positive integers.")
    if (
        not isinstance(bootstrap, dict)
        or not isinstance(bootstrap.get("replicates"), int)
        or bootstrap["replicates"] < 100
        or not isinstance(bootstrap.get("blockMonths"), int)
        or bootstrap["blockMonths"] < 1
        or not isinstance(bootstrap.get("seed"), int)
    ):
        raise DatasetValidationError("Bootstrap policy is invalid.")
    if not isinstance(policy.get("calibrationBins"), int) or policy["calibrationBins"] < 2:
        raise DatasetValidationError("Calibration policy is invalid.")


def _validate_input_hashes(
    policy: dict[str, Any], dataset_sha: str, evaluation_sha: str, plan_sha: str, truth_sha: str
) -> None:
    expected = policy.get("expectedInputs")
    actual = {
        "datasetSha256": dataset_sha,
        "evaluationSha256": evaluation_sha,
        "walkForwardPlanSha256": plan_sha,
        "groundTruthSha256": truth_sha,
    }
    if not isinstance(expected, dict) or any(expected.get(key) != value for key, value in actual.items()):
        raise DatasetValidationError("Evidence policy input hashes do not match the supplied artifacts.")


def _requirement(actual: int, required: int) -> dict[str, Any]:
    return {"actual": actual, "required": required, "passed": actual >= required}


def _month_difference(start: str, end: str) -> int:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    return (last.year - first.year) * 12 + last.month - first.month


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _iso_date(value: Any, location: str) -> date:
    if not isinstance(value, str):
        raise DatasetValidationError(f"{location} must be an ISO date string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid ISO date.") from exc
