from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .dimensions import dimension_scores
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics, calibration_table, metric_delta, probability_metrics
from .stress import validate_stress_truth


FEATURE_ORDER = [
    "GROWTH_MOM", "INFL_PRESS", "RISK_APPETITE", "MONETARY_COND", "CREDIT_STRESS"
]
PRIMARY_REGIMES = [
    "Goldilocks", "Reflation", "LateCycleOverheating", "Stagflation", "DeflationBust"
]


def dimensional_prediction(
    row: dict[str, Any],
    previous_row: dict[str, Any] | None,
    candidate: dict[str, Any],
    geometry: dict[str, Any],
) -> dict[str, Any]:
    current_dimensions = dimension_scores(row)
    previous_dimensions = dimension_scores(previous_row) if previous_row is not None else current_dimensions
    financial_impulse = max(
        0.0, current_dimensions["financialStress"] - previous_dimensions["financialStress"]
    )
    growth_impulse = max(
        0.0,
        current_dimensions["growthDeterioration"]
        - previous_dimensions["growthDeterioration"],
    )
    weights = _impulse_weights(candidate)
    features = _features(row)
    adjusted = {
        **features,
        "RISK_APPETITE": _clamp01(features["RISK_APPETITE"] - weights["risk"] * financial_impulse),
        "CREDIT_STRESS": _clamp01(features["CREDIT_STRESS"] - weights["credit"] * financial_impulse),
        "GROWTH_MOM": _clamp01(features["GROWTH_MOM"] - weights["growth"] * growth_impulse),
    }
    adjusted_dimensions = dimension_scores({
        "featureScores": [
            {"featureCode": code, "normalizedScore": adjusted[code]} for code in FEATURE_ORDER
        ]
    })
    divergent = (
        adjusted["GROWTH_MOM"] > 0.65
        and adjusted["INFL_PRESS"] > 0.65
        and (
            adjusted["RISK_APPETITE"] < float(geometry["divergentRiskThreshold"])
            or adjusted["CREDIT_STRESS"] < 0.40
        )
    )
    fits = {
        regime: max(
            0.05,
            1.0
            - sum(abs(adjusted[code] - float(target)) for code, target in zip(FEATURE_ORDER, geometry["archetypes"][regime]))
            / len(FEATURE_ORDER),
        )
        for regime in PRIMARY_REGIMES
    }
    neutral = max(
        0.0, 1.0 - sum(abs(adjusted[code] - 0.5) for code in FEATURE_ORDER) / len(FEATURE_ORDER) / 0.35
    )
    uncertain_fit = min(1.0, 0.15 + neutral * 0.25 + (0.40 if divergent else 0.0))
    raw = {regime: fit ** int(geometry["scorePower"]) for regime, fit in fits.items()}
    raw["UncertainTransition"] = uncertain_fit ** int(geometry["scorePower"])
    total = sum(raw.values())
    probabilities = {regime: raw[regime] / total for regime in raw}
    ranked = sorted(PRIMARY_REGIMES, key=lambda regime: (-fits[regime], regime))
    top, second = fits[ranked[0]], fits[ranked[1]]
    relative_separation = (top - second) / (1.0 - second) if second < 1.0 else 0.0
    confidence = _clamp01(
        float(geometry["confidenceFitShare"]) * top
        + float(geometry["confidenceSeparationShare"]) * relative_separation
        - (0.2 if divergent else 0.0)
    )
    primary = ranked[0]
    operational = (
        "UncertainTransition"
        if divergent or confidence < float(geometry["confirmationThreshold"])
        else primary
    )
    return {
        "asOfDate": row["asOfDate"],
        "modelId": candidate["modelId"],
        "primaryRegime": primary,
        "operationalRegime": operational,
        "confidence": round(confidence, 8),
        "recessionProbability": round(probabilities["DeflationBust"], 8),
        "financialStressImpulse": round(financial_impulse, 8),
        "growthDeteriorationImpulse": round(growth_impulse, 8),
        "dimensions": adjusted_dimensions,
        "adjustedFeatureScores": [
            {"featureCode": code, "normalizedScore": round(adjusted[code], 8)}
            for code in FEATURE_ORDER
        ],
    }


def archetype_scenarios(candidate: dict[str, Any], geometry: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = []
    for regime in PRIMARY_REGIMES:
        row = {
            "asOfDate": "2000-01-31",
            "featureScores": [
                {"featureCode": code, "normalizedScore": value}
                for code, value in zip(FEATURE_ORDER, geometry["archetypes"][regime])
            ],
        }
        prediction = dimensional_prediction(row, row, candidate, geometry)
        scenarios.append({
            "scenario": regime,
            "expectedPrimaryRegime": regime,
            "actualPrimaryRegime": prediction["primaryRegime"],
            "passed": prediction["primaryRegime"] == regime,
        })
    return scenarios


def write_dimensional_baseline_gate(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    recession_truth_path: str | Path,
    stress_truth_path: str | Path,
    candidate_path: str | Path,
    geometry_path: str | Path,
    gate_path: str | Path,
    manifest_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    inputs = [
        _read_json(evaluation_path, "baseline evaluation"),
        _read_json(plan_path, "walk-forward plan"),
        _read_json(recession_truth_path, "recession truth"),
        _read_json(stress_truth_path, "stress truth"),
        _read_json(candidate_path, "candidate config"),
        _read_json(geometry_path, "baseline geometry"),
        _read_json(gate_path, "E11 gate"),
        _read_json(manifest_path, "E11 preregistration manifest"),
    ]
    (evaluation_file, evaluation_bytes, evaluation), (plan_file, plan_bytes, plan), \
        (recession_file, recession_bytes, recession), (stress_file, stress_bytes, stress), \
        (candidate_file, candidate_bytes, candidate), (geometry_file, geometry_bytes, geometry), \
        (gate_file, gate_bytes, gate), (manifest_file, manifest_bytes, manifest) = inputs
    periods = validate_recession_truth(recession)
    taxonomy, episodes = validate_stress_truth(stress)
    _validate_contracts(dataset.sha256, evaluation, evaluation_bytes, plan_bytes, recession_bytes, stress_bytes, candidate_bytes, candidate, geometry_bytes, geometry, gate_bytes, gate, manifest)
    rows = sorted(evaluation["rows"], key=lambda item: item["asOfDate"])
    if {item["asOfDate"] for item in rows} != {item["asOfDate"] for item in dataset.rows}:
        raise DatasetValidationError("E11.2 evaluation dates do not match dataset dates.")
    by_date = {item["asOfDate"]: item for item in rows}
    predictions = {
        row["asOfDate"]: dimensional_prediction(row, rows[index - 1] if index else None, candidate, geometry)
        for index, row in enumerate(rows)
    }
    folds = plan.get("folds")
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds):
        raise DatasetValidationError("E11.2 walk-forward plan is invalid.")
    inner_years = int(plan.get("config", {}).get("testYears", 0))
    if inner_years <= 0:
        raise DatasetValidationError("E11.2 derives inner validation duration from plan.testYears.")
    fold_reports = []
    unique: dict[str, dict[str, Any]] = {}
    for fold in sorted(folds, key=lambda item: item["number"]):
        train_from, train_to = date.fromisoformat(fold["train_from"]), date.fromisoformat(fold["train_to"])
        test_from = date.fromisoformat(fold["test_from"])
        if train_to >= test_from:
            raise DatasetValidationError("E11.2 outer train/test windows overlap.")
        inner_from = _add_years(train_to, -inner_years)
        selected = [key for key in sorted(by_date) if inner_from < date.fromisoformat(key) <= train_to]
        if not selected:
            raise DatasetValidationError("E11.2 inner validation fold is empty.")
        if any(date.fromisoformat(key) >= test_from for key in selected):
            raise DatasetValidationError("E11.2 attempted to use an outer test row.")
        for key in selected:
            unique.setdefault(key, predictions[key])
        fold_reports.append({
            "number": fold["number"],
            "outerTrainFrom": train_from.isoformat(),
            "outerTrainTo": train_to.isoformat(),
            "innerValidationFrom": selected[0],
            "innerValidationTo": selected[-1],
            "innerValidationRowCount": len(selected),
            "outerTestFrom": fold["test_from"],
            "outerTestTo": fold["test_to"],
            "outerTestRowCountUsed": 0,
            "eligible": True,
        })
    keys = sorted(unique)
    actual = {key: is_recession(key, periods) for key in keys}
    candidate_binary = {key: unique[key]["operationalRegime"] == "DeflationBust" for key in keys}
    baseline_binary = {key: by_date[key]["operationalRegime"] == "DeflationBust" for key in keys}
    candidate_probabilities = {key: float(unique[key]["recessionProbability"]) for key in keys}
    baseline_probabilities = {key: _baseline_probability(by_date[key]) for key in keys}
    candidate_metrics, baseline_metrics = binary_metrics(actual, candidate_binary), binary_metrics(actual, baseline_binary)
    candidate_probability_metrics = probability_metrics(actual, candidate_probabilities)
    baseline_probability_metrics = probability_metrics(actual, baseline_probabilities)
    calibration = calibration_table(actual, candidate_probabilities, 5)
    thresholds = gate["innerValidation"]
    delta = metric_delta(candidate_metrics, baseline_metrics)
    probability_delta = {
        "brierScore": round(candidate_probability_metrics["brierScore"] - baseline_probability_metrics["brierScore"], 8),
        "averagePrecision": _optional_delta(candidate_probability_metrics["averagePrecision"], baseline_probability_metrics["averagePrecision"]),
    }
    fp_run_delta = _false_positive_run(actual, candidate_binary) - _false_positive_run(actual, baseline_binary)
    protected = _protected_stress_hit_rate(keys, unique, taxonomy, episodes)
    checks = {
        "minimumEligibleFolds": len(fold_reports) >= int(thresholds["minimumEligibleFolds"]),
        "recallDelta": _minimum_optional(delta["recall"], thresholds["minimumRecallDeltaVsBaseline"]),
        "f1Delta": _minimum_optional(delta["f1"], thresholds["minimumF1DeltaVsBaseline"]),
        "brierDelta": probability_delta["brierScore"] <= float(thresholds["maximumBrierDeltaVsBaseline"]),
        "averagePrecisionDelta": _minimum_optional(probability_delta["averagePrecision"], thresholds["minimumAveragePrecisionDeltaVsBaseline"]),
        "expectedCalibrationError": calibration["expectedCalibrationError"] <= float(thresholds["maximumExpectedCalibrationError"]),
        "falsePositiveRunDelta": fp_run_delta <= int(thresholds["maximumFalsePositiveRunDeltaMonths"]),
        "protectedStressDimensionHitRate": protected["hitRate"] is not None and protected["hitRate"] >= float(thresholds["minimumProtectedStressDimensionHitRate"]),
        "archetypeScenarios": all(item["passed"] for item in archetype_scenarios(candidate, geometry)),
    }
    passed = all(checks.values())
    report = {
        "reportVersion": 1,
        "reportType": "E11DimensionalBaselineInnerGate",
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
            "geometryFileName": geometry_file.name,
            "geometrySha256": hashlib.sha256(geometry_bytes).hexdigest(),
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
            "labelUse": "attached only after all candidate predictions are frozen",
        },
        "coverage": {"foldCount": len(fold_reports), "uniqueInnerValidationRowCount": len(keys), "from": keys[0], "to": keys[-1]},
        "candidateMetrics": candidate_metrics,
        "baselineMetrics": baseline_metrics,
        "deltaVsBaseline": delta,
        "candidateProbabilityMetrics": candidate_probability_metrics,
        "baselineProbabilityMetrics": baseline_probability_metrics,
        "probabilityDeltaVsBaseline": probability_delta,
        "calibration": calibration,
        "falsePositiveRunDeltaMonths": fp_run_delta,
        "protectedStressDiagnostics": protected,
        "archetypeScenarios": archetype_scenarios(candidate, geometry),
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
            "module": "regime_eval.dimensional_baseline",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _validate_contracts(dataset_sha: str, evaluation: Any, evaluation_bytes: bytes, plan_bytes: bytes, recession_bytes: bytes, stress_bytes: bytes, candidate_bytes: bytes, candidate: Any, geometry_bytes: bytes, geometry: Any, gate_bytes: bytes, gate: Any, manifest: Any) -> None:
    if not isinstance(evaluation, dict) or evaluation.get("schemaVersion") != 1 or evaluation.get("datasetSha256") != dataset_sha or not isinstance(evaluation.get("rows"), list):
        raise DatasetValidationError("E11.2 baseline evaluation is invalid.")
    if not isinstance(candidate, dict) or candidate.get("modelId") != "baseline-v1-5-dimensional" or candidate.get("benchmarkScope") != "inner-validation-only":
        raise DatasetValidationError("E11.2 candidate config is invalid.")
    expected = candidate.get("expectedInputs", {})
    actual = {
        "datasetSha256": dataset_sha,
        "baselineEvaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
        "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
        "recessionGroundTruthSha256": hashlib.sha256(recession_bytes).hexdigest(),
        "stressGroundTruthSha256": hashlib.sha256(stress_bytes).hexdigest(),
    }
    if expected != actual or candidate.get("baseModelConfigSha256") != hashlib.sha256(geometry_bytes).hexdigest():
        raise DatasetValidationError("E11.2 frozen input hashes do not match.")
    if not isinstance(geometry, dict) or geometry.get("modelVersion") != evaluation.get("modelVersion") or set(geometry.get("archetypes", {})) != set(PRIMARY_REGIMES):
        raise DatasetValidationError("E11.2 v1.4 geometry is invalid.")
    if not isinstance(gate, dict) or candidate["modelId"] not in gate.get("registeredModelIds", []) or gate.get("targetLifecycle") != "shadow-candidate":
        raise DatasetValidationError("E11.2 gate does not register the candidate.")
    if (
        not isinstance(manifest, dict)
        or manifest.get("artifactType") != "ExperimentPreregistrationManifest"
        or manifest.get("status") != "preregistered"
        or manifest.get("gate", {}).get("sha256") != hashlib.sha256(gate_bytes).hexdigest()
        or manifest.get("expectedInputs") != expected
    ):
        raise DatasetValidationError("E11.2 preregistration manifest does not bind the supplied gate and inputs.")
    registered = {item.get("modelId"): item for item in manifest.get("candidates", []) if isinstance(item, dict)}
    if registered.get(candidate["modelId"], {}).get("configSha256") != hashlib.sha256(candidate_bytes).hexdigest():
        raise DatasetValidationError("E11.2 preregistration manifest does not bind the candidate config.")


def _features(row: dict[str, Any]) -> dict[str, float]:
    dimension_scores(row)
    return {item["featureCode"]: float(item["normalizedScore"]) for item in row["featureScores"]}


def _impulse_weights(candidate: dict[str, Any]) -> dict[str, float]:
    policy = candidate.get("causalImpulsePolicy", {})
    expected = {
        "riskAppetiteAdjustment": ("RISK_APPETITE", 0.50),
        "creditStressAdjustment": ("CREDIT_STRESS", 0.50),
        "growthAdjustment": ("GROWTH_MOM", 0.35),
    }
    for key, (feature, weight) in expected.items():
        if str(policy.get(key)) != f"clamp01({feature} - {weight:.2f} * {'growthDeteriorationImpulse' if key == 'growthAdjustment' else 'financialStressImpulse'})":
            raise DatasetValidationError("E11.2 impulse policy differs from the frozen formula.")
    return {"risk": 0.50, "credit": 0.50, "growth": 0.35}


def _baseline_probability(row: dict[str, Any]) -> float:
    for item in row.get("probabilities", []):
        if item.get("regime") == "DeflationBust":
            return float(item["probability"])
    return 1.0 if row.get("operationalRegime") == "DeflationBust" else 0.0


def _protected_stress_hit_rate(keys: list[str], predictions: dict[str, dict[str, Any]], taxonomy: dict[str, dict[str, Any]], episodes: list[dict[str, Any]]) -> dict[str, Any]:
    observations = []
    for episode in episodes:
        if episode.get("validationRole") != "protected-v2":
            continue
        for key in keys:
            month = date.fromisoformat(key).replace(day=1)
            if episode["first"] <= month <= episode["last"]:
                for label in episode["labels"]:
                    for dimension, bounds in taxonomy[label]["expectedDimensions"].items():
                        value = predictions[key]["dimensions"][dimension]
                        hit = value >= float(bounds["minimum"]) if "minimum" in bounds else value <= float(bounds["maximum"])
                        observations.append({"asOfDate": key, "episodeId": episode["id"], "label": label, "dimension": dimension, "value": value, "hit": hit})
    hits = sum(item["hit"] for item in observations)
    return {"observationCount": len(observations), "hitCount": hits, "hitRate": round(hits / len(observations), 8) if observations else None, "observations": observations}


def _false_positive_run(actual: dict[str, bool], predicted: dict[str, bool]) -> int:
    longest = current = 0
    for key in sorted(actual):
        current = current + 1 if predicted[key] and not actual[key] else 0
        longest = max(longest, current)
    return longest


def _optional_delta(left: float | None, right: float | None) -> float | None:
    return round(left - right, 8) if left is not None and right is not None else None


def _minimum_optional(value: float | None, minimum: Any) -> bool:
    return value is not None and value >= float(minimum)


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc
