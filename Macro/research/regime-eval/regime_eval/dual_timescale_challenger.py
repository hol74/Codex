from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .dimensions import dimension_scores
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics, metric_delta, probability_metrics
from .stress import validate_stress_truth


def write_dual_timescale_report(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    recession_truth_path: str | Path,
    stress_truth_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    recession_file, recession_bytes, recession_truth = _read_json(recession_truth_path, "recession truth")
    stress_file, stress_bytes, stress_truth = _read_json(stress_truth_path, "stress truth")
    config_file, config_bytes, config = _read_json(config_path, "dual-timescale config")
    periods = validate_recession_truth(recession_truth)
    taxonomy, episodes = validate_stress_truth(stress_truth)
    parameters = _validate_config(config)
    _validate_hashes(
        config,
        dataset.sha256,
        hashlib.sha256(evaluation_bytes).hexdigest(),
        hashlib.sha256(plan_bytes).hexdigest(),
        hashlib.sha256(recession_bytes).hexdigest(),
        hashlib.sha256(stress_bytes).hexdigest(),
    )
    _validate_evaluation(evaluation, dataset.sha256, config)
    _validate_non_recession_episodes(episodes, periods)
    rows = {item["asOfDate"]: item for item in evaluation["rows"]}
    if set(rows) != {item["asOfDate"] for item in dataset.rows}:
        raise DatasetValidationError("Dual-timescale evaluation dates do not match dataset dates.")
    folds = plan.get("folds") if isinstance(plan, dict) else None
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")

    fold_reports: list[dict[str, Any]] = []
    earliest: dict[str, dict[str, Any]] = {}
    fold_actual: dict[str, bool] = {}
    fold_predicted: dict[str, bool] = {}
    for fold in sorted(folds, key=lambda item: item.get("number", 0)):
        train_from = _iso_date(fold.get("train_from"), "fold.train_from")
        train_to = _iso_date(fold.get("train_to"), "fold.train_to")
        test_from = _iso_date(fold.get("test_from"), "fold.test_from")
        test_to = _iso_date(fold.get("test_to"), "fold.test_to")
        if train_to >= test_from:
            raise DatasetValidationError(f"Fold {fold.get('number')} train and test windows overlap.")
        train_dates = sorted(key for key in rows if train_from <= date.fromisoformat(key) <= train_to)
        test_dates = sorted(key for key in rows if test_from <= date.fromisoformat(key) <= test_to)
        if not train_dates or not test_dates:
            raise DatasetValidationError(f"Fold {fold.get('number')} has insufficient train/test rows.")

        slow, fast = _initialize_state(train_dates, rows, parameters)
        probability = math.sqrt(slow * fast)
        active = probability >= parameters["entry"]
        predictions: list[dict[str, Any]] = []
        for key in test_dates:
            dimensions = dimension_scores(rows[key])
            raw_slow = _raw_slow(dimensions, parameters)
            slow = _ewma(slow, raw_slow, parameters["slowAlpha"])
            fast = _ewma(fast, dimensions["financialStress"], parameters["fastAlpha"])
            probability = math.sqrt(slow * fast)
            active = probability >= (parameters["exit"] if active else parameters["entry"])
            prediction = {
                "fold": fold.get("number"),
                "asOfDate": key,
                "dimensions": dimensions,
                "rawSlowContraction": round(raw_slow, 8),
                "filteredSlowContraction": round(slow, 8),
                "filteredFastStress": round(fast, 8),
                "recessionProbability": round(probability, 8),
                "predictedRecession": active,
            }
            predictions.append({**prediction, "actualRecession": is_recession(key, periods)})
            earliest.setdefault(key, prediction)
            composite_key = f"{fold.get('number')}:{key}"
            fold_actual[composite_key] = is_recession(key, periods)
            fold_predicted[composite_key] = active
        fold_reports.append({
            "number": fold.get("number"),
            "trainFrom": fold.get("train_from"),
            "trainTo": fold.get("train_to"),
            "testFrom": fold.get("test_from"),
            "testTo": fold.get("test_to"),
            "trainRowCount": len(train_dates),
            "testRowCount": len(test_dates),
            "terminalTrainSlowContraction": round(_initialize_state(train_dates, rows, parameters)[0], 8),
            "terminalTrainFastStress": round(_initialize_state(train_dates, rows, parameters)[1], 8),
            "metrics": binary_metrics(
                {item["asOfDate"]: item["actualRecession"] for item in predictions},
                {item["asOfDate"]: item["predictedRecession"] for item in predictions},
            ),
            "predictions": predictions,
        })

    unique_dates = sorted(earliest)
    actual = {key: is_recession(key, periods) for key in unique_dates}
    predicted = {key: bool(earliest[key]["predictedRecession"]) for key in unique_dates}
    probabilities = {key: float(earliest[key]["recessionProbability"]) for key in unique_dates}
    challenger_metrics = binary_metrics(actual, predicted)
    baseline_metrics = binary_metrics(
        actual, {key: rows[key]["operationalRegime"] == "DeflationBust" for key in unique_dates}
    )
    report = {
        "reportVersion": 1,
        "reportType": "DualTimescaleDevelopmentDiagnostic",
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "baselineEvaluationFileName": evaluation_file.name,
            "baselineEvaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "recessionGroundTruthFileName": recession_file.name,
            "recessionGroundTruthSha256": hashlib.sha256(recession_bytes).hexdigest(),
            "stressGroundTruthFileName": stress_file.name,
            "stressGroundTruthSha256": hashlib.sha256(stress_bytes).hexdigest(),
            "configFileName": config_file.name,
            "configSha256": hashlib.sha256(config_bytes).hexdigest(),
        },
        "challenger": config,
        "protocol": {
            "fitScope": "no outcome fitting; train feature history initializes causal filters",
            "testUse": "test labels are attached only after predictions are frozen",
            "overlapPolicy": config["uniqueDateAggregation"],
            "benchmarkScope": "development-diagnostic-only",
        },
        "coverage": {
            "foldCount": len(fold_reports),
            "foldObservationCount": len(fold_actual),
            "uniqueOutOfSampleRowCount": len(unique_dates),
            "uniqueOutOfSampleFrom": unique_dates[0],
            "uniqueOutOfSampleTo": unique_dates[-1],
        },
        "foldObservationAggregate": binary_metrics(fold_actual, fold_predicted),
        "uniqueOutOfSample": {
            "challenger": challenger_metrics,
            "probabilityMetrics": probability_metrics(actual, probabilities),
            "baselineOperational": baseline_metrics,
            "deltaVsBaselineOperational": metric_delta(challenger_metrics, baseline_metrics),
            "predictions": [
                {**earliest[key], "actualRecession": actual[key]} for key in unique_dates
            ],
        },
        "stressDiagnostics": _stress_diagnostics(unique_dates, earliest, taxonomy, episodes),
        "modelGate": {
            "status": "DEVELOPMENT_DIAGNOSTIC_ONLY",
            "passedAutomaticMetrics": False,
            "violations": ["FRESH_PROSPECTIVE_EVIDENCE_REQUIRED"],
            "historicalMetricComparisonIsPromotionGate": False,
            "humanReviewRequired": True,
        },
        "folds": fold_reports,
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _initialize_state(
    dates: list[str], rows: dict[str, dict[str, Any]], parameters: dict[str, float]
) -> tuple[float, float]:
    slow: float | None = None
    fast: float | None = None
    for key in dates:
        dimensions = dimension_scores(rows[key])
        raw_slow = _raw_slow(dimensions, parameters)
        slow = raw_slow if slow is None else _ewma(slow, raw_slow, parameters["slowAlpha"])
        raw_fast = dimensions["financialStress"]
        fast = raw_fast if fast is None else _ewma(fast, raw_fast, parameters["fastAlpha"])
    if slow is None or fast is None:
        raise DatasetValidationError("Dual-timescale state requires train history.")
    return slow, fast


def _raw_slow(dimensions: dict[str, float], parameters: dict[str, float]) -> float:
    return (
        parameters["growthWeight"] * dimensions["growthDeterioration"]
        + parameters["monetaryWeight"] * dimensions["monetaryRestriction"]
    )


def _ewma(previous: float, current: float, alpha: float) -> float:
    return alpha * current + (1.0 - alpha) * previous


def _stress_diagnostics(
    dates: list[str],
    predictions: dict[str, dict[str, Any]],
    taxonomy: dict[str, dict[str, Any]],
    episodes: list[dict[str, Any]],
) -> dict[str, Any]:
    partitions: dict[str, Any] = {}
    for role in ("development-v1", "protected-v2"):
        selected_episodes = [item for item in episodes if item.get("validationRole") == role]
        labels: dict[str, Any] = {}
        for code, definition in sorted(taxonomy.items()):
            selected = [
                key for key in dates
                if any(_episode_contains(item, key) and code in item["labels"] for item in selected_episodes)
            ]
            hits = [
                key for key in selected
                if all(
                    _dimension_hit(predictions[key]["dimensions"][dimension], bounds)
                    for dimension, bounds in definition["expectedDimensions"].items()
                )
            ]
            labels[code] = {
                "rowCount": len(selected),
                "allExpectedDimensionsHitCount": len(hits),
                "allExpectedDimensionsHitRate": round(len(hits) / len(selected), 8) if selected else None,
                "mismatchDates": [key for key in selected if key not in hits],
            }
        partitions[role] = {"episodeCount": len(selected_episodes), "labels": labels}
    return {
        "purpose": "dimension diagnostics only; curated unlabeled months are not true negatives",
        "partitions": partitions,
    }


def _episode_contains(episode: dict[str, Any], value: str) -> bool:
    month = date.fromisoformat(value).replace(day=1)
    return episode["first"] <= month <= episode["last"]


def _dimension_hit(value: float, bounds: dict[str, float]) -> bool:
    return value >= float(bounds["minimum"]) if "minimum" in bounds else value <= float(bounds["maximum"])


def _validate_non_recession_episodes(
    episodes: list[dict[str, Any]], periods: list[dict[str, Any]]
) -> None:
    for episode in episodes:
        current = episode["first"]
        while current <= episode["last"]:
            if is_recession(current.isoformat(), periods):
                raise DatasetValidationError(f"Stress episode '{episode['id']}' overlaps a recession.")
            current = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)


def _validate_config(config: Any) -> dict[str, float]:
    if (
        not isinstance(config, dict)
        or config.get("schemaVersion") != 1
        or config.get("role") != "challenger"
        or config.get("benchmarkScope") != "development-diagnostic-only"
        or config.get("dimensionFormulaVersion") != "macro-financial-dimensions-v1"
    ):
        raise DatasetValidationError("Unsupported dual-timescale configuration.")
    slow, fast, probability = config.get("slowComponent"), config.get("fastComponent"), config.get("recessionProbability")
    if not all(isinstance(item, dict) for item in (slow, fast, probability)):
        raise DatasetValidationError("Dual-timescale component configuration is incomplete.")
    parameters = {
        "growthWeight": slow.get("growthWeight"),
        "monetaryWeight": slow.get("monetaryWeight"),
        "slowAlpha": slow.get("causalEwmaAlpha"),
        "fastAlpha": fast.get("causalEwmaAlpha"),
        "entry": probability.get("entryThreshold"),
        "exit": probability.get("exitThreshold"),
    }
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 1
        for value in parameters.values()
    ):
        raise DatasetValidationError("Dual-timescale numeric parameters must be in (0, 1].")
    if not math.isclose(float(parameters["growthWeight"]) + float(parameters["monetaryWeight"]), 1.0):
        raise DatasetValidationError("Dual-timescale slow weights must sum to one.")
    if not float(parameters["exit"]) < float(parameters["entry"]):
        raise DatasetValidationError("Dual-timescale exit threshold must be below entry threshold.")
    return {key: float(value) for key, value in parameters.items()}


def _validate_hashes(
    config: dict[str, Any], dataset: str, evaluation: str, plan: str, recession: str, stress: str
) -> None:
    expected = config.get("expectedInputs")
    actual = {
        "datasetSha256": dataset,
        "baselineEvaluationSha256": evaluation,
        "walkForwardPlanSha256": plan,
        "recessionGroundTruthSha256": recession,
        "stressGroundTruthSha256": stress,
    }
    if not isinstance(expected, dict) or any(expected.get(key) != value for key, value in actual.items()):
        raise DatasetValidationError("Dual-timescale config input hashes do not match supplied artifacts.")


def _validate_evaluation(evaluation: Any, dataset_sha: str, config: dict[str, Any]) -> None:
    if (
        not isinstance(evaluation, dict)
        or evaluation.get("schemaVersion") != 1
        or evaluation.get("datasetSha256") != dataset_sha
        or evaluation.get("modelVersion") != config.get("baselineModelVersion")
        or not isinstance(evaluation.get("rows"), list)
    ):
        raise DatasetValidationError("Baseline evaluation does not match dual-timescale config.")
    for row in evaluation["rows"]:
        dimension_scores(row)


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
