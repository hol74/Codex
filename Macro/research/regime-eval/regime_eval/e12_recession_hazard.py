from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .dimensional_baseline import _add_years, _false_positive_run
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics, calibration_table, probability_metrics


MODEL_ID = "sahm-yield-hazard-v1"
GATE_ID = "e12-recession-hazard-gate-v1"
REQUIRED_CODES = ("SAHM", "INDPRO_YOY", "YC_10Y2Y")


def recession_hazard_predictions(rows: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    history: list[float] = []
    predictions = []
    for row in sorted(rows, key=lambda item: item["asOfDate"]):
        values = {
            str(item.get("seriesCode")): float(item["value"])
            for item in row.get("macroObservations", [])
            if item.get("seriesCode") and item.get("value") is not None
        }
        missing = [code for code in REQUIRED_CODES if code not in values]
        if missing:
            raise DatasetValidationError(f"E12 recession row lacks inputs: {missing}.")
        curve = values["YC_10Y2Y"]
        trailing = (history + [curve])[-24:]
        minimum = min(trailing)
        sahm = _clip01(values["SAHM"] / 0.50)
        growth = _clip01((1.0 - values["INDPRO_YOY"]) / 7.0)
        inversion = _clip01(-minimum / 0.75)
        resteepening = _clip01((curve - minimum) / 1.0)
        transition = inversion * resteepening
        score = 0.50 * sahm + 0.30 * growth + 0.20 * transition
        probability = _sigmoid(8.0 * (score - 0.50))
        predictions.append({
            "asOfDate": row["asOfDate"],
            "modelId": MODEL_ID,
            "recessionProbability": round(probability, 8),
            "predictedRecession": probability >= float(config["decisionThreshold"]),
            "hazardScore": round(score, 8),
            "components": {
                "sahmSeverity": round(sahm, 8),
                "growthDeterioration": round(growth, 8),
                "curveInversion": round(inversion, 8),
                "curveResteepening": round(resteepening, 8),
                "curveTransition": round(transition, 8),
                "trailingCurveMinimum": round(minimum, 8),
            },
        })
        history.append(curve)
    return predictions


def write_e12_recession_preregistration(candidate_path: str | Path, gate_path: str | Path, foundation_lock_path: str | Path, output_path: str | Path) -> Path:
    candidate_file, candidate_bytes, candidate = _read_json(candidate_path, "E12 recession candidate")
    gate_file, gate_bytes, gate = _read_json(gate_path, "E12 recession gate")
    lock_file, lock_bytes, lock = _read_json(foundation_lock_path, "E12 foundation lock")
    _validate_static(candidate, gate, lock, lock_bytes)
    seed = {"candidate": hashlib.sha256(candidate_bytes).hexdigest(), "gate": hashlib.sha256(gate_bytes).hexdigest(), "lock": hashlib.sha256(lock_bytes).hexdigest()}
    payload = {
        "schemaVersion": 1,
        "artifactType": "E12RecessionHazardPreregistration",
        "registrationId": hashlib.sha256(_canonical_bytes(seed)).hexdigest()[:24],
        "status": "preregistered",
        "frozenAt": candidate["frozenAt"],
        "modelId": MODEL_ID,
        "taskRole": "recession-signal",
        "candidate": _artifact(candidate_file, candidate_bytes),
        "gate": {**_artifact(gate_file, gate_bytes), "contractId": GATE_ID},
        "foundationLock": _artifact(lock_file, lock_bytes),
        "expectedInputs": candidate["expectedInputs"],
        "maximumLifecycle": "shadow-candidate",
        "outerOosPolicy": candidate["outerOosPolicy"],
        "implementation": {"module": "regime_eval.e12_recession_hazard", "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    return _write_new_json(output_path, payload)


def write_e12_recession_hazard_gate(
    dataset_path: str | Path, plan_path: str | Path, recession_truth_path: str | Path,
    candidate_path: str | Path, gate_path: str | Path, foundation_lock_path: str | Path,
    foundation_freeze_path: str | Path, preregistration_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    sources = [
        _read_json(plan_path, "walk-forward plan"),
        _read_json(recession_truth_path, "recession truth"),
        _read_json(candidate_path, "E12 recession candidate"),
        _read_json(gate_path, "E12 recession gate"),
        _read_json(foundation_lock_path, "E12 foundation lock"),
        _read_json(foundation_freeze_path, "E12 foundation freeze"),
        _read_json(preregistration_path, "E12 recession preregistration"),
    ]
    (plan_file, plan_bytes, plan), (truth_file, truth_bytes, truth), \
        (candidate_file, candidate_bytes, candidate), (gate_file, gate_bytes, gate), \
        (lock_file, lock_bytes, lock), (freeze_file, freeze_bytes, freeze), \
        (manifest_file, manifest_bytes, manifest) = sources
    periods = validate_recession_truth(truth)
    _validate_runtime(dataset.sha256, plan_bytes, truth_bytes, candidate_bytes, candidate, gate_bytes, gate, lock_bytes, lock, freeze_bytes, freeze, manifest)
    ordered_rows = sorted(dataset.rows, key=lambda item: item["asOfDate"])
    predictions = {item["asOfDate"]: item for item in recession_hazard_predictions(list(ordered_rows), candidate)}
    folds = plan.get("folds")
    inner_years = int(plan.get("config", {}).get("testYears", 0))
    if not isinstance(folds, list) or plan.get("foldCount") != len(folds) or inner_years <= 0:
        raise DatasetValidationError("E12.4 walk-forward plan is invalid.")
    unique: dict[str, dict[str, Any]] = {}
    fold_reports = []
    for fold in sorted(folds, key=lambda item: item["number"]):
        train_to = date.fromisoformat(fold["train_to"])
        test_from = date.fromisoformat(fold["test_from"])
        if train_to >= test_from:
            raise DatasetValidationError("E12.4 outer train/test windows overlap.")
        inner_from = _add_years(train_to, -inner_years)
        selected = [key for key in sorted(predictions) if inner_from < date.fromisoformat(key) <= train_to]
        if not selected or any(date.fromisoformat(key) >= test_from for key in selected):
            raise DatasetValidationError("E12.4 attempted to use an outer test row.")
        for key in selected:
            unique.setdefault(key, predictions[key])
        fold_reports.append({
            "number": fold["number"], "innerValidationFrom": selected[0], "innerValidationTo": selected[-1],
            "innerValidationRowCount": len(selected), "outerTestFrom": fold["test_from"],
            "outerTestTo": fold["test_to"], "outerTestRowCountUsed": 0, "eligible": True,
        })
    keys = sorted(unique)
    actual = {key: is_recession(key, periods) for key in keys}
    predicted = {key: bool(unique[key]["predictedRecession"]) for key in keys}
    probabilities = {key: float(unique[key]["recessionProbability"]) for key in keys}
    metrics = binary_metrics(actual, predicted)
    probabilistic = probability_metrics(actual, probabilities)
    calibration = calibration_table(actual, probabilities, 5)
    lag = _detection_lag(keys, predicted, periods)
    max_lag = max((item["detectionLagMonths"] for item in lag if item["detectionLagMonths"] is not None), default=None)
    requirements = gate["requirements"]
    fp_run = _false_positive_run(actual, predicted)
    checks = {
        "minimumEligibleFolds": len(fold_reports) >= int(requirements["minimumEligibleFolds"]),
        "minimumPositiveMonths": sum(actual.values()) >= int(requirements["minimumPositiveMonths"]),
        "recall": metrics["recall"] is not None and metrics["recall"] >= float(requirements["minimumRecall"]),
        "f1": metrics["f1"] is not None and metrics["f1"] >= float(requirements["minimumF1"]),
        "brierScore": probabilistic["brierScore"] <= float(requirements["maximumBrierScore"]),
        "averagePrecision": probabilistic["averagePrecision"] is not None and probabilistic["averagePrecision"] >= float(requirements["minimumAveragePrecision"]),
        "expectedCalibrationError": calibration["expectedCalibrationError"] <= float(requirements["maximumExpectedCalibrationError"]),
        "falsePositiveRun": fp_run <= int(requirements["maximumFalsePositiveRunMonths"]),
        "detectionLag": max_lag is not None and max_lag <= int(requirements["maximumDetectionLagMonths"]),
        "outerTestClosed": all(item["outerTestRowCountUsed"] == 0 for item in fold_reports),
    }
    passed = all(checks.values())
    report = {
        "reportVersion": 1, "reportType": "E12RecessionHazardInnerGate", "modelId": MODEL_ID,
        "taskRole": "recession-signal",
        "inputs": {
            "dataset": {"fileName": dataset.path.name, "sha256": dataset.sha256, "sizeBytes": dataset.size_bytes},
            "walkForwardPlan": _artifact(plan_file, plan_bytes), "recessionGroundTruth": _artifact(truth_file, truth_bytes),
            "candidateConfig": _artifact(candidate_file, candidate_bytes), "gate": _artifact(gate_file, gate_bytes),
            "foundationLock": _artifact(lock_file, lock_bytes), "foundationFreeze": _artifact(freeze_file, freeze_bytes),
            "preregistration": _artifact(manifest_file, manifest_bytes),
        },
        "protocol": {"scope": "nested-inner-validation-only", "uniqueDateAggregation": "earliest fold wins", "outerTestRowCountUsed": 0, "predictionLabelOrder": "all probabilities frozen before NBER labels are attached"},
        "coverage": {"foldCount": len(fold_reports), "uniqueInnerValidationRowCount": len(keys), "positiveMonthCount": sum(actual.values()), "from": keys[0], "to": keys[-1]},
        "metrics": metrics, "probabilityMetrics": probabilistic, "calibration": calibration,
        "falsePositiveRunMonths": fp_run, "episodeDiagnostics": lag,
        "gate": {"status": "ELIGIBLE_FOR_SHADOW_REVIEW" if passed else "REJECTED_FOR_SHADOW", "passed": passed, "checks": checks, "maximumLifecycle": "shadow-candidate", "operationalApprovalAuthorized": False},
        "folds": fold_reports,
        "predictions": [{**unique[key], "actualRecession": actual[key]} for key in keys],
        "implementation": {"module": "regime_eval.e12_recession_hazard", "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _detection_lag(keys: list[str], predicted: dict[str, bool], periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for period in periods:
        available = [key for key in keys if period["first"] <= date.fromisoformat(key).replace(day=1) <= period["trough"]]
        if not available:
            continue
        hits = [key for key in available if predicted[key]]
        first = date.fromisoformat(available[0])
        hit = date.fromisoformat(hits[0]) if hits else None
        output.append({"name": period["name"], "firstAvailableRecessionSample": available[0], "firstSignal": hits[0] if hits else None, "detectionLagMonths": ((hit.year-first.year)*12+hit.month-first.month) if hit else None})
    return output


def _validate_static(candidate: Any, gate: Any, lock: Any, lock_bytes: bytes) -> None:
    if not isinstance(candidate, dict) or candidate.get("modelId") != MODEL_ID or candidate.get("taskRole") != "recession-signal" or candidate.get("benchmarkScope") != "nested-inner-validation-only":
        raise DatasetValidationError("Unsupported E12 recession candidate.")
    if candidate.get("expectedInputs", {}).get("foundationLockSha256") != hashlib.sha256(lock_bytes).hexdigest() or candidate.get("decisionThreshold") != 0.5:
        raise DatasetValidationError("E12 recession candidate does not bind the foundation or formula.")
    if not isinstance(gate, dict) or gate.get("contractId") != GATE_ID or gate.get("registeredModelId") != MODEL_ID or gate.get("targetLifecycle") != "shadow-candidate":
        raise DatasetValidationError("Unsupported E12 recession gate.")
    if not isinstance(lock, dict) or lock.get("status") != "frozen":
        raise DatasetValidationError("Invalid E12 foundation lock.")


def _validate_runtime(dataset_sha: str, plan_bytes: bytes, truth_bytes: bytes, candidate_bytes: bytes, candidate: Any, gate_bytes: bytes, gate: Any, lock_bytes: bytes, lock: Any, freeze_bytes: bytes, freeze: Any, manifest: Any) -> None:
    _validate_static(candidate, gate, lock, lock_bytes)
    actual = {"datasetSha256": dataset_sha, "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(), "recessionGroundTruthSha256": hashlib.sha256(truth_bytes).hexdigest(), "foundationFreezeSha256": hashlib.sha256(freeze_bytes).hexdigest(), "foundationLockSha256": hashlib.sha256(lock_bytes).hexdigest()}
    if candidate.get("expectedInputs") != actual:
        raise DatasetValidationError("E12.4 frozen input hashes do not match.")
    if freeze.get("freezeId") != lock.get("lockId") or lock.get("hashes", {}).get("foundationFreezeSha256") != actual["foundationFreezeSha256"]:
        raise DatasetValidationError("E12.4 foundation freeze and lock differ.")
    if not isinstance(manifest, dict) or manifest.get("status") != "preregistered" or manifest.get("modelId") != MODEL_ID or manifest.get("expectedInputs") != actual:
        raise DatasetValidationError("E12.4 preregistration is invalid.")
    if manifest.get("candidate", {}).get("sha256") != hashlib.sha256(candidate_bytes).hexdigest() or manifest.get("gate", {}).get("sha256") != hashlib.sha256(gate_bytes).hexdigest() or manifest.get("foundationLock", {}).get("sha256") != hashlib.sha256(lock_bytes).hexdigest():
        raise DatasetValidationError("E12.4 preregistration bindings differ.")


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


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E12 recession preregistration exists: '{destination}'.") from exc
    return destination
