from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from statistics import fmean, median
from typing import Any, Callable

from .dataset import DatasetValidationError, load_dataset
from .dimensional_baseline import (
    _add_years,
    _baseline_probability,
    _false_positive_run,
    _minimum_optional,
    _optional_delta,
    _protected_stress_hit_rate,
    _read_json,
)
from .dimensions import dimension_scores
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics, calibration_table, metric_delta, probability_metrics
from .stress import validate_stress_truth


def write_e11_challenger_gate(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    recession_truth_path: str | Path,
    stress_truth_path: str | Path,
    candidate_path: str | Path,
    gate_path: str | Path,
    manifest_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    sources = [
        _read_json(evaluation_path, "baseline evaluation"),
        _read_json(plan_path, "walk-forward plan"),
        _read_json(recession_truth_path, "recession truth"),
        _read_json(stress_truth_path, "stress truth"),
        _read_json(candidate_path, "E11 challenger config"),
        _read_json(gate_path, "E11 gate"),
        _read_json(manifest_path, "E11 preregistration manifest"),
    ]
    (evaluation_file, evaluation_bytes, evaluation), (plan_file, plan_bytes, plan), \
        (recession_file, recession_bytes, recession), (stress_file, stress_bytes, stress), \
        (candidate_file, candidate_bytes, candidate), (gate_file, gate_bytes, gate), \
        (manifest_file, manifest_bytes, manifest) = sources
    periods = validate_recession_truth(recession)
    taxonomy, episodes = validate_stress_truth(stress)
    _validate_contracts(
        dataset.sha256, evaluation, evaluation_bytes, plan_bytes, recession_bytes,
        stress_bytes, candidate_bytes, candidate, gate_bytes, gate, manifest,
    )
    rows = sorted(evaluation["rows"], key=lambda item: item["asOfDate"])
    by_date = {item["asOfDate"]: item for item in rows}
    if set(by_date) != {item["asOfDate"] for item in dataset.rows}:
        raise DatasetValidationError("E11.3 evaluation dates do not match dataset dates.")
    folds = plan.get("folds")
    inner_years = int(plan.get("config", {}).get("testYears", 0))
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds) or inner_years <= 0:
        raise DatasetValidationError("E11.3 walk-forward plan is invalid.")

    fold_reports: list[dict[str, Any]] = []
    unique: dict[str, dict[str, Any]] = {}
    runner: Callable[..., tuple[list[dict[str, Any]], dict[str, Any]]]
    runner = _run_changepoint_fold if candidate["modelId"] == "changepoint-duration-v1" else _run_logit_fold
    for fold in sorted(folds, key=lambda item: item["number"]):
        train_from = date.fromisoformat(fold["train_from"])
        train_to = date.fromisoformat(fold["train_to"])
        test_from = date.fromisoformat(fold["test_from"])
        if train_to >= test_from:
            raise DatasetValidationError("E11.3 outer train/test windows overlap.")
        inner_from = _add_years(train_to, -inner_years)
        fit_dates = [key for key in sorted(by_date) if train_from <= date.fromisoformat(key) <= inner_from]
        validation_dates = [key for key in sorted(by_date) if inner_from < date.fromisoformat(key) <= train_to]
        if not fit_dates or not validation_dates or any(date.fromisoformat(key) >= test_from for key in validation_dates):
            raise DatasetValidationError("E11.3 inner fit/validation boundaries are invalid.")
        predictions, fit = runner(fit_dates, validation_dates, by_date, periods, candidate)
        for prediction in predictions:
            unique.setdefault(prediction["asOfDate"], prediction)
        fold_reports.append({
            "number": fold["number"],
            "outerTrainFrom": fold["train_from"],
            "outerTrainTo": fold["train_to"],
            "innerFitFrom": fit_dates[0],
            "innerFitTo": fit_dates[-1],
            "innerFitRowCount": len(fit_dates),
            "innerValidationFrom": validation_dates[0],
            "innerValidationTo": validation_dates[-1],
            "innerValidationRowCount": len(validation_dates),
            "outerTestFrom": fold["test_from"],
            "outerTestTo": fold["test_to"],
            "outerTestRowCountUsed": 0,
            "eligible": bool(fit["eligible"]),
            "fit": fit,
        })

    keys = sorted(unique)
    actual = {key: is_recession(key, periods) for key in keys}
    predicted = {key: bool(unique[key]["predictedRecession"]) for key in keys}
    probabilities = {key: float(unique[key]["recessionProbability"]) for key in keys}
    baseline_binary = {key: by_date[key]["operationalRegime"] == "DeflationBust" for key in keys}
    baseline_probabilities = {key: _baseline_probability(by_date[key]) for key in keys}
    metrics, baseline_metrics = binary_metrics(actual, predicted), binary_metrics(actual, baseline_binary)
    prob_metrics, baseline_prob_metrics = probability_metrics(actual, probabilities), probability_metrics(actual, baseline_probabilities)
    delta = metric_delta(metrics, baseline_metrics)
    prob_delta = {
        "brierScore": round(prob_metrics["brierScore"] - baseline_prob_metrics["brierScore"], 8),
        "averagePrecision": _optional_delta(prob_metrics["averagePrecision"], baseline_prob_metrics["averagePrecision"]),
    }
    calibration = calibration_table(actual, probabilities, 5)
    fp_run_delta = _false_positive_run(actual, predicted) - _false_positive_run(actual, baseline_binary)
    protected = _protected_stress_hit_rate(keys, unique, taxonomy, episodes)
    thresholds = gate["innerValidation"]
    eligible_count = sum(item["eligible"] for item in fold_reports)
    checks = {
        "minimumEligibleFolds": eligible_count >= int(thresholds["minimumEligibleFolds"]),
        "recallDelta": _minimum_optional(delta["recall"], thresholds["minimumRecallDeltaVsBaseline"]),
        "f1Delta": _minimum_optional(delta["f1"], thresholds["minimumF1DeltaVsBaseline"]),
        "brierDelta": prob_delta["brierScore"] <= float(thresholds["maximumBrierDeltaVsBaseline"]),
        "averagePrecisionDelta": _minimum_optional(prob_delta["averagePrecision"], thresholds["minimumAveragePrecisionDeltaVsBaseline"]),
        "expectedCalibrationError": calibration["expectedCalibrationError"] <= float(thresholds["maximumExpectedCalibrationError"]),
        "falsePositiveRunDelta": fp_run_delta <= int(thresholds["maximumFalsePositiveRunDeltaMonths"]),
        "protectedStressDimensionHitRate": protected["hitRate"] is not None and protected["hitRate"] >= float(thresholds["minimumProtectedStressDimensionHitRate"]),
    }
    passed = all(checks.values())
    report = {
        "reportVersion": 1,
        "reportType": "E11ChallengerInnerGate",
        "modelId": candidate["modelId"],
        "inputs": {
            "datasetSha256": dataset.sha256,
            "baselineEvaluationFileName": evaluation_file.name,
            "baselineEvaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "recessionGroundTruthFileName": recession_file.name,
            "recessionGroundTruthSha256": hashlib.sha256(recession_bytes).hexdigest(),
            "stressGroundTruthFileName": stress_file.name,
            "stressGroundTruthSha256": hashlib.sha256(stress_bytes).hexdigest(),
            "candidateConfigFileName": candidate_file.name,
            "candidateConfigSha256": hashlib.sha256(candidate_bytes).hexdigest(),
            "gateFileName": gate_file.name,
            "gateSha256": hashlib.sha256(gate_bytes).hexdigest(),
            "preregistrationManifestFileName": manifest_file.name,
            "preregistrationManifestSha256": hashlib.sha256(manifest_bytes).hexdigest(),
        },
        "protocol": {
            "scope": "inner-validation-only",
            "innerValidationYears": inner_years,
            "innerValidationSource": "walk-forward plan testYears",
            "uniqueDateAggregation": "earliest eligible fold wins",
            "outerTestRowCountUsed": 0,
            "calibrationBins": 5,
            "labelUse": "fit labels come only from inner-fit; validation labels are attached after probabilities and used only by the declared threshold selector and gate",
        },
        "coverage": {
            "foldCount": len(fold_reports),
            "eligibleFoldCount": eligible_count,
            "uniqueInnerValidationRowCount": len(keys),
            "from": keys[0],
            "to": keys[-1],
        },
        "challengerMetrics": metrics,
        "baselineMetrics": baseline_metrics,
        "deltaVsBaseline": delta,
        "challengerProbabilityMetrics": prob_metrics,
        "baselineProbabilityMetrics": baseline_prob_metrics,
        "probabilityDeltaVsBaseline": prob_delta,
        "calibration": calibration,
        "falsePositiveRunDeltaMonths": fp_run_delta,
        "protectedStressDiagnostics": protected,
        "gate": {
            "status": "ELIGIBLE_FOR_SHADOW_REVIEW" if passed else "REJECTED_FOR_SHADOW",
            "passed": passed,
            "checks": checks,
            "maximumLifecycle": "shadow-candidate",
            "operationalApprovalAuthorized": False,
        },
        "folds": fold_reports,
        "predictions": [{**unique[key], "actualRecession": actual[key]} for key in keys],
        "implementation": {
            "module": "regime_eval.e11_challengers",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _run_changepoint_fold(
    fit_dates: list[str], validation_dates: list[str], rows: dict[str, dict[str, Any]],
    periods: list[dict[str, Any]], config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    timeline = fit_dates + validation_dates
    dimensions = {key: dimension_scores(rows[key]) for key in timeline}
    changes = {
        key: _dimension_change(dimensions, timeline, index)
        for index, key in enumerate(timeline)
    }
    configured = config["trainOnlyRobustScaling"]
    centers, scales = {}, {}
    for dimension in ("growthDeterioration", "financialStress"):
        values = [changes[key][dimension] for key in fit_dates]
        center = median(values)
        mad = median(abs(value - center) for value in values)
        centers[dimension] = center
        scales[dimension] = max(float(configured["minimumScale"]), 1.4826 * mad)
    state = {"active": False, "duration": 0, "exitStreak": 0}
    for key in fit_dates:
        _changepoint_step(dimensions[key], changes[key], centers, scales, state, config)
    predictions = []
    for key in validation_dates:
        result = _changepoint_step(dimensions[key], changes[key], centers, scales, state, config)
        predictions.append({
            "asOfDate": key,
            "predictedRecession": result["active"],
            "recessionProbability": result["probability"],
            "changeScore": result["changeScore"],
            "stateDurationMonths": result["duration"],
            "dimensions": dimensions[key],
        })
    return predictions, {
        "eligible": True,
        "scalingCenters": {key: round(value, 8) for key, value in centers.items()},
        "scalingScales": {key: round(value, 8) for key, value in scales.items()},
        "probabilityFormula": "sigmoid(max(changeScore / robustZThreshold, financialStress / extremeFinancialStressLevel) - 1)",
    }


def _dimension_change(dimensions: dict[str, dict[str, float]], timeline: list[str], index: int) -> dict[str, float]:
    if index == 0:
        return {"growthDeterioration": 0.0, "financialStress": 0.0}
    current, previous = dimensions[timeline[index]], dimensions[timeline[index - 1]]
    return {key: current[key] - previous[key] for key in ("growthDeterioration", "financialStress")}


def _changepoint_step(
    dimensions: dict[str, float], changes: dict[str, float], centers: dict[str, float],
    scales: dict[str, float], state: dict[str, Any], config: dict[str, Any],
) -> dict[str, Any]:
    z = {
        key: (changes[key] - centers[key]) / scales[key]
        for key in ("growthDeterioration", "financialStress")
    }
    score = max(0.0, z["growthDeterioration"], z["financialStress"])
    entry, duration = config["entryPolicy"], config["durationPolicy"]
    financial = dimensions["financialStress"]
    growth = dimensions["growthDeterioration"]
    enters = (
        score >= float(entry["robustZThreshold"])
        and financial >= float(entry["minimumFinancialStressLevel"])
    ) or financial >= float(entry["extremeFinancialStressLevel"])
    if not state["active"]:
        if enters:
            state.update(active=True, duration=1, exitStreak=0)
    else:
        state["duration"] += 1
        exit_condition = (
            financial < float(duration["exitFinancialStressLevel"])
            and growth < float(duration["exitGrowthDeteriorationLevel"])
        )
        state["exitStreak"] = state["exitStreak"] + 1 if exit_condition else 0
        normal_exit = (
            state["duration"] >= int(duration["minimumStateMonths"])
            and state["exitStreak"] >= int(duration["consecutiveExitMonths"])
        )
        forced_exit = (
            state["duration"] > int(duration["maximumStateMonths"])
            and financial < 0.70
        )
        if normal_exit or forced_exit:
            state.update(active=False, duration=0, exitStreak=0)
    driver = max(
        score / float(entry["robustZThreshold"]),
        financial / float(entry["extremeFinancialStressLevel"]),
    )
    return {
        "active": bool(state["active"]),
        "duration": int(state["duration"]),
        "changeScore": round(score, 8),
        "probability": round(_sigmoid(driver - 1.0), 8),
    }


def _run_logit_fold(
    fit_dates: list[str], validation_dates: list[str], rows: dict[str, dict[str, Any]],
    periods: list[dict[str, Any]], config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    timeline = fit_dates + validation_dates
    vectors = _logit_vectors(timeline, rows, config)
    labels = {key: is_recession(key, periods) for key in timeline}
    positive = sum(labels[key] for key in fit_dates)
    negative = len(fit_dates) - positive
    if positive == 0:
        return [], {"eligible": False, "reason": "NO_POSITIVE_INNER_FIT"}
    means = [fmean(vectors[key][index] for key in fit_dates) for index in range(len(vectors[fit_dates[0]]))]
    scales = []
    for index, mean in enumerate(means):
        variance = fmean((vectors[key][index] - mean) ** 2 for key in fit_dates)
        scales.append(max(math.sqrt(variance), 1e-12))
    standardized = {key: [(value - means[index]) / scales[index] for index, value in enumerate(vectors[key])] for key in timeline}
    positive_weight = min(float(config["rareEventPolicy"]["maximumPositiveClassWeight"]), negative / positive)
    coefficients, iterations, converged = _fit_weighted_logit(
        [standardized[key] for key in fit_dates],
        [labels[key] for key in fit_dates],
        positive_weight,
        config["optimizer"],
    )
    probabilities = {key: _logit_probability(coefficients, standardized[key]) for key in validation_dates}
    threshold, threshold_table = _select_threshold(validation_dates, labels, probabilities, config)
    predictions = [{
        "asOfDate": key,
        "predictedRecession": probabilities[key] >= threshold,
        "recessionProbability": round(probabilities[key], 8),
        "selectedThreshold": threshold,
        "dimensions": dimension_scores(rows[key]),
    } for key in validation_dates]
    return predictions, {
        "eligible": True,
        "positiveFitCount": positive,
        "negativeFitCount": negative,
        "positiveClassWeight": round(positive_weight, 8),
        "iterations": iterations,
        "converged": converged,
        "selectedThreshold": threshold,
        "thresholdSelection": threshold_table,
        "coefficients": [round(value, 8) for value in coefficients],
    }


def _logit_vectors(timeline: list[str], rows: dict[str, dict[str, Any]], config: dict[str, Any]) -> dict[str, list[float]]:
    levels = config["levelFeatures"]
    differences = config["differenceFeatures"]
    raw = {key: {item["featureCode"]: float(item["normalizedScore"]) for item in rows[key]["featureScores"]} for key in timeline}
    vectors = {}
    for index, key in enumerate(timeline):
        previous = raw[timeline[index - 1]] if index else raw[key]
        vectors[key] = [raw[key][code] for code in levels] + [raw[key][code] - previous[code] for code in differences]
    return vectors


def _fit_weighted_logit(vectors: list[list[float]], labels: list[bool], positive_weight: float, optimizer: dict[str, Any]) -> tuple[list[float], int, bool]:
    coefficients = [0.0] * (len(vectors[0]) + 1)
    rate = float(optimizer["learningRate"])
    penalty = float(optimizer["l2Penalty"])
    tolerance = float(optimizer["convergenceTolerance"])
    weight_sum = sum(positive_weight if label else 1.0 for label in labels)
    for iteration in range(1, int(optimizer["maximumIterations"]) + 1):
        gradient = [0.0] * len(coefficients)
        for vector, label in zip(vectors, labels):
            probability = _logit_probability(coefficients, vector)
            weight = positive_weight if label else 1.0
            error = weight * (probability - float(label))
            gradient[0] += error
            for index, value in enumerate(vector, start=1):
                gradient[index] += error * value
        gradient[0] /= weight_sum
        for index in range(1, len(gradient)):
            gradient[index] = gradient[index] / weight_sum + penalty * coefficients[index] / len(vectors)
        updates = [rate * value for value in gradient]
        coefficients = [value - update for value, update in zip(coefficients, updates)]
        if max(abs(value) for value in updates) <= tolerance:
            return coefficients, iteration, True
    return coefficients, int(optimizer["maximumIterations"]), False


def _select_threshold(dates: list[str], labels: dict[str, bool], probabilities: dict[str, float], config: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
    table = []
    brier = probability_metrics(
        {key: labels[key] for key in dates}, {key: probabilities[key] for key in dates}
    )["brierScore"]
    for threshold in config["decisionThresholdPolicy"]["candidates"]:
        predicted = {key: probabilities[key] >= float(threshold) for key in dates}
        metrics = binary_metrics({key: labels[key] for key in dates}, predicted)
        table.append({
            "threshold": float(threshold),
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "brierScore": brier,
        })
    eligible = [item for item in table if item["recall"] is not None and item["recall"] >= 0.50]
    if not eligible:
        return float(config["decisionThresholdPolicy"]["fallback"]), table
    selected = max(
        eligible,
        key=lambda item: (
            item["f1"] if item["f1"] is not None else -1.0,
            -item["brierScore"],
            item["threshold"],
        ),
    )
    return float(selected["threshold"]), table


def _logit_probability(coefficients: list[float], vector: list[float]) -> float:
    return _sigmoid(coefficients[0] + sum(weight * value for weight, value in zip(coefficients[1:], vector)))


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-min(value, 700.0)))
    exponential = math.exp(max(value, -700.0))
    return exponential / (1.0 + exponential)


def _validate_contracts(
    dataset_sha: str, evaluation: Any, evaluation_bytes: bytes, plan_bytes: bytes,
    recession_bytes: bytes, stress_bytes: bytes, candidate_bytes: bytes,
    candidate: Any, gate_bytes: bytes, gate: Any, manifest: Any,
) -> None:
    if not isinstance(evaluation, dict) or evaluation.get("schemaVersion") != 1 or evaluation.get("datasetSha256") != dataset_sha or not isinstance(evaluation.get("rows"), list):
        raise DatasetValidationError("E11.3 baseline evaluation is invalid.")
    model_id = candidate.get("modelId") if isinstance(candidate, dict) else None
    if model_id not in {"changepoint-duration-v1", "rare-event-logit-v1"} or candidate.get("benchmarkScope") != "inner-validation-only":
        raise DatasetValidationError("E11.3 challenger config is invalid.")
    expected = candidate.get("expectedInputs", {})
    actual = {
        "datasetSha256": dataset_sha,
        "baselineEvaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
        "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
        "recessionGroundTruthSha256": hashlib.sha256(recession_bytes).hexdigest(),
        "stressGroundTruthSha256": hashlib.sha256(stress_bytes).hexdigest(),
    }
    if expected != actual:
        raise DatasetValidationError("E11.3 frozen input hashes do not match.")
    if not isinstance(gate, dict) or model_id not in gate.get("registeredModelIds", []) or gate.get("targetLifecycle") != "shadow-candidate":
        raise DatasetValidationError("E11.3 gate does not register the challenger.")
    if not isinstance(manifest, dict) or manifest.get("gate", {}).get("sha256") != hashlib.sha256(gate_bytes).hexdigest() or manifest.get("expectedInputs") != expected:
        raise DatasetValidationError("E11.3 manifest does not bind the gate and inputs.")
    registered = {item.get("modelId"): item for item in manifest.get("candidates", []) if isinstance(item, dict)}
    if registered.get(model_id, {}).get("configSha256") != hashlib.sha256(candidate_bytes).hexdigest():
        raise DatasetValidationError("E11.3 manifest does not bind the challenger config.")
    if model_id == "changepoint-duration-v1":
        if candidate.get("changeScore") != "max positive robust-z innovation across growthDeterioration and financialStress":
            raise DatasetValidationError("E11.3 changepoint formula is not frozen.")
    else:
        optimizer = candidate.get("optimizer", {})
        if candidate.get("decisionThresholdPolicy", {}).get("candidates") != [0.25, 0.35, 0.5] or optimizer.get("algorithm") != "deterministic batch gradient descent":
            raise DatasetValidationError("E11.3 logit policy is not frozen.")
