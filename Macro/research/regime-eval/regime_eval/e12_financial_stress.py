from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .dimensional_baseline import _add_years
from .metrics import binary_metrics, calibration_table, probability_metrics
from .stress import validate_stress_truth


MODEL_ID = "event-aware-financial-stress-v1"
GATE_ID = "e12-financial-stress-gate-v1"
BASE_CODES = (
    "VIX_MONTHLY_MAX",
    "SPY_MONTHLY_MAX_DRAWDOWN",
    "HYG_MONTHLY_MAX_DRAWDOWN",
    "HY_OAS",
)
FUNDING_CODE = "SOFR_EFFR_MONTHLY_MAX"


def financial_stress_prediction(row: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    values = {
        str(item.get("seriesCode")): float(item["value"])
        for item in row.get("macroObservations", [])
        if item.get("seriesCode") and item.get("value") is not None
    }
    missing = [code for code in BASE_CODES if code not in values]
    if missing:
        raise DatasetValidationError(f"E12 financial-stress row lacks base inputs: {missing}.")
    severity = {
        "vix": _clip01((values["VIX_MONTHLY_MAX"] - 18.0) / 42.0),
        "spyDrawdown": _clip01(values["SPY_MONTHLY_MAX_DRAWDOWN"] / 25.0),
        "hygDrawdown": _clip01(values["HYG_MONTHLY_MAX_DRAWDOWN"] / 15.0),
        "credit": _clip01((values["HY_OAS"] - 2.0) / 4.0),
    }
    weights = config["baseScore"]["weightedMean"]
    weighted = sum(severity[key] * float(weights[key]) for key in severity)
    base = 0.60 * max(severity.values()) + 0.40 * weighted
    funding_available = FUNDING_CODE in values
    funding = _clip01(values[FUNDING_CODE] / 200.0) if funding_available else None
    final = max(base, 0.70 * funding + 0.30 * base) if funding is not None else base
    probability = _sigmoid(7.0 * (final - 0.45))
    return {
        "asOfDate": row["asOfDate"],
        "modelId": MODEL_ID,
        "financialStressProbability": round(probability, 8),
        "predictedFinancialStress": probability >= float(config["decisionThreshold"]),
        "baseScore": round(base, 8),
        "finalScore": round(final, 8),
        "fundingAvailable": funding_available,
        "severities": {**{key: round(value, 8) for key, value in severity.items()}, "funding": round(funding, 8) if funding is not None else None},
    }


def write_e12_financial_preregistration(
    candidate_path: str | Path,
    gate_path: str | Path,
    foundation_lock_path: str | Path,
    output_path: str | Path,
) -> Path:
    candidate_file, candidate_bytes, candidate = _read_json(candidate_path, "E12 candidate")
    gate_file, gate_bytes, gate = _read_json(gate_path, "E12 financial gate")
    lock_file, lock_bytes, lock = _read_json(foundation_lock_path, "E12 foundation lock")
    _validate_static_contract(candidate, gate, lock, lock_bytes)
    seed = {
        "candidateSha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "gateSha256": hashlib.sha256(gate_bytes).hexdigest(),
        "foundationLockSha256": hashlib.sha256(lock_bytes).hexdigest(),
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E12FinancialStressPreregistration",
        "registrationId": hashlib.sha256(_canonical_bytes(seed)).hexdigest()[:24],
        "status": "preregistered",
        "frozenAt": candidate["frozenAt"],
        "modelId": MODEL_ID,
        "taskRole": "financial-stress-signal",
        "candidate": _artifact(candidate_file, candidate_bytes),
        "gate": {**_artifact(gate_file, gate_bytes), "contractId": GATE_ID},
        "foundationLock": _artifact(lock_file, lock_bytes),
        "expectedInputs": candidate["expectedInputs"],
        "maximumLifecycle": "shadow-candidate",
        "outerOosPolicy": candidate["outerOosPolicy"],
        "implementation": {"module": "regime_eval.e12_financial_stress", "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    return _write_new_json(output_path, payload, "Immutable E12 financial preregistration exists")


def write_e12_financial_stress_gate(
    dataset_path: str | Path,
    plan_path: str | Path,
    stress_truth_path: str | Path,
    candidate_path: str | Path,
    gate_path: str | Path,
    foundation_lock_path: str | Path,
    foundation_freeze_path: str | Path,
    preregistration_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    inputs = [
        _read_json(plan_path, "walk-forward plan"),
        _read_json(stress_truth_path, "stress truth"),
        _read_json(candidate_path, "E12 candidate"),
        _read_json(gate_path, "E12 financial gate"),
        _read_json(foundation_lock_path, "E12 foundation lock"),
        _read_json(foundation_freeze_path, "E12 foundation freeze"),
        _read_json(preregistration_path, "E12 financial preregistration"),
    ]
    (plan_file, plan_bytes, plan), (stress_file, stress_bytes, stress), \
        (candidate_file, candidate_bytes, candidate), (gate_file, gate_bytes, gate), \
        (lock_file, lock_bytes, lock), (freeze_file, freeze_bytes, freeze), \
        (manifest_file, manifest_bytes, manifest) = inputs
    taxonomy, episodes = validate_stress_truth(stress)
    _validate_runtime_contract(
        dataset.sha256, plan_bytes, stress_bytes, candidate_bytes, candidate,
        gate_bytes, gate, lock_bytes, lock, freeze_bytes, freeze, manifest,
    )
    rows = {row["asOfDate"]: row for row in dataset.rows}
    folds = plan.get("folds")
    inner_years = int(plan.get("config", {}).get("testYears", 0))
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds) or inner_years <= 0:
        raise DatasetValidationError("E12.3 walk-forward plan is invalid.")

    unique: dict[str, dict[str, Any]] = {}
    fold_reports = []
    for fold in sorted(folds, key=lambda item: item["number"]):
        train_from = date.fromisoformat(fold["train_from"])
        train_to = date.fromisoformat(fold["train_to"])
        test_from = date.fromisoformat(fold["test_from"])
        if train_to >= test_from:
            raise DatasetValidationError("E12.3 outer train/test windows overlap.")
        inner_from = _add_years(train_to, -inner_years)
        selected = [key for key in sorted(rows) if inner_from < date.fromisoformat(key) <= train_to]
        if not selected or any(date.fromisoformat(key) >= test_from for key in selected):
            raise DatasetValidationError("E12.3 attempted to use an outer test row.")
        predictions = [financial_stress_prediction(rows[key], candidate) for key in selected]
        for prediction in predictions:
            unique.setdefault(prediction["asOfDate"], prediction)
        fold_reports.append({
            "number": fold["number"],
            "outerTrainFrom": fold["train_from"],
            "outerTrainTo": fold["train_to"],
            "innerValidationFrom": selected[0],
            "innerValidationTo": selected[-1],
            "innerValidationRowCount": len(selected),
            "fundingAvailableRowCount": sum(item["fundingAvailable"] for item in predictions),
            "outerTestFrom": fold["test_from"],
            "outerTestTo": fold["test_to"],
            "outerTestRowCountUsed": 0,
            "eligible": True,
        })

    keys = sorted(unique)
    labels = {key: _labels_for_date(key, episodes) for key in keys}
    curated_keys = [key for key in keys if labels[key]]
    if not curated_keys:
        raise DatasetValidationError("E12.3 has no curated inner-validation observations.")
    actual = {key: "financial_stress" in labels[key] for key in curated_keys}
    predicted = {key: bool(unique[key]["predictedFinancialStress"]) for key in curated_keys}
    probabilities = {key: float(unique[key]["financialStressProbability"]) for key in curated_keys}
    metrics = binary_metrics(actual, predicted)
    probabilistic = probability_metrics(actual, probabilities)
    calibration = calibration_table(actual, probabilities, 5)
    protected = _episode_diagnostics(keys, unique, episodes, "protected-v2")
    development = _episode_diagnostics(keys, unique, episodes, "development-v1")
    repo = next((item for item in protected["episodes"] if item["episodeId"] == "repo-stress-2019"), None)
    requirements = gate["requirements"]
    alert_run = _longest_alert_run(keys, unique)
    checks = {
        "minimumEligibleFolds": len(fold_reports) >= int(requirements["minimumEligibleFolds"]),
        "curatedFinancialStressRecall": metrics["recall"] is not None and metrics["recall"] >= float(requirements["minimumCuratedFinancialStressRecall"]),
        "curatedF1": metrics["f1"] is not None and metrics["f1"] >= float(requirements["minimumCuratedF1"]),
        "curatedBrierScore": probabilistic["brierScore"] <= float(requirements["maximumCuratedBrierScore"]),
        "curatedAveragePrecision": probabilistic["averagePrecision"] is not None and probabilistic["averagePrecision"] >= float(requirements["minimumCuratedAveragePrecision"]),
        "expectedCalibrationError": calibration["expectedCalibrationError"] <= float(requirements["maximumExpectedCalibrationError"]),
        "protectedEpisodeHitRate": protected["hitRate"] is not None and protected["hitRate"] >= float(requirements["minimumProtectedEpisodeHitRate"]),
        "repoStressMustHit": repo is not None and bool(repo["hit"]),
        "maximumAlertRunMonths": alert_run <= int(requirements["maximumAlertRunMonths"]),
        "outerTestClosed": all(item["outerTestRowCountUsed"] == 0 for item in fold_reports),
    }
    passed = all(checks.values())
    report = {
        "reportVersion": 1,
        "reportType": "E12FinancialStressInnerGate",
        "modelId": MODEL_ID,
        "taskRole": "financial-stress-signal",
        "inputs": {
            "dataset": {"fileName": dataset.path.name, "sha256": dataset.sha256, "sizeBytes": dataset.size_bytes},
            "walkForwardPlan": _artifact(plan_file, plan_bytes),
            "stressGroundTruth": _artifact(stress_file, stress_bytes),
            "candidateConfig": _artifact(candidate_file, candidate_bytes),
            "gate": _artifact(gate_file, gate_bytes),
            "foundationLock": _artifact(lock_file, lock_bytes),
            "foundationFreeze": _artifact(freeze_file, freeze_bytes),
            "preregistration": _artifact(manifest_file, manifest_bytes),
        },
        "protocol": {
            "scope": "nested-inner-validation-only",
            "uniqueDateAggregation": "earliest fold wins",
            "outerTestRowCountUsed": 0,
            "predictionLabelOrder": "all probabilities frozen before curated labels are attached",
            "classificationUniverse": gate["classificationUniverse"],
            "negativeClassLimitation": "comparison controls are other curated stress labels; unlabeled months are excluded from classification metrics",
        },
        "coverage": {"foldCount": len(fold_reports), "uniqueInnerValidationRowCount": len(keys), "curatedClassificationRowCount": len(curated_keys), "from": keys[0], "to": keys[-1]},
        "curatedMetrics": metrics,
        "curatedProbabilityMetrics": probabilistic,
        "calibration": calibration,
        "developmentEpisodeDiagnostics": development,
        "protectedEpisodeDiagnostics": protected,
        "longestAlertRunMonths": alert_run,
        "gate": {
            "status": "ELIGIBLE_FOR_SHADOW_REVIEW" if passed else "REJECTED_FOR_SHADOW",
            "passed": passed,
            "checks": checks,
            "maximumLifecycle": "shadow-candidate",
            "operationalApprovalAuthorized": False,
        },
        "folds": fold_reports,
        "predictions": [{**unique[key], "curatedLabels": sorted(labels[key])} for key in keys],
        "implementation": {"module": "regime_eval.e12_financial_stress", "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _validate_static_contract(candidate: Any, gate: Any, lock: Any, lock_bytes: bytes) -> None:
    if not isinstance(candidate, dict) or candidate.get("modelId") != MODEL_ID or candidate.get("taskRole") != "financial-stress-signal" or candidate.get("benchmarkScope") != "nested-inner-validation-only":
        raise DatasetValidationError("Unsupported E12 financial candidate.")
    if candidate.get("expectedInputs", {}).get("foundationLockSha256") != hashlib.sha256(lock_bytes).hexdigest():
        raise DatasetValidationError("E12 candidate does not bind the foundation lock.")
    if not isinstance(gate, dict) or gate.get("contractId") != GATE_ID or gate.get("registeredModelId") != MODEL_ID or gate.get("targetLifecycle") != "shadow-candidate":
        raise DatasetValidationError("Unsupported E12 financial gate.")
    if not isinstance(lock, dict) or lock.get("status") != "frozen" or lock.get("contractId") != "e12-task-lifecycle-v1":
        raise DatasetValidationError("Invalid E12 foundation lock.")
    if candidate.get("decisionThreshold") != 0.5 or "no zero fill" not in candidate.get("fundingOverlay", {}).get("whenMissing", ""):
        raise DatasetValidationError("E12 financial formula or missingness policy is not frozen.")


def _validate_runtime_contract(
    dataset_sha: str, plan_bytes: bytes, stress_bytes: bytes, candidate_bytes: bytes,
    candidate: Any, gate_bytes: bytes, gate: Any, lock_bytes: bytes, lock: Any,
    freeze_bytes: bytes, freeze: Any, manifest: Any,
) -> None:
    _validate_static_contract(candidate, gate, lock, lock_bytes)
    expected = candidate["expectedInputs"]
    actual = {
        "datasetSha256": dataset_sha,
        "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
        "stressGroundTruthSha256": hashlib.sha256(stress_bytes).hexdigest(),
        "foundationFreezeSha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "foundationLockSha256": hashlib.sha256(lock_bytes).hexdigest(),
    }
    if expected != actual:
        raise DatasetValidationError("E12.3 frozen input hashes do not match.")
    if freeze.get("freezeId") != lock.get("lockId") or lock.get("hashes", {}).get("foundationFreezeSha256") != actual["foundationFreezeSha256"]:
        raise DatasetValidationError("E12.3 foundation freeze and lock differ.")
    if not isinstance(manifest, dict) or manifest.get("status") != "preregistered" or manifest.get("modelId") != MODEL_ID or manifest.get("expectedInputs") != expected:
        raise DatasetValidationError("E12.3 preregistration is invalid.")
    if manifest.get("candidate", {}).get("sha256") != hashlib.sha256(candidate_bytes).hexdigest() or manifest.get("gate", {}).get("sha256") != hashlib.sha256(gate_bytes).hexdigest() or manifest.get("foundationLock", {}).get("sha256") != hashlib.sha256(lock_bytes).hexdigest():
        raise DatasetValidationError("E12.3 preregistration does not bind config, gate and lock.")


def _labels_for_date(value: str, episodes: list[dict[str, Any]]) -> set[str]:
    month = date.fromisoformat(value).replace(day=1)
    return {code for episode in episodes if episode["first"] <= month <= episode["last"] for code in episode["labels"]}


def _episode_diagnostics(keys: list[str], predictions: dict[str, dict[str, Any]], episodes: list[dict[str, Any]], role: str) -> dict[str, Any]:
    reports = []
    for episode in episodes:
        if episode.get("validationRole") != role or "financial_stress" not in episode["labels"]:
            continue
        selected = [key for key in keys if episode["first"] <= date.fromisoformat(key).replace(day=1) <= episode["last"]]
        if not selected:
            continue
        alerts = [key for key in selected if predictions[key]["predictedFinancialStress"]]
        reports.append({"episodeId": episode["id"], "observedMonths": selected, "alertMonths": alerts, "hit": bool(alerts)})
    hits = sum(item["hit"] for item in reports)
    return {"episodeCount": len(reports), "hitCount": hits, "hitRate": round(hits / len(reports), 8) if reports else None, "episodes": reports}


def _longest_alert_run(keys: list[str], predictions: dict[str, dict[str, Any]]) -> int:
    longest = current = 0
    previous: date | None = None
    for key in keys:
        current_date = date.fromisoformat(key)
        consecutive = previous is not None and (current_date.year * 12 + current_date.month) == (previous.year * 12 + previous.month + 1)
        current = current + 1 if predictions[key]["predictedFinancialStress"] and consecutive else (1 if predictions[key]["predictedFinancialStress"] else 0)
        longest = max(longest, current)
        previous = current_date
    return longest


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-700.0, min(700.0, value))))


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write_new_json(path: str | Path, payload: dict[str, Any], message: str) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"{message}: '{destination}'.") from exc
    return destination
