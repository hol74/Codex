from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from statistics import fmean
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics as _binary_metrics
from .metrics import metric_delta as _metric_delta


def write_clustering_challenger_report(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    ground_truth_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    truth_file, truth_bytes, truth = _read_json(ground_truth_path, "recession ground truth")
    config_file, config_bytes, config = _read_json(config_path, "challenger config")
    periods = validate_recession_truth(truth)
    feature_codes, cluster_count, max_iterations, tolerance = _validate_config(config)
    _validate_evaluation(evaluation, dataset.sha256, feature_codes)
    rows = {row["asOfDate"]: row for row in evaluation["rows"]}
    if set(rows) != {row["asOfDate"] for row in dataset.rows}:
        raise DatasetValidationError("Challenger evaluation dates do not exactly match dataset dates.")
    coverage_from = _iso_date(truth.get("coverageFrom"), "groundTruth.coverageFrom")
    coverage_to = _iso_date(truth.get("coverageTo"), "groundTruth.coverageTo")
    if coverage_from > coverage_to or any(
        not coverage_from <= date.fromisoformat(key) <= coverage_to for key in rows
    ):
        raise DatasetValidationError("Challenger ground-truth coverage does not contain every dataset date.")

    vectors = {key: _feature_vector(row, feature_codes) for key, row in rows.items()}
    folds = plan.get("folds")
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")

    fold_reports: list[dict[str, Any]] = []
    all_fold_predictions: list[dict[str, Any]] = []
    earliest_predictions: dict[str, bool] = {}
    for fold in sorted(folds, key=lambda item: item.get("number", 0)):
        train_from = _iso_date(fold.get("train_from"), "fold.train_from")
        train_to = _iso_date(fold.get("train_to"), "fold.train_to")
        test_from = _iso_date(fold.get("test_from"), "fold.test_from")
        test_to = _iso_date(fold.get("test_to"), "fold.test_to")
        if train_to >= test_from:
            raise DatasetValidationError(f"Fold {fold.get('number')} train and test windows overlap.")
        train_dates = sorted(key for key in rows if train_from <= date.fromisoformat(key) <= train_to)
        test_dates = sorted(key for key in rows if test_from <= date.fromisoformat(key) <= test_to)
        if len(train_dates) < cluster_count or not test_dates:
            raise DatasetValidationError(f"Fold {fold.get('number')} has insufficient train/test rows.")
        if not any(is_recession(key, periods) for key in train_dates):
            raise DatasetValidationError(f"Fold {fold.get('number')} has no train recession label for cluster mapping.")

        means, scales = _fit_standardizer([vectors[key] for key in train_dates])
        train_vectors = [_standardize(vectors[key], means, scales) for key in train_dates]
        centroids, assignments, iterations, converged = _fit_kmeans(
            train_vectors, cluster_count, max_iterations, tolerance
        )
        cluster_summary = _cluster_summary(train_dates, assignments, centroids, periods)
        recession_cluster = max(
            (item for item in cluster_summary if item["recessionCount"] > 0),
            key=lambda item: (
                item["smoothedRecessionRate"],
                item["recessionRate"],
                item["recessionCount"],
                -item["cluster"],
            ),
        )["cluster"]
        predictions = []
        for key in test_dates:
            cluster = _nearest(_standardize(vectors[key], means, scales), centroids)
            predicted = cluster == recession_cluster
            prediction = {
                "fold": fold.get("number"),
                "asOfDate": key,
                "cluster": cluster,
                "predictedRecession": predicted,
                "actualRecession": is_recession(key, periods),
            }
            predictions.append(prediction)
            all_fold_predictions.append(prediction)
            earliest_predictions.setdefault(key, predicted)

        fold_reports.append({
            "number": fold.get("number"),
            "trainFrom": fold.get("train_from"),
            "trainTo": fold.get("train_to"),
            "testFrom": fold.get("test_from"),
            "testTo": fold.get("test_to"),
            "trainRowCount": len(train_dates),
            "testRowCount": len(test_dates),
            "trainRecessionCount": sum(is_recession(key, periods) for key in train_dates),
            "iterations": iterations,
            "converged": converged,
            "recessionCluster": recession_cluster,
            "clusterTrainingSummary": cluster_summary,
            "metrics": _binary_metrics({item["asOfDate"]: item["actualRecession"] for item in predictions},
                                       {item["asOfDate"]: item["predictedRecession"] for item in predictions}),
            "predictions": predictions,
        })

    unique_dates = sorted(earliest_predictions)
    actual_unique = {key: is_recession(key, periods) for key in unique_dates}
    challenger_metrics = _binary_metrics(actual_unique, earliest_predictions)
    baseline_primary = _binary_metrics(
        actual_unique, {key: rows[key]["primaryRegime"] == "DeflationBust" for key in unique_dates}
    )
    baseline_operational = _binary_metrics(
        actual_unique, {key: rows[key]["operationalRegime"] == "DeflationBust" for key in unique_dates}
    )
    fold_actual = {f"{item['fold']}:{item['asOfDate']}": item["actualRecession"] for item in all_fold_predictions}
    fold_predicted = {f"{item['fold']}:{item['asOfDate']}": item["predictedRecession"] for item in all_fold_predictions}
    report = {
        "reportVersion": 1,
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "baselineEvaluationFileName": evaluation_file.name,
            "baselineEvaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "groundTruthFileName": truth_file.name,
            "groundTruthSha256": hashlib.sha256(truth_bytes).hexdigest(),
            "configFileName": config_file.name,
            "configSha256": hashlib.sha256(config_bytes).hexdigest(),
        },
        "challenger": config,
        "protocol": {
            "fitScope": "standardizer, centroids, and recession-cluster mapping fit on each train fold only",
            "testUse": "test labels are read only after predictions and never affect model selection",
            "overlapPolicy": config["uniqueDateAggregation"],
            "promotionStatus": "not automatically promotable; human Model Gate required",
        },
        "coverage": {
            "foldCount": len(fold_reports),
            "foldObservationCount": len(all_fold_predictions),
            "uniqueOutOfSampleRowCount": len(unique_dates),
            "uniqueOutOfSampleFrom": unique_dates[0] if unique_dates else None,
            "uniqueOutOfSampleTo": unique_dates[-1] if unique_dates else None,
        },
        "foldObservationAggregate": _binary_metrics(fold_actual, fold_predicted),
        "uniqueOutOfSample": {
            "challenger": challenger_metrics,
            "baselinePrimary": baseline_primary,
            "baselineOperational": baseline_operational,
            "deltaVsBaselinePrimary": _metric_delta(challenger_metrics, baseline_primary),
            "predictions": [
                {"asOfDate": key, "predictedRecession": earliest_predictions[key], "actualRecession": actual_unique[key]}
                for key in unique_dates
            ],
        },
        "folds": fold_reports,
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination.resolve()


def _fit_standardizer(vectors: list[list[float]]) -> tuple[list[float], list[float]]:
    means = [fmean(vector[index] for vector in vectors) for index in range(len(vectors[0]))]
    scales = []
    for index, mean in enumerate(means):
        variance = fmean((vector[index] - mean) ** 2 for vector in vectors)
        scale = math.sqrt(variance)
        scales.append(scale if scale > 1e-12 else 1.0)
    return means, scales


def _standardize(vector: list[float], means: list[float], scales: list[float]) -> list[float]:
    return [(value - means[index]) / scales[index] for index, value in enumerate(vector)]


def _fit_kmeans(
    vectors: list[list[float]], cluster_count: int, max_iterations: int, tolerance: float
) -> tuple[list[list[float]], list[int], int, bool]:
    zero = [0.0] * len(vectors[0])
    first = min(range(len(vectors)), key=lambda index: (_distance(vectors[index], zero), index))
    centroids = [list(vectors[first])]
    while len(centroids) < cluster_count:
        next_index = max(
            range(len(vectors)),
            key=lambda index: (min(_distance(vectors[index], item) for item in centroids), -index),
        )
        centroids.append(list(vectors[next_index]))

    assignments: list[int] = []
    for iteration in range(1, max_iterations + 1):
        new_assignments = [_nearest(vector, centroids) for vector in vectors]
        new_centroids: list[list[float]] = []
        for cluster in range(cluster_count):
            members = [vectors[index] for index, assigned in enumerate(new_assignments) if assigned == cluster]
            new_centroids.append(
                [fmean(item[column] for item in members) for column in range(len(vectors[0]))]
                if members else list(centroids[cluster])
            )
        shift = max(_distance(centroids[index], new_centroids[index]) for index in range(cluster_count))
        stable = new_assignments == assignments
        centroids, assignments = new_centroids, new_assignments
        if stable or shift <= tolerance * tolerance:
            return centroids, assignments, iteration, True
    return centroids, assignments, max_iterations, False


def _nearest(vector: list[float], centroids: list[list[float]]) -> int:
    return min(range(len(centroids)), key=lambda index: (_distance(vector, centroids[index]), index))


def _distance(first: list[float], second: list[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(first, second))


def _cluster_summary(
    dates: list[str], assignments: list[int], centroids: list[list[float]], periods: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    summary = []
    for cluster in range(len(centroids)):
        members = [key for key, assigned in zip(dates, assignments) if assigned == cluster]
        recession_count = sum(is_recession(key, periods) for key in members)
        summary.append({
            "cluster": cluster,
            "rowCount": len(members),
            "recessionCount": recession_count,
            "recessionRate": _ratio(recession_count, len(members)),
            "smoothedRecessionRate": _ratio(recession_count + 1, len(members) + 2),
            "standardizedCentroid": [round(value, 8) for value in centroids[cluster]],
        })
    return summary


def _validate_config(config: Any) -> tuple[list[str], int, int, float]:
    if not isinstance(config, dict) or config.get("schemaVersion") != 1 or config.get("role") != "challenger":
        raise DatasetValidationError("Unsupported challenger configuration.")
    feature_codes = config.get("featureCodes")
    cluster_count = config.get("clusterCount")
    max_iterations = config.get("maxIterations")
    tolerance = config.get("convergenceTolerance")
    if not isinstance(feature_codes, list) or not feature_codes or len(set(feature_codes)) != len(feature_codes):
        raise DatasetValidationError("Challenger featureCodes must be a unique non-empty array.")
    if not isinstance(cluster_count, int) or cluster_count < 2:
        raise DatasetValidationError("Challenger clusterCount must be at least two.")
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise DatasetValidationError("Challenger maxIterations must be positive.")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or tolerance <= 0:
        raise DatasetValidationError("Challenger convergenceTolerance must be positive.")
    return [str(item) for item in feature_codes], cluster_count, max_iterations, float(tolerance)


def _validate_evaluation(evaluation: Any, dataset_sha256: str, feature_codes: list[str]) -> None:
    if not isinstance(evaluation, dict) or evaluation.get("schemaVersion") != 1:
        raise DatasetValidationError("Unsupported baseline evaluation schema for challenger.")
    if evaluation.get("datasetSha256") != dataset_sha256 or not isinstance(evaluation.get("rows"), list):
        raise DatasetValidationError("Baseline evaluation does not match the challenger dataset.")
    for index, row in enumerate(evaluation["rows"]):
        scores = row.get("featureScores") if isinstance(row, dict) else None
        if not isinstance(scores, list) or {item.get("featureCode") for item in scores} != set(feature_codes):
            raise DatasetValidationError(f"Baseline evaluation row {index} does not contain the configured features.")


def _feature_vector(row: dict[str, Any], feature_codes: list[str]) -> list[float]:
    scores = {item["featureCode"]: item["normalizedScore"] for item in row["featureScores"]}
    vector = [float(scores[code]) for code in feature_codes]
    if any(not math.isfinite(value) for value in vector):
        raise DatasetValidationError("Challenger feature vector contains a non-finite value.")
    return vector


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


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 8) if denominator else None
