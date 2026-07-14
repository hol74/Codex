from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import fmean, median
from typing import Any

from .baseline import _read_json, _validate_evaluation
from .dataset import DatasetValidationError, load_dataset


def write_baseline_audit(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    config_file, config_bytes, config = _read_json(config_path, "baseline audit config")
    _validate_evaluation(evaluation, dataset.sha256)
    _validate_config(config)

    rows = evaluation["rows"]
    unique_oos_dates = _unique_oos_dates(plan, [row["asOfDate"] for row in rows])
    oos_rows = [row for row in rows if row["asOfDate"] in unique_oos_dates]
    if not oos_rows:
        raise DatasetValidationError("Baseline audit has no out-of-sample rows.")

    full = _summarize(rows, config)
    oos = _summarize(oos_rows, config)
    violations = _gate_violations(oos, config)
    report = {
        "reportVersion": 1,
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "evaluationFileName": evaluation_file.name,
            "evaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "configFileName": config_file.name,
            "configSha256": hashlib.sha256(config_bytes).hexdigest(),
        },
        "methodology": {
            "purpose": "diagnostic gate before baseline redesign; not a promotion score",
            "aggregation": "out-of-sample uses each test date once",
            "boundaryDefinition": "scores at or below floor, or at or above ceiling",
        },
        "gate": {
            "passed": not violations,
            "violationCount": len(violations),
            "violations": violations,
        },
        "fullHistory": full,
        "uniqueOutOfSample": oos,
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination.resolve()


def _summarize(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    floor = float(config["featureBoundaryFloor"])
    ceiling = float(config["featureBoundaryCeiling"])
    features: dict[str, list[float]] = {}
    for row in rows:
        for feature in row.get("featureScores", []):
            features.setdefault(str(feature["featureCode"]), []).append(float(feature["normalizedScore"]))

    primary = Counter(str(row["primaryRegime"]) for row in rows)
    operational = Counter(str(row["operationalRegime"]) for row in rows)
    top_pairs = Counter(
        f"{probabilities[0]['regime']} > {probabilities[1]['regime']}"
        for row in rows
        if len(probabilities := row.get("probabilities", [])) >= 2
    )
    return {
        "rowCount": len(rows),
        "featureDiagnostics": [
            _feature_summary(code, values, floor, ceiling) for code, values in sorted(features.items())
        ],
        "primaryRegimeDistribution": _distribution(primary, len(rows)),
        "operationalRegimeDistribution": _distribution(operational, len(rows)),
        "primaryRegimeCount": len(primary),
        "dominantPrimaryRegime": max(primary, key=primary.get) if primary else None,
        "dominantPrimaryRegimeRate": _round(max(primary.values()) / len(rows)) if rows else None,
        "uncertainTransitionRate": _round(operational.get("UncertainTransition", 0) / len(rows)) if rows else None,
        "topTwoRegimePairs": [
            {"pair": pair, "count": count, "rate": _round(count / len(rows))}
            for pair, count in top_pairs.most_common()
        ],
    }


def _feature_summary(code: str, values: list[float], floor: float, ceiling: float) -> dict[str, Any]:
    ordered = sorted(values)
    boundary_count = sum(value <= floor or value >= ceiling for value in values)
    return {
        "featureCode": code,
        "count": len(values),
        "minimum": _round(ordered[0]),
        "p10": _round(_percentile(ordered, 0.10)),
        "median": _round(median(ordered)),
        "p90": _round(_percentile(ordered, 0.90)),
        "maximum": _round(ordered[-1]),
        "mean": _round(fmean(ordered)),
        "floorRate": _round(sum(value <= floor for value in values) / len(values)),
        "ceilingRate": _round(sum(value >= ceiling for value in values) / len(values)),
        "boundaryRate": _round(boundary_count / len(values)),
    }


def _gate_violations(summary: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *_feature_integrity_violations(summary, config),
        *_coverage_violations(summary, config),
        *_operational_violations(summary, config),
    ]


def _feature_integrity_violations(
    summary: dict[str, Any], config: dict[str, Any]
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    max_boundary = float(config["maxFeatureBoundaryRate"])
    present = {feature["featureCode"] for feature in summary["featureDiagnostics"]}
    for feature_code in config["expectedFeatureCodes"]:
        if feature_code not in present:
            violations.append({
                "code": "MISSING_FEATURE_DIAGNOSTIC",
                "subject": feature_code,
            })
    for feature in summary["featureDiagnostics"]:
        if feature["boundaryRate"] > max_boundary:
            violations.append({
                "code": "FEATURE_BOUNDARY_SATURATION",
                "subject": feature["featureCode"],
                "actual": feature["boundaryRate"],
                "limit": max_boundary,
            })
    return violations


def _coverage_violations(summary: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if summary["primaryRegimeCount"] < int(config["minPrimaryRegimeCount"]):
        violations.append({
            "code": "INSUFFICIENT_PRIMARY_REGIME_DIVERSITY",
            "actual": summary["primaryRegimeCount"],
            "limit": int(config["minPrimaryRegimeCount"]),
        })
    if summary["dominantPrimaryRegimeRate"] > float(config["maxDominantPrimaryRegimeRate"]):
        violations.append({
            "code": "DOMINANT_PRIMARY_REGIME",
            "subject": summary["dominantPrimaryRegime"],
            "actual": summary["dominantPrimaryRegimeRate"],
            "limit": float(config["maxDominantPrimaryRegimeRate"]),
        })
    return violations


def _operational_violations(summary: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if summary["uncertainTransitionRate"] > float(config["maxUncertainTransitionRate"]):
        violations.append({
            "code": "EXCESSIVE_UNCERTAIN_TRANSITION",
            "actual": summary["uncertainTransitionRate"],
            "limit": float(config["maxUncertainTransitionRate"]),
        })
    return violations


def _unique_oos_dates(plan: dict[str, Any], evaluation_dates: list[str]) -> set[str]:
    folds = plan.get("folds")
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")
    dates: set[str] = set()
    for fold in folds:
        start = str(fold["test_from"])
        end = str(fold["test_to"])
        dates.update(value for value in evaluation_dates if start <= value <= end)
    return dates


def _validate_config(config: Any) -> None:
    required = {
        "featureBoundaryFloor", "featureBoundaryCeiling", "maxFeatureBoundaryRate",
        "expectedFeatureCodes", "minPrimaryRegimeCount", "maxDominantPrimaryRegimeRate",
        "maxUncertainTransitionRate",
    }
    if not isinstance(config, dict) or config.get("schemaVersion") != 1 or not required <= config.keys():
        raise DatasetValidationError("Unsupported or incomplete baseline audit config.")
    if not 0 <= float(config["featureBoundaryFloor"]) < float(config["featureBoundaryCeiling"]) <= 1:
        raise DatasetValidationError("Baseline audit feature boundaries are invalid.")
    if not isinstance(config["expectedFeatureCodes"], list) or not config["expectedFeatureCodes"]:
        raise DatasetValidationError("Baseline audit expectedFeatureCodes must be a non-empty array.")


def _distribution(counts: Counter[str], total: int) -> list[dict[str, Any]]:
    return [
        {"regime": key, "count": counts[key], "rate": _round(counts[key] / total)}
        for key in sorted(counts)
    ]


def _percentile(values: list[float], fraction: float) -> float:
    return values[round((len(values) - 1) * fraction)]


def _round(value: float) -> float:
    return round(value, 8)
