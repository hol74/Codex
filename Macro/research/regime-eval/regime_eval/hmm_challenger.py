from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

from .challenger import (
    _feature_vector,
    _fit_kmeans,
    _fit_standardizer,
    _iso_date,
    _read_json,
    _standardize,
)
from .dataset import DatasetValidationError, load_dataset
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics as _binary_metrics
from .metrics import metric_delta as _metric_delta


def write_hmm_challenger_report(
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
    config_file, config_bytes, config = _read_json(config_path, "HMM challenger config")
    periods = validate_recession_truth(truth)
    settings = _validate_config(config)
    evaluation_sha = hashlib.sha256(evaluation_bytes).hexdigest()
    _validate_evaluation(evaluation, dataset.sha256, evaluation_sha, settings)

    rows = {row["asOfDate"]: row for row in evaluation["rows"]}
    if set(rows) != {row["asOfDate"] for row in dataset.rows}:
        raise DatasetValidationError("HMM evaluation dates do not exactly match dataset dates.")
    coverage_from = _iso_date(truth.get("coverageFrom"), "groundTruth.coverageFrom")
    coverage_to = _iso_date(truth.get("coverageTo"), "groundTruth.coverageTo")
    if coverage_from > coverage_to or any(
        not coverage_from <= date.fromisoformat(key) <= coverage_to for key in rows
    ):
        raise DatasetValidationError("HMM ground-truth coverage does not contain every dataset date.")

    vectors = {key: _feature_vector(row, settings["featureCodes"]) for key, row in rows.items()}
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
        if train_from > train_to or train_to >= test_from or test_from > test_to:
            raise DatasetValidationError(f"Fold {fold.get('number')} has invalid train/test boundaries.")
        train_dates = sorted(key for key in rows if train_from <= date.fromisoformat(key) <= train_to)
        test_dates = sorted(key for key in rows if test_from <= date.fromisoformat(key) <= test_to)
        if len(train_dates) < settings["stateCount"] or not test_dates:
            raise DatasetValidationError(f"Fold {fold.get('number')} has insufficient train/test rows.")
        if not any(is_recession(key, periods) for key in train_dates):
            raise DatasetValidationError(f"Fold {fold.get('number')} has no train recession label for state mapping.")

        means, scales = _fit_standardizer([vectors[key] for key in train_dates])
        train_vectors = [_standardize(vectors[key], means, scales) for key in train_dates]
        model, gammas, terminal_posterior, iterations, converged, log_likelihood = _fit_hmm(
            train_vectors,
            settings["stateCount"],
            settings["maxIterations"],
            settings["convergenceTolerance"],
            settings["varianceFloor"],
            settings["transitionPseudoCount"],
        )
        state_summary = _state_training_summary(
            train_dates, gammas, model, periods, settings["labelSmoothing"]
        )
        recession_state = max(
            (item for item in state_summary if item["recessionCount"] > 0),
            key=lambda item: (
                item["smoothedRecessionRate"],
                item["recessionRate"],
                item["recessionCount"],
                -item["state"],
            ),
        )["state"]

        predictions: list[dict[str, Any]] = []
        posterior = terminal_posterior
        for key in test_dates:
            posterior = _filter_step(
                _standardize(vectors[key], means, scales), posterior, model
            )
            state = max(range(len(posterior)), key=lambda index: (posterior[index], -index))
            predicted = state == recession_state
            prediction = {
                "fold": fold.get("number"),
                "asOfDate": key,
                "state": state,
                "stateProbability": round(posterior[state], 8),
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
            "trainLogLikelihood": round(log_likelihood, 8),
            "recessionState": recession_state,
            "initialProbabilities": [round(value, 8) for value in model["initial"]],
            "transitionMatrix": [
                [round(value, 8) for value in row] for row in model["transitions"]
            ],
            "stateTrainingSummary": state_summary,
            "metrics": _binary_metrics(
                {item["asOfDate"]: item["actualRecession"] for item in predictions},
                {item["asOfDate"]: item["predictedRecession"] for item in predictions},
            ),
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
    challenger_delta = _metric_delta(challenger_metrics, baseline_operational)
    policy = config["promotionPolicy"]
    gate_violations = []
    if challenger_delta["recall"] is None or challenger_delta["recall"] < float(policy["minimumRecallDeltaVsBaselineOperational"]):
        gate_violations.append("RECALL_REGRESSION")
    if challenger_delta["f1"] is None or challenger_delta["f1"] < float(policy["minimumF1DeltaVsBaselineOperational"]):
        gate_violations.append("F1_REGRESSION")
    if policy["requireConvergenceEveryFold"] and any(not fold["converged"] for fold in fold_reports):
        gate_violations.append("NON_CONVERGED_FOLD")

    fold_actual = {f"{item['fold']}:{item['asOfDate']}": item["actualRecession"] for item in all_fold_predictions}
    fold_predicted = {f"{item['fold']}:{item['asOfDate']}": item["predictedRecession"] for item in all_fold_predictions}
    report = {
        "reportVersion": 1,
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "baselineEvaluationFileName": evaluation_file.name,
            "baselineEvaluationSha256": evaluation_sha,
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "groundTruthFileName": truth_file.name,
            "groundTruthSha256": hashlib.sha256(truth_bytes).hexdigest(),
            "configFileName": config_file.name,
            "configSha256": hashlib.sha256(config_bytes).hexdigest(),
        },
        "challenger": config,
        "protocol": {
            "fitScope": "standardizer, HMM parameters, and recession-state mapping fit on each train fold only",
            "testInference": config["testInference"],
            "testUse": "test labels are read only after causal predictions and never affect fit or state mapping",
            "overlapPolicy": config["uniqueDateAggregation"],
        },
        "coverage": {
            "foldCount": len(fold_reports),
            "foldObservationCount": len(all_fold_predictions),
            "uniqueOutOfSampleRowCount": len(unique_dates),
            "uniqueOutOfSampleFrom": unique_dates[0] if unique_dates else None,
            "uniqueOutOfSampleTo": unique_dates[-1] if unique_dates else None,
        },
        "modelGate": {
            "passedAutomaticMetrics": not gate_violations,
            "humanReviewRequired": bool(policy["humanModelGateRequired"]),
            "violations": gate_violations,
        },
        "foldObservationAggregate": _binary_metrics(fold_actual, fold_predicted),
        "uniqueOutOfSample": {
            "challenger": challenger_metrics,
            "baselinePrimary": baseline_primary,
            "baselineOperational": baseline_operational,
            "deltaVsBaselineOperational": challenger_delta,
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


def _fit_hmm(
    vectors: list[list[float]],
    state_count: int,
    max_iterations: int,
    tolerance: float,
    variance_floor: float,
    transition_pseudo_count: float,
) -> tuple[dict[str, Any], list[list[float]], list[float], int, bool, float]:
    centroids, assignments, _, _ = _fit_kmeans(vectors, state_count, max_iterations, tolerance)
    dimension_count = len(vectors[0])
    global_variances = [
        max(variance_floor, sum((vector[d] - sum(item[d] for item in vectors) / len(vectors)) ** 2 for vector in vectors) / len(vectors))
        for d in range(dimension_count)
    ]
    variances = []
    for state in range(state_count):
        members = [vector for vector, assigned in zip(vectors, assignments) if assigned == state]
        variances.append([
            max(
                variance_floor,
                sum((vector[d] - centroids[state][d]) ** 2 for vector in members) / len(members),
            ) if members else global_variances[d]
            for d in range(dimension_count)
        ])
    initial = _normalize([
        transition_pseudo_count + (1.0 if assignments[0] == state else 0.0)
        for state in range(state_count)
    ])
    transition_counts = [[transition_pseudo_count] * state_count for _ in range(state_count)]
    for left, right in zip(assignments, assignments[1:]):
        transition_counts[left][right] += 1.0
    transitions = [_normalize(row) for row in transition_counts]
    model = {"initial": initial, "transitions": transitions, "means": centroids, "variances": variances}

    previous_log_likelihood: float | None = None
    for iteration in range(1, max_iterations + 1):
        log_likelihood, gammas, xis, terminal = _forward_backward(vectors, model)
        if previous_log_likelihood is not None and abs(log_likelihood - previous_log_likelihood) <= tolerance:
            return model, gammas, terminal, iteration, True, log_likelihood
        model = _maximize(
            vectors, gammas, xis, variance_floor, transition_pseudo_count
        )
        previous_log_likelihood = log_likelihood
    log_likelihood, gammas, _, terminal = _forward_backward(vectors, model)
    return model, gammas, terminal, max_iterations, False, log_likelihood


def _maximize(
    vectors: list[list[float]],
    gammas: list[list[float]],
    xis: list[list[list[float]]],
    variance_floor: float,
    transition_pseudo_count: float,
) -> dict[str, Any]:
    state_count = len(gammas[0])
    dimension_count = len(vectors[0])
    initial = _normalize([max(1e-12, value) for value in gammas[0]])
    transitions = []
    for left in range(state_count):
        counts = [
            transition_pseudo_count + sum(matrix[left][right] for matrix in xis)
            for right in range(state_count)
        ]
        transitions.append(_normalize(counts))
    means: list[list[float]] = []
    variances: list[list[float]] = []
    for state in range(state_count):
        weight = max(1e-12, sum(gamma[state] for gamma in gammas))
        mean = [
            sum(gammas[index][state] * vectors[index][dimension] for index in range(len(vectors))) / weight
            for dimension in range(dimension_count)
        ]
        variance = [
            max(
                variance_floor,
                sum(
                    gammas[index][state] * (vectors[index][dimension] - mean[dimension]) ** 2
                    for index in range(len(vectors))
                ) / weight,
            )
            for dimension in range(dimension_count)
        ]
        means.append(mean)
        variances.append(variance)
    return {"initial": initial, "transitions": transitions, "means": means, "variances": variances}


def _forward_backward(
    vectors: list[list[float]], model: dict[str, Any]
) -> tuple[float, list[list[float]], list[list[list[float]]], list[float]]:
    state_count = len(model["initial"])
    emissions = [[_log_gaussian(vector, model["means"][state], model["variances"][state])
                  for state in range(state_count)] for vector in vectors]
    log_initial = [math.log(max(1e-300, value)) for value in model["initial"]]
    log_transitions = [[math.log(max(1e-300, value)) for value in row] for row in model["transitions"]]
    alpha = [[log_initial[state] + emissions[0][state] for state in range(state_count)]]
    for index in range(1, len(vectors)):
        alpha.append([
            emissions[index][right] + _logsumexp([
                alpha[index - 1][left] + log_transitions[left][right]
                for left in range(state_count)
            ])
            for right in range(state_count)
        ])
    log_likelihood = _logsumexp(alpha[-1])
    beta = [[0.0] * state_count for _ in vectors]
    for index in range(len(vectors) - 2, -1, -1):
        beta[index] = [
            _logsumexp([
                log_transitions[left][right] + emissions[index + 1][right] + beta[index + 1][right]
                for right in range(state_count)
            ])
            for left in range(state_count)
        ]
    gammas = [
        _normalize([math.exp(alpha[index][state] + beta[index][state] - log_likelihood)
                    for state in range(state_count)])
        for index in range(len(vectors))
    ]
    xis = []
    for index in range(len(vectors) - 1):
        matrix = [[
            math.exp(
                alpha[index][left] + log_transitions[left][right]
                + emissions[index + 1][right] + beta[index + 1][right] - log_likelihood
            )
            for right in range(state_count)] for left in range(state_count)]
        total = sum(sum(row) for row in matrix)
        xis.append([[value / total for value in row] for row in matrix])
    terminal = _normalize([math.exp(value - log_likelihood) for value in alpha[-1]])
    return log_likelihood, gammas, xis, terminal


def _filter_step(vector: list[float], previous: list[float], model: dict[str, Any]) -> list[float]:
    state_count = len(previous)
    log_values = []
    for right in range(state_count):
        predictive = sum(previous[left] * model["transitions"][left][right] for left in range(state_count))
        log_values.append(
            math.log(max(1e-300, predictive))
            + _log_gaussian(vector, model["means"][right], model["variances"][right])
        )
    normalizer = _logsumexp(log_values)
    return _normalize([math.exp(value - normalizer) for value in log_values])


def _state_training_summary(
    dates: list[str],
    gammas: list[list[float]],
    model: dict[str, Any],
    periods: list[dict[str, Any]],
    smoothing: float,
) -> list[dict[str, Any]]:
    summary = []
    assignments = [
        max(range(len(gamma)), key=lambda index: (gamma[index], -index)) for gamma in gammas
    ]
    for state in range(len(model["initial"])):
        members = [key for key, assigned in zip(dates, assignments) if assigned == state]
        recession_count = sum(is_recession(key, periods) for key in members)
        occupancy = sum(gamma[state] for gamma in gammas)
        recession_responsibility = sum(
            gammas[index][state] for index, key in enumerate(dates) if is_recession(key, periods)
        )
        summary.append({
            "state": state,
            "rowCount": len(members),
            "recessionCount": recession_count,
            "occupancy": round(occupancy, 8),
            "recessionResponsibility": round(recession_responsibility, 8),
            "recessionRate": round(recession_count / len(members), 8) if members else None,
            "smoothedRecessionRate": round(
                (recession_count + smoothing) / (len(members) + (2.0 * smoothing)), 8
            ),
            "standardizedMean": [round(value, 8) for value in model["means"][state]],
            "standardizedVariance": [round(value, 8) for value in model["variances"][state]],
        })
    return summary


def _log_gaussian(vector: list[float], mean: list[float], variance: list[float]) -> float:
    return -0.5 * sum(
        math.log(2.0 * math.pi * variance[index])
        + ((value - mean[index]) ** 2 / variance[index])
        for index, value in enumerate(vector)
    )


def _logsumexp(values: list[float]) -> float:
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def _normalize(values: list[float]) -> list[float]:
    total = sum(values)
    if not math.isfinite(total) or total <= 0.0:
        raise DatasetValidationError("HMM normalization encountered invalid probability mass.")
    return [value / total for value in values]


def _validate_config(config: Any) -> dict[str, Any]:
    required = {
        "featureCodes", "stateCount", "maxIterations", "convergenceTolerance",
        "varianceFloor", "transitionPseudoCount", "labelSmoothing",
        "baselineModelVersion", "baselineEvaluationSha256", "testInference",
        "uniqueDateAggregation", "promotionPolicy",
    }
    if (
        not isinstance(config, dict)
        or config.get("schemaVersion") != 1
        or config.get("role") != "challenger"
        or config.get("modelFamily") != "Gaussian HMM"
        or not required <= config.keys()
    ):
        raise DatasetValidationError("Unsupported or incomplete HMM challenger configuration.")
    feature_codes = config["featureCodes"]
    if not isinstance(feature_codes, list) or not feature_codes or len(feature_codes) != len(set(feature_codes)):
        raise DatasetValidationError("HMM featureCodes must be a unique non-empty array.")
    integer_fields = ("stateCount", "maxIterations")
    if any(isinstance(config[key], bool) or not isinstance(config[key], int) or config[key] < 2 for key in integer_fields):
        raise DatasetValidationError("HMM stateCount and maxIterations must be integers of at least two.")
    for key in ("convergenceTolerance", "varianceFloor", "transitionPseudoCount", "labelSmoothing"):
        if isinstance(config[key], bool) or not isinstance(config[key], (int, float)) or config[key] <= 0:
            raise DatasetValidationError(f"HMM {key} must be positive.")
    policy = config["promotionPolicy"]
    if not isinstance(policy, dict) or not {
        "minimumRecallDeltaVsBaselineOperational", "minimumF1DeltaVsBaselineOperational",
        "requireConvergenceEveryFold", "humanModelGateRequired",
    } <= policy.keys():
        raise DatasetValidationError("HMM promotionPolicy is incomplete.")
    return {
        "featureCodes": [str(value) for value in feature_codes],
        "stateCount": config["stateCount"],
        "maxIterations": config["maxIterations"],
        "convergenceTolerance": float(config["convergenceTolerance"]),
        "varianceFloor": float(config["varianceFloor"]),
        "transitionPseudoCount": float(config["transitionPseudoCount"]),
        "labelSmoothing": float(config["labelSmoothing"]),
        "baselineModelVersion": config["baselineModelVersion"],
        "baselineEvaluationSha256": config["baselineEvaluationSha256"],
    }


def _validate_evaluation(
    evaluation: Any, dataset_sha256: str, evaluation_sha256: str, settings: dict[str, Any]
) -> None:
    if not isinstance(evaluation, dict) or evaluation.get("schemaVersion") != 1:
        raise DatasetValidationError("Unsupported baseline evaluation schema for HMM challenger.")
    if evaluation.get("datasetSha256") != dataset_sha256 or evaluation.get("modelVersion") != settings["baselineModelVersion"]:
        raise DatasetValidationError("HMM baseline evaluation does not match configured dataset/model.")
    if evaluation_sha256 != settings["baselineEvaluationSha256"]:
        raise DatasetValidationError("HMM baseline evaluation SHA-256 does not match the preregistered config.")
    if not isinstance(evaluation.get("rows"), list):
        raise DatasetValidationError("HMM baseline evaluation rows are missing.")
    for index, row in enumerate(evaluation["rows"]):
        scores = row.get("featureScores") if isinstance(row, dict) else None
        if not isinstance(scores, list) or {item.get("featureCode") for item in scores} != set(settings["featureCodes"]):
            raise DatasetValidationError(f"HMM evaluation row {index} does not contain configured features.")
