from __future__ import annotations

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


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 8) if denominator else None
