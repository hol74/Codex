from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .baseline import _read_json, _validate_evaluation
from .baseline_audit import (
    _coverage_violations,
    _feature_integrity_violations,
    _gate_violations,
    _operational_violations,
    _summarize,
    _validate_config,
)
from .dataset import DatasetValidationError, load_dataset


def write_baseline_train_gate(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    config_file, config_bytes, config = _read_json(config_path, "preregistered baseline config")
    _validate_evaluation(evaluation, dataset.sha256)
    evaluation_sha256 = hashlib.sha256(evaluation_bytes).hexdigest()
    _validate_train_config(config, dataset.sha256, evaluation_sha256, evaluation.get("modelVersion"))

    folds = plan.get("folds")
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("Walk-forward plan foldCount is inconsistent.")
    rows = sorted(evaluation["rows"], key=lambda row: row["asOfDate"])
    if {row["asOfDate"] for row in rows} != {row["asOfDate"] for row in dataset.rows}:
        raise DatasetValidationError("Baseline evaluation dates do not exactly match dataset dates.")
    inner_years = int(config["innerValidationYears"])
    gate_version = int(config.get("gateVersion", 1))
    fold_reports: list[dict[str, Any]] = []
    unique_validation_rows: dict[str, dict[str, Any]] = {}
    for fold in sorted(folds, key=lambda item: item.get("number", 0)):
        train_from = _iso_date(fold.get("train_from"), "fold.train_from")
        train_to = _iso_date(fold.get("train_to"), "fold.train_to")
        test_from = _iso_date(fold.get("test_from"), "fold.test_from")
        test_to = _iso_date(fold.get("test_to"), "fold.test_to")
        if train_from > train_to or train_to >= test_from or test_from > test_to:
            raise DatasetValidationError(f"Fold {fold.get('number')} has invalid train/test boundaries.")
        inner_from = _add_years(train_to, -inner_years) + timedelta(days=1)
        fit_rows = [row for row in rows if train_from <= date.fromisoformat(row["asOfDate"]) < inner_from]
        validation_rows = [row for row in rows if inner_from <= date.fromisoformat(row["asOfDate"]) <= train_to]
        if not fit_rows or not validation_rows:
            raise DatasetValidationError(f"Fold {fold.get('number')} has an empty inner fit or validation slice.")
        summary = _summarize(validation_rows, config)
        for row in validation_rows:
            unique_validation_rows[row["asOfDate"]] = row
        violations = (
            _operational_violations(summary, config)
            if gate_version == 2
            else _gate_violations(summary, config)
        )
        fold_report = {
            "number": fold.get("number"),
            "outerTrainFrom": train_from.isoformat(),
            "outerTrainTo": train_to.isoformat(),
            "innerFitFrom": fit_rows[0]["asOfDate"],
            "innerFitTo": fit_rows[-1]["asOfDate"],
            "innerFitRowCount": len(fit_rows),
            "innerValidationFrom": validation_rows[0]["asOfDate"],
            "innerValidationTo": validation_rows[-1]["asOfDate"],
            "outerTestFrom": test_from.isoformat(),
            "outerTestTo": test_to.isoformat(),
            "outerTestRowCountUsed": 0,
            "summary": summary,
        }
        if gate_version == 2:
            fold_report["operationalGate"] = {"passed": not violations, "violations": violations}
        else:
            fold_report["passed"] = not violations
            fold_report["violations"] = violations
        fold_reports.append(fold_report)

    if gate_version == 2:
        aggregate_rows = [unique_validation_rows[key] for key in sorted(unique_validation_rows)]
        aggregate_summary = {
            "from": aggregate_rows[0]["asOfDate"],
            "to": aggregate_rows[-1]["asOfDate"],
            **_summarize(aggregate_rows, config),
        }
        feature_violations = _feature_integrity_violations(aggregate_summary, config)
        coverage_violations = _coverage_violations(aggregate_summary, config)
        operational_count = sum(fold["operationalGate"]["passed"] for fold in fold_reports)
        minimum = int(config["minimumOperationalFoldCount"])
        if minimum > len(fold_reports):
            raise DatasetValidationError("minimumOperationalFoldCount exceeds the plan fold count.")
        feature_passed = not feature_violations
        coverage_passed = not coverage_violations
        operational_passed = operational_count >= minimum
        gate = {
            "eligibleForOuterOos": feature_passed and coverage_passed and operational_passed,
            "featureIntegrity": {"passed": feature_passed, "violations": feature_violations},
            "regimeCoverage": {"passed": coverage_passed, "violations": coverage_violations},
            "operationalRobustness": {
                "passed": operational_passed,
                "passingFoldCount": operational_count,
                "foldCount": len(fold_reports),
                "minimumPassingFoldCount": minimum,
            },
        }
    else:
        aggregate_summary = None
        eligible_count = sum(fold["passed"] for fold in fold_reports)
        minimum = int(config["minimumEligibleFoldCount"])
        gate = {
            "eligibleForOuterOos": eligible_count >= minimum,
            "eligibleFoldCount": eligible_count,
            "foldCount": len(fold_reports),
            "minimumEligibleFoldCount": minimum,
        }
    report = {
        "reportVersion": gate_version,
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "evaluationFileName": evaluation_file.name,
            "evaluationSha256": evaluation_sha256,
            "walkForwardPlanFileName": plan_file.name,
            "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
            "configFileName": config_file.name,
            "configSha256": hashlib.sha256(config_bytes).hexdigest(),
        },
        "methodology": {
            "purpose": "train-only preflight for a frozen candidate before outer OOS reporting",
            "selection": "no parameter fitting or search is performed",
            "innerValidation": f"last {inner_years} years of each outer training window",
            "outerTestUse": "each fold excludes its own outer test; because rolling folds overlap, a later train may contain dates that were test dates in an earlier fold",
            "gateSeparation": (
                "feature integrity and regime coverage on unique aggregate validation dates; operational uncertainty per fold"
                if gate_version == 2
                else "all diagnostics applied independently to every fold"
            ),
        },
        "gate": gate,
        "folds": fold_reports,
    }
    if aggregate_summary is not None:
        report["aggregateUniqueInnerValidation"] = aggregate_summary
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination.resolve()


def _validate_train_config(
    config: Any, dataset_sha256: str, evaluation_sha256: str, model_version: Any
) -> None:
    _validate_config(config)
    gate_version = int(config.get("gateVersion", 1))
    required = {"modelVersion", "datasetSha256", "innerValidationYears"}
    required.add("minimumOperationalFoldCount" if gate_version == 2 else "minimumEligibleFoldCount")
    if gate_version == 2:
        required.update({
            "evaluationSha256", "aggregateDatePolicy", "featureIntegrityScope",
            "coverageScope", "operationalScope",
        })
    if not required <= config.keys():
        raise DatasetValidationError("Preregistered baseline config is incomplete.")
    if config["datasetSha256"] != dataset_sha256:
        raise DatasetValidationError("Preregistered config dataset SHA-256 does not match the dataset.")
    if config["modelVersion"] != model_version:
        raise DatasetValidationError("Preregistered config modelVersion does not match the evaluation.")
    if gate_version not in (1, 2):
        raise DatasetValidationError("Unsupported train gate version.")
    if gate_version == 2 and config.get("evaluationSha256") != evaluation_sha256:
        raise DatasetValidationError("Preregistered config evaluation SHA-256 does not match the evaluation.")
    if gate_version == 2 and (
        config.get("featureIntegrityScope") != "aggregateUniqueInnerValidation"
        or config.get("coverageScope") != "aggregateUniqueInnerValidation"
        or config.get("operationalScope") != "perFold"
    ):
        raise DatasetValidationError("Train gate v2 scopes are invalid.")
    minimum_key = "minimumOperationalFoldCount" if gate_version == 2 else "minimumEligibleFoldCount"
    if int(config["innerValidationYears"]) <= 0 or int(config[minimum_key]) <= 0:
        raise DatasetValidationError("Train gate year and fold requirements must be positive.")


def _iso_date(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise DatasetValidationError(f"{field} must be an ISO date.") from exc


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)
