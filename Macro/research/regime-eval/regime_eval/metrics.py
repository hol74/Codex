from __future__ import annotations

import math
from typing import Any

from .dataset import DatasetValidationError


def binary_metrics(actual: dict[str, bool], predicted: dict[str, bool]) -> dict[str, Any]:
    if set(actual) != set(predicted):
        raise DatasetValidationError("Actual and predicted keys do not match.")
    tp = sorted(key for key in actual if actual[key] and predicted[key])
    fp = sorted(key for key in actual if not actual[key] and predicted[key])
    tn = sorted(key for key in actual if not actual[key] and not predicted[key])
    fn = sorted(key for key in actual if actual[key] and not predicted[key])
    recall = ratio(len(tp), len(tp) + len(fn))
    specificity = ratio(len(tn), len(tn) + len(fp))
    return {
        "confusionMatrix": {
            "truePositive": len(tp),
            "falsePositive": len(fp),
            "trueNegative": len(tn),
            "falseNegative": len(fn),
        },
        "recall": recall,
        "precision": ratio(len(tp), len(tp) + len(fp)),
        "specificity": specificity,
        "accuracy": ratio(len(tp) + len(tn), len(actual)),
        "balancedAccuracy": (
            round((recall + specificity) / 2, 8)
            if recall is not None and specificity is not None
            else None
        ),
        "f1": ratio(2 * len(tp), (2 * len(tp)) + len(fp) + len(fn)),
        "falsePositiveKeys": fp,
        "falseNegativeKeys": fn,
    }


def metric_delta(challenger: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key in ("recall", "precision", "specificity", "accuracy", "balancedAccuracy", "f1"):
        left, right = challenger[key], baseline[key]
        output[key] = round(left - right, 8) if left is not None and right is not None else None
    output["falsePositiveCount"] = (
        challenger["confusionMatrix"]["falsePositive"]
        - baseline["confusionMatrix"]["falsePositive"]
    )
    output["falseNegativeCount"] = (
        challenger["confusionMatrix"]["falseNegative"]
        - baseline["confusionMatrix"]["falseNegative"]
    )
    return output


def probability_metrics(
    actual: dict[str, bool], probabilities: dict[str, float]
) -> dict[str, Any]:
    if set(actual) != set(probabilities):
        raise DatasetValidationError("Actual and probability keys do not match.")
    if not actual:
        raise DatasetValidationError("Probability metrics require at least one observation.")
    for key, value in probabilities.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise DatasetValidationError(f"Probability for '{key}' is not numeric.")
        if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
            raise DatasetValidationError(f"Probability for '{key}' must be between zero and one.")
    brier = sum((float(probabilities[key]) - float(actual[key])) ** 2 for key in actual) / len(actual)
    epsilon = 1e-15
    log_loss = -sum(
        math.log(min(1.0 - epsilon, max(epsilon, float(probabilities[key]))))
        if actual[key]
        else math.log(min(1.0 - epsilon, max(epsilon, 1.0 - float(probabilities[key]))))
        for key in actual
    ) / len(actual)
    return {
        "brierScore": round(brier, 8),
        "logLoss": round(log_loss, 8),
        "averagePrecision": average_precision(actual, probabilities),
    }


def average_precision(actual: dict[str, bool], probabilities: dict[str, float]) -> float | None:
    positive_count = sum(actual.values())
    if positive_count == 0:
        return None
    ranked = sorted(actual, key=lambda key: (-float(probabilities[key]), key))
    hits = 0
    total = 0.0
    for rank, key in enumerate(ranked, start=1):
        if actual[key]:
            hits += 1
            total += hits / rank
    return round(total / positive_count, 8)


def calibration_table(
    actual: dict[str, bool], probabilities: dict[str, float], bin_count: int
) -> dict[str, Any]:
    if not isinstance(bin_count, int) or bin_count < 2:
        raise DatasetValidationError("Calibration bin count must be at least two.")
    probability_metrics(actual, probabilities)
    bins: list[dict[str, Any]] = []
    weighted_error = 0.0
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        keys = [
            key
            for key, value in probabilities.items()
            if lower <= float(value) <= upper
            and (index == bin_count - 1 or float(value) < upper)
        ]
        mean_probability = (
            sum(float(probabilities[key]) for key in keys) / len(keys) if keys else None
        )
        observed_rate = sum(actual[key] for key in keys) / len(keys) if keys else None
        if mean_probability is not None and observed_rate is not None:
            weighted_error += len(keys) * abs(mean_probability - observed_rate)
        bins.append({
            "lowerInclusive": round(lower, 8),
            "upperInclusive": round(upper, 8),
            "rowCount": len(keys),
            "meanProbability": round(mean_probability, 8) if mean_probability is not None else None,
            "observedRate": round(observed_rate, 8) if observed_rate is not None else None,
        })
    return {
        "method": "fixed equal-width bins preregistered before report execution",
        "binCount": bin_count,
        "expectedCalibrationError": round(weighted_error / len(actual), 8),
        "bins": bins,
    }


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 8) if denominator else None
