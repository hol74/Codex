from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset


def write_recession_report(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    ground_truth_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    truth_file, truth_bytes, truth = _read_json(ground_truth_path, "recession ground truth")
    periods = validate_recession_truth(truth)
    _validate_evaluation(evaluation, dataset.sha256)

    evaluation_rows = {row["asOfDate"]: row for row in evaluation["rows"]}
    dataset_dates = [row["asOfDate"] for row in dataset.rows]
    coverage_from = _iso_date(truth["coverageFrom"], "coverageFrom")
    coverage_to = _iso_date(truth["coverageTo"], "coverageTo")
    if coverage_from > coverage_to or any(
        not coverage_from <= date.fromisoformat(value) <= coverage_to for value in dataset_dates
    ):
        raise DatasetValidationError("Recession ground-truth coverage does not contain every dataset date.")
    if set(evaluation_rows) != set(dataset_dates):
        raise DatasetValidationError("Baseline evaluation dates do not exactly match dataset dates.")

    folds = plan.get("folds")
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")

    fold_reports: list[dict[str, Any]] = []
    unique_test_dates: set[str] = set()
    for fold in folds:
        test_from = _iso_date(fold.get("test_from"), "fold.test_from")
        test_to = _iso_date(fold.get("test_to"), "fold.test_to")
        dates = sorted(key for key in evaluation_rows if test_from <= date.fromisoformat(key) <= test_to)
        unique_test_dates.update(dates)
        fold_reports.append({
            "number": fold.get("number"),
            "testFrom": fold.get("test_from"),
            "testTo": fold.get("test_to"),
            "rowCount": len(dates),
            "actualRecessionCount": sum(is_recession(key, periods) for key in dates),
            "primaryDeflationBust": _signal_metrics(dates, evaluation_rows, periods, "primaryRegime"),
            "operationalDeflationBust": _signal_metrics(dates, evaluation_rows, periods, "operationalRegime"),
        })

    unique_dates = sorted(unique_test_dates)
    report = {
        "reportVersion": 1,
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "evaluationFileName": evaluation_file.name,
            "evaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "groundTruthFileName": truth_file.name,
            "groundTruthSha256": hashlib.sha256(truth_bytes).hexdigest(),
        },
        "groundTruth": {
            "id": truth["groundTruthId"],
            "mappingPolicy": truth["mappingPolicy"],
            "coverageFrom": truth["coverageFrom"],
            "coverageTo": truth["coverageTo"],
            "periodCount": len(periods),
            "limitations": truth["limitations"],
        },
        "signalPolicy": {
            "positiveRegime": "DeflationBust",
            "primary": "primaryRegime == DeflationBust",
            "operational": "operationalRegime == DeflationBust",
            "scope": "binary US recession detection only; other regime classes are not scored",
        },
        "coverage": {
            "fullDatasetRowCount": len(dataset_dates),
            "foldCount": len(fold_reports),
            "foldObservationCount": sum(item["rowCount"] for item in fold_reports),
            "uniqueOutOfSampleRowCount": len(unique_dates),
            "uniqueOutOfSampleFrom": unique_dates[0] if unique_dates else None,
            "uniqueOutOfSampleTo": unique_dates[-1] if unique_dates else None,
        },
        "fullDataset": _scope_metrics(dataset_dates, evaluation_rows, periods),
        "aggregateOutOfSample": _scope_metrics(unique_dates, evaluation_rows, periods),
        "folds": fold_reports,
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination.resolve()


def _scope_metrics(
    dates: list[str], evaluation_rows: dict[str, dict[str, Any]], periods: list[dict[str, Any]]
) -> dict[str, Any]:
    recession_dates = [key for key in dates if is_recession(key, periods)]
    uncertain_recession_dates = [
        key for key in recession_dates
        if evaluation_rows[key]["operationalRegime"] == "UncertainTransition"
    ]
    return {
        "rowCount": len(dates),
        "actualRecessionCount": len(recession_dates),
        "actualRecessionPrevalence": _ratio(len(recession_dates), len(dates)),
        "uncertainDuringRecessionCount": len(uncertain_recession_dates),
        "uncertainDuringRecessionRate": _ratio(len(uncertain_recession_dates), len(recession_dates)),
        "primaryDeflationBust": _signal_metrics(dates, evaluation_rows, periods, "primaryRegime"),
        "operationalDeflationBust": _signal_metrics(dates, evaluation_rows, periods, "operationalRegime"),
        "episodeDiagnostics": _episode_diagnostics(dates, evaluation_rows, periods),
    }


def _signal_metrics(
    dates: list[str],
    evaluation_rows: dict[str, dict[str, Any]],
    periods: list[dict[str, Any]],
    field: str,
) -> dict[str, Any]:
    true_positive: list[str] = []
    false_positive: list[str] = []
    true_negative: list[str] = []
    false_negative: list[str] = []
    for key in dates:
        actual = is_recession(key, periods)
        predicted = evaluation_rows[key][field] == "DeflationBust"
        if actual and predicted:
            true_positive.append(key)
        elif predicted:
            false_positive.append(key)
        elif actual:
            false_negative.append(key)
        else:
            true_negative.append(key)

    tp, fp, tn, fn = map(len, (true_positive, false_positive, true_negative, false_negative))
    recall = _ratio(tp, tp + fn)
    specificity = _ratio(tn, tn + fp)
    precision = _ratio(tp, tp + fp)
    return {
        "confusionMatrix": {"truePositive": tp, "falsePositive": fp, "trueNegative": tn, "falseNegative": fn},
        "recall": recall,
        "falseNegativeRate": _ratio(fn, tp + fn),
        "specificity": specificity,
        "falsePositiveRate": _ratio(fp, tn + fp),
        "precision": precision,
        "accuracy": _ratio(tp + tn, tp + fp + tn + fn),
        "balancedAccuracy": _average(recall, specificity),
        "f1": _ratio(2 * tp, (2 * tp) + fp + fn),
        "falseNegativeDates": false_negative,
        "falsePositiveDates": false_positive,
    }


def _episode_diagnostics(
    dates: list[str], evaluation_rows: dict[str, dict[str, Any]], periods: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    available = [date.fromisoformat(key) for key in dates]
    diagnostics = []
    for period in periods:
        episode_dates = [item for item in available if period["first"] <= item.replace(day=1) <= period["trough"]]
        if not episode_dates:
            continue
        first_sample = min(episode_dates)
        primary = [item for item in episode_dates if evaluation_rows[item.isoformat()]["primaryRegime"] == "DeflationBust"]
        operational = [item for item in episode_dates if evaluation_rows[item.isoformat()]["operationalRegime"] == "DeflationBust"]
        diagnostics.append({
            "name": period["name"],
            "firstAvailableRecessionSample": first_sample.isoformat(),
            "availableRecessionSampleCount": len(episode_dates),
            "firstPrimarySignal": min(primary).isoformat() if primary else None,
            "primaryDetectionLagMonths": _month_difference(first_sample, min(primary)) if primary else None,
            "firstOperationalSignal": min(operational).isoformat() if operational else None,
            "operationalDetectionLagMonths": _month_difference(first_sample, min(operational)) if operational else None,
        })
    return diagnostics


def validate_recession_truth(truth: Any) -> list[dict[str, Any]]:
    if not isinstance(truth, dict) or truth.get("schemaVersion") != 1:
        raise DatasetValidationError("Unsupported recession ground-truth schema.")
    required = ("groundTruthId", "mappingPolicy", "coverageFrom", "coverageTo", "limitations")
    if any(key not in truth for key in required) or not isinstance(truth.get("periods"), list):
        raise DatasetValidationError("Recession ground truth is incomplete.")
    periods = []
    previous_trough: date | None = None
    for index, item in enumerate(truth["periods"]):
        peak = _iso_date(item.get("peakMonth"), f"periods[{index}].peakMonth")
        first = _iso_date(item.get("firstRecessionMonth"), f"periods[{index}].firstRecessionMonth")
        trough = _iso_date(item.get("troughMonth"), f"periods[{index}].troughMonth")
        if first != _next_month(peak) or first > trough:
            raise DatasetValidationError(f"periods[{index}] does not follow the peak-to-trough monthly policy.")
        if previous_trough is not None and first <= previous_trough:
            raise DatasetValidationError("Recession ground-truth periods overlap or are unordered.")
        previous_trough = trough
        periods.append({"name": item.get("name"), "peak": peak, "first": first, "trough": trough})
    return periods


def _validate_evaluation(evaluation: Any, dataset_sha256: str) -> None:
    if not isinstance(evaluation, dict) or evaluation.get("schemaVersion") != 1:
        raise DatasetValidationError("Unsupported baseline evaluation schema.")
    if evaluation.get("datasetSha256") != dataset_sha256 or not isinstance(evaluation.get("rows"), list):
        raise DatasetValidationError("Baseline evaluation does not match the dataset.")


def is_recession(value: str, periods: list[dict[str, Any]]) -> bool:
    month = date.fromisoformat(value).replace(day=1)
    return any(item["first"] <= month <= item["trough"] for item in periods)


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
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid ISO date.") from exc
    if parsed.day != 1 and location.startswith("periods["):
        raise DatasetValidationError(f"{location} must be the first day of a month.")
    return parsed


def _next_month(value: date) -> date:
    return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


def _month_difference(start: date, end: date) -> int:
    return ((end.year - start.year) * 12) + end.month - start.month


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 8) if denominator else None


def _average(first: float | None, second: float | None) -> float | None:
    return round((first + second) / 2, 8) if first is not None and second is not None else None
