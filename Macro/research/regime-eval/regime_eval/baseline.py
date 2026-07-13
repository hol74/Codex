from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import fmean, median
from typing import Any, Iterable

from .dataset import DatasetValidationError, load_dataset


def write_baseline_report(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    _validate_evaluation(evaluation, dataset.sha256)

    evaluation_rows = {row["asOfDate"]: row for row in evaluation["rows"]}
    dataset_rows = {row["asOfDate"]: row for row in dataset.rows}
    if set(evaluation_rows) != set(dataset_rows):
        raise DatasetValidationError("Baseline evaluation dates do not exactly match dataset dates.")

    folds = plan.get("folds")
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")

    confirmation_threshold = float(evaluation["confirmationThreshold"])
    fold_reports: list[dict[str, Any]] = []
    unique_test_dates: set[str] = set()
    for fold in folds:
        test_from = _iso_date(fold.get("test_from"), "fold.test_from")
        test_to = _iso_date(fold.get("test_to"), "fold.test_to")
        dates = sorted(key for key in evaluation_rows if test_from <= date.fromisoformat(key) <= test_to)
        unique_test_dates.update(dates)
        fold_reports.append(
            {
                "number": fold.get("number"),
                "trainFrom": fold.get("train_from"),
                "trainTo": fold.get("train_to"),
                "testFrom": fold.get("test_from"),
                "testTo": fold.get("test_to"),
                **_summarize(dates, evaluation_rows, dataset_rows, confirmation_threshold, conditional=False),
            }
        )

    aggregate_dates = sorted(unique_test_dates)
    report = {
        "reportVersion": 1,
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "evaluationFileName": evaluation_file.name,
            "evaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
        },
        "baseline": {
            "modelName": evaluation["modelName"],
            "modelVersion": evaluation["modelVersion"],
            "modelEffectiveFrom": evaluation["modelEffectiveFrom"],
            "featureSetName": evaluation["featureSetName"],
            "featureSetVersion": evaluation["featureSetVersion"],
            "confirmationThreshold": confirmation_threshold,
        },
        "methodology": {
            "role": "fixed rule-based benchmark; no parameters are fitted on train or test",
            "historicalStatus": "retrospective application of the current baseline; not an ex-ante live-performance claim",
            "aggregation": "fold metrics preserve overlapping test windows; aggregate metrics use each test date once",
            "accuracyStatus": "not computed: no versioned external regime ground truth is included yet",
            "returnsStatus": "descriptive conditional forward returns; not a trading strategy or promotion score",
        },
        "coverage": {
            "predictionRowCount": len(evaluation_rows),
            "foldCount": len(fold_reports),
            "foldObservationCount": sum(item["rowCount"] for item in fold_reports),
            "uniqueOutOfSampleRowCount": len(aggregate_dates),
            "uniqueOutOfSampleFrom": aggregate_dates[0] if aggregate_dates else None,
            "uniqueOutOfSampleTo": aggregate_dates[-1] if aggregate_dates else None,
        },
        "aggregateOutOfSample": _summarize(
            aggregate_dates, evaluation_rows, dataset_rows, confirmation_threshold, conditional=True
        ),
        "folds": fold_reports,
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination.resolve()


def _summarize(
    dates: list[str],
    evaluations: dict[str, dict[str, Any]],
    dataset_rows: dict[str, dict[str, Any]],
    threshold: float,
    *,
    conditional: bool,
) -> dict[str, Any]:
    rows = [evaluations[key] for key in dates]
    confidences = [float(row["confidence"]) for row in rows]
    operational = [str(row["operationalRegime"]) for row in rows]
    primary = [str(row["primaryRegime"]) for row in rows]
    missing = [any("missing" in str(item).casefold() for item in row.get("warnings", [])) for row in rows]
    transitions = sum(current != previous for previous, current in zip(operational, operational[1:]))
    result: dict[str, Any] = {
        "rowCount": len(rows),
        "meanConfidence": _round(fmean(confidences)) if confidences else None,
        "medianConfidence": _round(median(confidences)) if confidences else None,
        "uncertainTransitionRate": _rate(sum(item == "UncertainTransition" for item in operational), len(rows)),
        "belowConfirmationThresholdRate": _rate(sum(item < threshold for item in confidences), len(rows)),
        "missingFeatureRate": _rate(sum(missing), len(rows)),
        "operationalTransitionRate": _rate(transitions, max(0, len(rows) - 1)),
        "primaryRegimeDistribution": _distribution(primary),
        "operationalRegimeDistribution": _distribution(operational),
        "assetForwardReturns": _forward_return_summary(dates, dataset_rows),
    }
    if conditional:
        result["regimeConditionalForwardReturns"] = _forward_return_summary(
            dates, dataset_rows, {key: evaluations[key]["operationalRegime"] for key in dates}
        )
    return result


def _forward_return_summary(
    dates: Iterable[str],
    dataset_rows: dict[str, dict[str, Any]],
    regimes: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for key in dates:
        for item in dataset_rows[key].get("forwardReturns", []):
            prefix = (str(regimes[key]),) if regimes is not None else ()
            group_key = prefix + (str(item["symbol"]), str(item["horizonDays"]))
            grouped[group_key].append(float(item["returnValue"]))

    output = []
    for key, values in sorted(grouped.items()):
        offset = 1 if regimes is not None else 0
        item: dict[str, Any] = {
            "symbol": key[offset],
            "horizonDays": int(key[offset + 1]),
            "count": len(values),
            "meanReturn": _round(fmean(values)),
            "medianReturn": _round(median(values)),
            "positiveRate": _rate(sum(value > 0 for value in values), len(values)),
        }
        if regimes is not None:
            item["operationalRegime"] = key[0]
        output.append(item)
    return output


def _distribution(values: list[str]) -> list[dict[str, Any]]:
    counts = Counter(values)
    return [
        {"regime": key, "count": counts[key], "rate": _rate(counts[key], len(values))}
        for key in sorted(counts)
    ]


def _validate_evaluation(evaluation: Any, dataset_sha256: str) -> None:
    if not isinstance(evaluation, dict) or evaluation.get("schemaVersion") != 1:
        raise DatasetValidationError("Unsupported baseline evaluation schema.")
    if evaluation.get("datasetSha256") != dataset_sha256:
        raise DatasetValidationError("Baseline evaluation dataset SHA-256 does not match the dataset.")
    if not isinstance(evaluation.get("rows"), list):
        raise DatasetValidationError("Baseline evaluation rows must be an array.")
    for index, row in enumerate(evaluation["rows"]):
        if not isinstance(row, dict):
            raise DatasetValidationError(f"Baseline evaluation rows[{index}] must be an object.")
        _iso_date(row.get("asOfDate"), f"baseline rows[{index}].asOfDate")
        if not row.get("primaryRegime") or not row.get("operationalRegime"):
            raise DatasetValidationError(f"Baseline evaluation rows[{index}] has no regime.")
        confidence = row.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise DatasetValidationError(f"Baseline evaluation rows[{index}].confidence is invalid.")


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


def _rate(numerator: int, denominator: int) -> float | None:
    return _round(numerator / denominator) if denominator else None


def _round(value: float) -> float:
    return round(value, 8)
