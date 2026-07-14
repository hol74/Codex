from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from statistics import fmean
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .dimensions import DIMENSION_NAMES, dimension_scores
from .ground_truth import is_recession, validate_recession_truth


REGIMES = {
    "Goldilocks",
    "Reflation",
    "LateCycleOverheating",
    "Stagflation",
    "DeflationBust",
}


def write_stress_report(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    stress_truth_path: str | Path,
    recession_truth_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    stress_file, stress_bytes, stress_truth = _read_json(stress_truth_path, "stress chronology")
    recession_file, recession_bytes, recession_truth = _read_json(recession_truth_path, "recession ground truth")
    taxonomy, episodes = validate_stress_truth(stress_truth)
    recession_periods = validate_recession_truth(recession_truth)
    _validate_non_recession_scope(episodes, recession_periods)
    _validate_evaluation(evaluation, dataset.sha256)

    evaluation_rows = {row["asOfDate"]: row for row in evaluation["rows"]}
    dataset_dates = [row["asOfDate"] for row in dataset.rows]
    if set(evaluation_rows) != set(dataset_dates):
        raise DatasetValidationError("Baseline evaluation dates do not exactly match dataset dates.")
    _validate_coverage(stress_truth, dataset_dates, "Stress chronology")
    _validate_coverage(recession_truth, dataset_dates, "Recession ground truth")

    folds = plan.get("folds")
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")
    unique_test_dates: set[str] = set()
    for fold in folds:
        test_from = _iso_date(fold.get("test_from"), "fold.test_from")
        test_to = _iso_date(fold.get("test_to"), "fold.test_to")
        unique_test_dates.update(
            key for key in evaluation_rows if test_from <= date.fromisoformat(key) <= test_to
        )

    schema_version = stress_truth["schemaVersion"]
    report = {
        "reportVersion": schema_version,
        "reportType": "DimensionalNonRecessionStressAlignment" if schema_version == 2 else "NonRecessionStressAlignment",
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "evaluationFileName": evaluation_file.name,
            "evaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "stressChronologyFileName": stress_file.name,
            "stressChronologySha256": hashlib.sha256(stress_bytes).hexdigest(),
            "recessionGroundTruthFileName": recession_file.name,
            "recessionGroundTruthSha256": hashlib.sha256(recession_bytes).hexdigest(),
        },
        "chronology": {
            "id": stress_truth["groundTruthId"],
            "evidenceStatus": stress_truth["evidenceStatus"],
            "coverageFrom": stress_truth["coverageFrom"],
            "coverageTo": stress_truth["coverageTo"],
            "labelCount": len(taxonomy),
            "episodeCount": len(episodes),
            "scopePolicy": stress_truth["scopePolicy"],
            "limitations": stress_truth["limitations"],
        },
        "alignmentPolicy": {
            "unit": "each stress label is evaluated independently on labeled months",
            "multiLabel": True,
            "negativeClassMetrics": "not computed",
            "purpose": "descriptive regime alignment; not generic accuracy and not a promotion gate",
            **({
                "dimensionPolicy": "evaluate preregistered dimensions before composite regime alignment",
                "dimensionFormulaVersion": "macro-financial-dimensions-v1",
                "promotionUse": "development-diagnostic-only",
            } if schema_version == 2 else {}),
        },
        "coverage": {
            "fullDatasetRowCount": len(dataset_dates),
            "uniqueOutOfSampleRowCount": len(unique_test_dates),
        },
        "fullDataset": _scope_report(dataset_dates, evaluation_rows, taxonomy, episodes, schema_version),
        "aggregateOutOfSample": _scope_report(
            sorted(unique_test_dates), evaluation_rows, taxonomy, episodes, schema_version
        ),
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def validate_stress_truth(truth: Any) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(truth, dict) or truth.get("schemaVersion") not in {1, 2}:
        raise DatasetValidationError("Unsupported stress chronology schema.")
    required = (
        "groundTruthId",
        "evidenceStatus",
        "scopePolicy",
        "coverageFrom",
        "coverageTo",
        "limitations",
    )
    if any(key not in truth for key in required):
        raise DatasetValidationError("Stress chronology is incomplete.")
    coverage_from = _iso_date(truth["coverageFrom"], "coverageFrom")
    coverage_to = _iso_date(truth["coverageTo"], "coverageTo")
    if coverage_from > coverage_to:
        raise DatasetValidationError("Stress chronology coverage is invalid.")

    sources = truth.get("sources")
    if not isinstance(sources, list) or not sources:
        raise DatasetValidationError("Stress chronology requires sources.")
    source_ids = {item.get("id") for item in sources if isinstance(item, dict)}
    if len(source_ids) != len(sources) or None in source_ids:
        raise DatasetValidationError("Stress chronology source ids must be unique.")

    labels = truth.get("taxonomy")
    if not isinstance(labels, list) or not labels:
        raise DatasetValidationError("Stress chronology requires a taxonomy.")
    taxonomy: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(labels):
        if not isinstance(item, dict) or not isinstance(item.get("code"), str):
            raise DatasetValidationError(f"taxonomy[{index}] is invalid.")
        code = item["code"]
        expected = item.get("expectedPrimaryRegimes")
        if code in taxonomy or not isinstance(expected, list) or not expected or any(
            value not in REGIMES for value in expected
        ):
            raise DatasetValidationError(f"taxonomy[{index}] has invalid code or expected regimes.")
        if truth["schemaVersion"] == 2:
            dimensions = item.get("expectedDimensions")
            if not isinstance(dimensions, dict) or not dimensions:
                raise DatasetValidationError(f"taxonomy[{index}] requires expected dimensions.")
            for dimension, bounds in dimensions.items():
                if dimension not in DIMENSION_NAMES or not isinstance(bounds, dict):
                    raise DatasetValidationError(f"taxonomy[{index}] has an invalid dimension.")
                minimum, maximum = bounds.get("minimum"), bounds.get("maximum")
                if (minimum is None) == (maximum is None):
                    raise DatasetValidationError(f"taxonomy[{index}] dimension must define one bound.")
                bound = minimum if minimum is not None else maximum
                if isinstance(bound, bool) or not isinstance(bound, (int, float)) or not 0 <= bound <= 1:
                    raise DatasetValidationError(f"taxonomy[{index}] dimension bound is invalid.")
        taxonomy[code] = item

    raw_episodes = truth.get("episodes")
    if not isinstance(raw_episodes, list) or not raw_episodes:
        raise DatasetValidationError("Stress chronology requires episodes.")
    episodes: list[dict[str, Any]] = []
    episode_ids: set[str] = set()
    for index, item in enumerate(raw_episodes):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise DatasetValidationError(f"episodes[{index}] is invalid.")
        first = _month(item.get("firstMonth"), f"episodes[{index}].firstMonth")
        last = _month(item.get("lastMonth"), f"episodes[{index}].lastMonth")
        label_codes = item.get("labels")
        references = item.get("sourceIds")
        if (
            item["id"] in episode_ids
            or first > last
            or first < coverage_from.replace(day=1)
            or last > coverage_to.replace(day=1)
            or not isinstance(label_codes, list)
            or not label_codes
            or any(code not in taxonomy for code in label_codes)
            or not isinstance(references, list)
            or not references
            or any(source_id not in source_ids for source_id in references)
            or not isinstance(item.get("boundaryRationale"), str)
            or not item["boundaryRationale"].strip()
            or (truth["schemaVersion"] == 2 and item.get("validationRole") not in {"development-v1", "protected-v2"})
        ):
            raise DatasetValidationError(f"episodes[{index}] has invalid boundaries or references.")
        episode_ids.add(item["id"])
        episodes.append({**item, "first": first, "last": last})
    return taxonomy, episodes


def _scope_report(
    dates: list[str],
    evaluation_rows: dict[str, dict[str, Any]],
    taxonomy: dict[str, dict[str, Any]],
    episodes: list[dict[str, Any]],
    schema_version: int,
) -> dict[str, Any]:
    labels_by_date = {key: _labels_for_date(key, episodes) for key in dates}
    labeled_dates = [key for key, labels in labels_by_date.items() if labels]
    label_reports = {}
    for code, definition in sorted(taxonomy.items()):
        selected = [key for key in dates if code in labels_by_date[key]]
        label_reports[code] = {
            "label": definition["label"],
            "expectedPrimaryRegimes": definition["expectedPrimaryRegimes"],
            **_alignment(selected, evaluation_rows, set(definition["expectedPrimaryRegimes"])),
            **({"dimensionalAlignment": _dimensional_alignment(
                selected, evaluation_rows, definition["expectedDimensions"]
            )} if schema_version == 2 else {}),
        }

    episode_reports = []
    for episode in episodes:
        selected = [key for key in dates if _contains(episode, key)]
        expected = {
            regime
            for code in episode["labels"]
            for regime in taxonomy[code]["expectedPrimaryRegimes"]
        }
        episode_reports.append({
            "id": episode["id"],
            "name": episode["name"],
            "firstMonth": episode["firstMonth"],
            "lastMonth": episode["lastMonth"],
            "labels": episode["labels"],
            "expectedPrimaryRegimes": sorted(expected),
            **_alignment(selected, evaluation_rows, expected),
        })

    report = {
        "rowCount": len(dates),
        "labeledRowCount": len(labeled_dates),
        "unlabeledRowCount": len(dates) - len(labeled_dates),
        "multiLabelRowCount": sum(len(labels) > 1 for labels in labels_by_date.values()),
        "labels": label_reports,
        "episodes": episode_reports,
    }
    if schema_version == 2:
        report["validationPartitions"] = {
            role: _partition_report(dates, evaluation_rows, taxonomy, episodes, role)
            for role in ("development-v1", "protected-v2")
        }
    return report


def _dimensional_alignment(
    dates: list[str],
    evaluation_rows: dict[str, dict[str, Any]],
    expectations: dict[str, dict[str, float]],
) -> dict[str, Any]:
    per_dimension: dict[str, Any] = {}
    all_hits: list[str] = []
    scores_by_date = {key: dimension_scores(evaluation_rows[key]) for key in dates}
    for dimension, bounds in sorted(expectations.items()):
        hits = [key for key in dates if _dimension_hit(scores_by_date[key][dimension], bounds)]
        per_dimension[dimension] = {
            "expectation": bounds,
            "rowCount": len(dates),
            "meanScore": round(fmean(scores_by_date[key][dimension] for key in dates), 8) if dates else None,
            "hitCount": len(hits),
            "hitRate": _ratio(len(hits), len(dates)),
            "mismatchDates": [key for key in dates if key not in hits],
        }
    all_hits = [
        key for key in dates
        if all(_dimension_hit(scores_by_date[key][dimension], bounds) for dimension, bounds in expectations.items())
    ]
    return {
        "allExpectedDimensionsHitCount": len(all_hits),
        "allExpectedDimensionsHitRate": _ratio(len(all_hits), len(dates)),
        "dimensions": per_dimension,
    }


def _partition_report(
    dates: list[str],
    evaluation_rows: dict[str, dict[str, Any]],
    taxonomy: dict[str, dict[str, Any]],
    episodes: list[dict[str, Any]],
    role: str,
) -> dict[str, Any]:
    selected_episodes = [item for item in episodes if item.get("validationRole") == role]
    selected_dates = [key for key in dates if any(_contains(item, key) for item in selected_episodes)]
    label_results: dict[str, Any] = {}
    for code, definition in sorted(taxonomy.items()):
        label_dates = [
            key for key in selected_dates
            if any(_contains(item, key) and code in item["labels"] for item in selected_episodes)
        ]
        label_results[code] = _dimensional_alignment(
            label_dates, evaluation_rows, definition["expectedDimensions"]
        )
    return {"episodeCount": len(selected_episodes), "rowCount": len(set(selected_dates)), "labels": label_results}


def _dimension_hit(value: float, bounds: dict[str, float]) -> bool:
    return value >= float(bounds["minimum"]) if "minimum" in bounds else value <= float(bounds["maximum"])


def _alignment(
    dates: list[str], evaluation_rows: dict[str, dict[str, Any]], expected: set[str]
) -> dict[str, Any]:
    primary = [evaluation_rows[key]["primaryRegime"] for key in dates]
    operational = [evaluation_rows[key]["operationalRegime"] for key in dates]
    primary_hits = [key for key in dates if evaluation_rows[key]["primaryRegime"] in expected]
    operational_hits = [key for key in dates if evaluation_rows[key]["operationalRegime"] in expected]
    uncertain = [key for key in dates if evaluation_rows[key]["operationalRegime"] == "UncertainTransition"]
    return {
        "rowCount": len(dates),
        "primaryDistribution": dict(sorted(Counter(primary).items())),
        "operationalDistribution": dict(sorted(Counter(operational).items())),
        "primaryExpectedCount": len(primary_hits),
        "primaryExpectedRate": _ratio(len(primary_hits), len(dates)),
        "operationalExpectedCount": len(operational_hits),
        "operationalExpectedRate": _ratio(len(operational_hits), len(dates)),
        "operationalUncertainCount": len(uncertain),
        "operationalUncertainRate": _ratio(len(uncertain), len(dates)),
        "primaryMismatchDates": [key for key in dates if key not in primary_hits],
        "operationalMismatchDates": [key for key in dates if key not in operational_hits],
    }


def _validate_non_recession_scope(
    episodes: list[dict[str, Any]], recession_periods: list[dict[str, Any]]
) -> None:
    for episode in episodes:
        current = episode["first"]
        while current <= episode["last"]:
            if is_recession(current.isoformat(), recession_periods):
                raise DatasetValidationError(
                    f"Stress episode '{episode['id']}' overlaps NBER recession month {current:%Y-%m}."
                )
            current = _next_month(current)


def _validate_coverage(truth: dict[str, Any], dates: list[str], label: str) -> None:
    first = _iso_date(truth["coverageFrom"], "coverageFrom")
    last = _iso_date(truth["coverageTo"], "coverageTo")
    if any(not first <= date.fromisoformat(value) <= last for value in dates):
        raise DatasetValidationError(f"{label} coverage does not contain every dataset date.")


def _validate_evaluation(evaluation: Any, dataset_sha256: str) -> None:
    if not isinstance(evaluation, dict) or evaluation.get("schemaVersion") != 1:
        raise DatasetValidationError("Unsupported baseline evaluation schema.")
    if evaluation.get("datasetSha256") != dataset_sha256 or not isinstance(evaluation.get("rows"), list):
        raise DatasetValidationError("Baseline evaluation does not match the dataset.")


def _labels_for_date(value: str, episodes: list[dict[str, Any]]) -> set[str]:
    return {code for episode in episodes if _contains(episode, value) for code in episode["labels"]}


def _contains(episode: dict[str, Any], value: str) -> bool:
    month = date.fromisoformat(value).replace(day=1)
    return episode["first"] <= month <= episode["last"]


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


def _month(value: Any, location: str) -> date:
    parsed = _iso_date(value, location)
    if parsed.day != 1:
        raise DatasetValidationError(f"{location} must be the first day of a month.")
    return parsed


def _next_month(value: date) -> date:
    return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 8) if denominator else None
