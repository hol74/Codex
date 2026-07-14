from __future__ import annotations

import hashlib
import json
import math
import platform
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .dataset import DatasetValidationError, load_dataset
from .ground_truth import is_recession, validate_recession_truth
from .metrics import binary_metrics


REGIME_NAMES = {
    "Goldilocks",
    "Reflation",
    "LateCycleOverheating",
    "Stagflation",
    "DeflationBust",
}
REGIME_PROBABILITY_NAMES = REGIME_NAMES | {"UncertainTransition"}


def write_baseline_prediction_ledger(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    model_config_path: str | Path,
    as_of_dates: Iterable[str],
    generated_at_utc: str,
    run_mode: str,
    output_path: str | Path,
    preflight_path: str | Path | None = None,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(
        evaluation_path, "baseline evaluation"
    )
    config_file, config_bytes, config = _read_json(model_config_path, "model config")
    generated_at = _utc_datetime(generated_at_utc, "generatedAtUtc")
    if run_mode not in {"dry-run", "shadow-live"}:
        raise DatasetValidationError("runMode must be 'dry-run' or 'shadow-live'.")
    _validate_baseline_source(evaluation, config, dataset.sha256)

    requested = list(as_of_dates)
    if not requested or len(requested) != len(set(requested)):
        raise DatasetValidationError("At least one unique as-of date is required.")
    requested_dates = sorted(_iso_date(value, "asOfDate") for value in requested)
    if generated_at.date() < requested_dates[-1]:
        raise DatasetValidationError("generatedAtUtc cannot precede a prediction as-of date.")

    rows = {row["asOfDate"]: row for row in evaluation["rows"]}
    missing = [value.isoformat() for value in requested_dates if value.isoformat() not in rows]
    if missing:
        raise DatasetValidationError(f"Prediction dates are missing from evaluation: {', '.join(missing)}.")

    preflight_input = _preflight_input(
        preflight_path,
        evaluation_bytes,
        dataset.path.read_bytes(),
        config_bytes,
        requested_dates,
        generated_at,
        run_mode,
    )

    evaluation_sha = hashlib.sha256(evaluation_bytes).hexdigest()
    config_sha = hashlib.sha256(config_bytes).hexdigest()
    source_sha = _source_fingerprint()
    run_seed = {
        "evaluationSha256": evaluation_sha,
        "datasetSha256": dataset.sha256,
        "modelConfigSha256": config_sha,
        "asOfDates": [value.isoformat() for value in requested_dates],
        "generatedAtUtc": generated_at_utc,
        "runMode": run_mode,
        "sourceSha256": source_sha,
        "preflightSha256": preflight_input["sha256"] if preflight_input else None,
    }
    run_id = hashlib.sha256(_canonical_bytes(run_seed)).hexdigest()[:24]
    predictions = [
        _prediction_record(rows[value.isoformat()], value, generated_at_utc, run_id)
        for value in requested_dates
    ]
    payload = {
        "schemaVersion": 1,
        "artifactType": "PredictionLedger",
        "lifecycleStatus": "predicted",
        "immutable": True,
        "runManifest": {
            "runId": run_id,
            "runMode": run_mode,
            "generatedAtUtc": generated_at_utc,
            "implementation": {
                "module": "regime_eval.shadow",
                "sourceSha256": source_sha,
                "pythonImplementation": platform.python_implementation(),
                "pythonVersion": platform.python_version(),
            },
            "inputs": {
                "datasetFileName": dataset.path.name,
                "datasetSha256": dataset.sha256,
                "evaluationFileName": evaluation_file.name,
                "evaluationSha256": evaluation_sha,
                "modelConfigFileName": config_file.name,
                "modelConfigSha256": config_sha,
                **({
                    "preflightFileName": preflight_input["fileName"],
                    "preflightSha256": preflight_input["sha256"],
                } if preflight_input else {}),
            },
        },
        "evaluationTask": {
            "taskId": "US_RECESSION_DETECTION",
            "taskType": "RecessionDetection",
            "decisionPolicy": "operational regime equals DeflationBust",
            "probabilityField": "recessionProbability",
        },
        "model": {
            "modelId": config.get("name", evaluation.get("modelName", "baseline")),
            "modelVersion": evaluation["modelVersion"],
            "role": "baseline",
            "lifecycleStatus": "evaluated",
            "developmentDatasetSha256": config.get("datasetSha256"),
        },
        "predictionCount": len(predictions),
        "predictions": predictions,
    }
    return _write_new_json(output_path, payload)


def _preflight_input(
    preflight_path: str | Path | None,
    evaluation_bytes: bytes,
    dataset_bytes: bytes,
    config_bytes: bytes,
    requested_dates: list[date],
    generated_at: datetime,
    run_mode: str,
) -> dict[str, str] | None:
    if preflight_path is None:
        if run_mode == "shadow-live":
            raise DatasetValidationError("shadow-live requires a passed ShadowPreflight artifact.")
        return None
    preflight_file, preflight_bytes, preflight = _read_json(preflight_path, "shadow preflight")
    if not isinstance(preflight, dict):
        raise DatasetValidationError("ShadowPreflight must be a JSON object.")
    expected_dates = [value.isoformat() for value in requested_dates]
    inputs = preflight.get("inputs")
    if (
        preflight.get("schemaVersion") != 1
        or preflight.get("artifactType") != "ShadowPreflight"
        or preflight.get("immutable") is not True
        or preflight.get("status") != "passed"
        or preflight.get("asOfDates") != expected_dates
        or not isinstance(inputs, dict)
        or inputs.get("datasetSha256") != hashlib.sha256(dataset_bytes).hexdigest()
        or inputs.get("evaluationSha256") != hashlib.sha256(evaluation_bytes).hexdigest()
        or inputs.get("modelConfigSha256") != hashlib.sha256(config_bytes).hexdigest()
    ):
        raise DatasetValidationError("ShadowPreflight does not match the prediction inputs.")
    prepared_at = _utc_datetime(preflight.get("generatedAtUtc"), "preflight.generatedAtUtc")
    if prepared_at > generated_at:
        raise DatasetValidationError("ShadowPreflight cannot be generated after the prediction ledger.")
    implementation = preflight.get("implementation")
    if (
        not isinstance(implementation, dict)
        or not _sha256_value(implementation.get("csharpSourceSha256"))
        or not _sha256_value(implementation.get("pythonSourceSha256"))
    ):
        raise DatasetValidationError("ShadowPreflight implementation fingerprints are invalid.")
    return {
        "fileName": preflight_file.name,
        "sha256": hashlib.sha256(preflight_bytes).hexdigest(),
    }


def write_shadow_score(
    ledger_path: str | Path,
    ground_truth_path: str | Path,
    scored_at_utc: str,
    output_path: str | Path,
) -> Path:
    ledger_file, ledger_bytes, ledger = _read_json(ledger_path, "prediction ledger")
    truth_file, truth_bytes, truth = _read_json(ground_truth_path, "ground truth")
    _utc_datetime(scored_at_utc, "scoredAtUtc")
    predictions = _validate_ledger(ledger)
    periods = validate_recession_truth(truth)
    coverage_from = _iso_date(truth.get("coverageFrom"), "groundTruth.coverageFrom")
    coverage_to = _iso_date(truth.get("coverageTo"), "groundTruth.coverageTo")
    dates = [_iso_date(item["asOfDate"], "prediction.asOfDate") for item in predictions]
    if any(not coverage_from <= value <= coverage_to for value in dates):
        raise DatasetValidationError("Ground truth does not cover every prediction date.")

    actual = {item["asOfDate"]: is_recession(item["asOfDate"], periods) for item in predictions}
    predicted = {item["asOfDate"]: bool(item["predictedRecession"]) for item in predictions}
    probabilities = {
        item["asOfDate"]: float(item["recessionProbability"]) for item in predictions
    }
    scored_predictions = [
        {
            "predictionId": item["predictionId"],
            "asOfDate": item["asOfDate"],
            "predictedRecession": item["predictedRecession"],
            "recessionProbability": item["recessionProbability"],
            "actualRecession": actual[item["asOfDate"]],
        }
        for item in predictions
    ]
    payload = {
        "schemaVersion": 1,
        "artifactType": "PredictionScore",
        "lifecycleStatus": "scored",
        "immutable": True,
        "scoredAtUtc": scored_at_utc,
        "predictionLedger": {
            "fileName": ledger_file.name,
            "sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "runId": ledger["runManifest"]["runId"],
        },
        "groundTruth": {
            "fileName": truth_file.name,
            "sha256": hashlib.sha256(truth_bytes).hexdigest(),
            "groundTruthId": truth["groundTruthId"],
        },
        "metrics": binary_metrics(actual, predicted),
        "probabilityMetrics": _probability_metrics(actual, probabilities),
        "predictions": scored_predictions,
    }
    return _write_new_json(output_path, payload)


def write_gate_decision(
    report_path: str | Path,
    decision: str,
    reviewer: str,
    rationale: str,
    decided_at_utc: str,
    output_path: str | Path,
) -> Path:
    report_file, report_bytes, report = _read_json(report_path, "model report")
    _utc_datetime(decided_at_utc, "decidedAtUtc")
    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approved", "rejected", "deferred"}:
        raise DatasetValidationError("Gate decision must be approved, rejected, or deferred.")
    if not reviewer.strip() or not rationale.strip():
        raise DatasetValidationError("Gate reviewer and rationale are required.")
    automatic = report.get("modelGate")
    if not isinstance(automatic, dict) or not isinstance(automatic.get("passedAutomaticMetrics"), bool):
        raise DatasetValidationError("Model report does not contain a valid automatic gate.")
    if normalized_decision == "approved" and not automatic["passedAutomaticMetrics"]:
        raise DatasetValidationError("A failed automatic gate cannot receive an approved decision.")
    challenger = report.get("challenger")
    model_id = challenger.get("modelId") if isinstance(challenger, dict) else None
    if not isinstance(model_id, str) or not model_id:
        raise DatasetValidationError("Model report challenger id is missing.")
    payload = {
        "schemaVersion": 1,
        "artifactType": "GateDecision",
        "immutable": True,
        "model": {
            "modelId": model_id,
            "role": "challenger",
            "lifecycleStatus": {
                "approved": "approved",
                "rejected": "rejected",
                "deferred": "evaluated",
            }[normalized_decision],
        },
        "sourceReport": {
            "fileName": report_file.name,
            "sha256": hashlib.sha256(report_bytes).hexdigest(),
        },
        "automaticGate": automatic,
        "humanDecision": {
            "decision": normalized_decision,
            "reviewer": reviewer.strip(),
            "rationale": rationale.strip(),
            "decidedAtUtc": decided_at_utc,
        },
    }
    return _write_new_json(output_path, payload)


def _prediction_record(
    row: dict[str, Any], as_of: date, generated_at_utc: str, run_id: str
) -> dict[str, Any]:
    probabilities_value = row.get("probabilities")
    if not isinstance(probabilities_value, list):
        raise DatasetValidationError(f"Evaluation row {as_of} has no regime probabilities.")
    probabilities: dict[str, float] = {}
    for item in probabilities_value:
        if not isinstance(item, dict) or item.get("regime") not in REGIME_PROBABILITY_NAMES:
            raise DatasetValidationError(f"Evaluation row {as_of} has invalid regime probabilities.")
        value = float(item.get("probability"))
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise DatasetValidationError(f"Evaluation row {as_of} has invalid probability mass.")
        probabilities[str(item["regime"])] = value
    if set(probabilities) != REGIME_PROBABILITY_NAMES or not math.isclose(sum(probabilities.values()), 1.0, abs_tol=1e-6):
        raise DatasetValidationError(f"Evaluation row {as_of} probabilities must cover all regimes and sum to one.")
    primary = row.get("primaryRegime")
    operational = row.get("operationalRegime")
    if primary not in REGIME_NAMES or operational not in REGIME_NAMES | {"UncertainTransition"}:
        raise DatasetValidationError(f"Evaluation row {as_of} has invalid regime labels.")
    prediction_id = hashlib.sha256(f"{run_id}:{as_of.isoformat()}".encode()).hexdigest()[:24]
    return {
        "predictionId": prediction_id,
        "asOfDate": as_of.isoformat(),
        "forecastOrigin": as_of.isoformat(),
        "informationCutoff": as_of.isoformat(),
        "generatedAtUtc": generated_at_utc,
        "primaryRegime": primary,
        "operationalRegime": operational,
        "regimeProbabilities": {key: round(probabilities[key], 8) for key in sorted(probabilities)},
        "recessionProbability": round(probabilities["DeflationBust"], 8),
        "predictedRecession": operational == "DeflationBust",
        "warnings": [str(value) for value in row.get("warnings", [])],
        "sourceRowSha256": hashlib.sha256(_canonical_bytes(row)).hexdigest(),
    }


def _validate_baseline_source(evaluation: Any, config: Any, dataset_sha256: str) -> None:
    if (
        not isinstance(evaluation, dict)
        or evaluation.get("schemaVersion") != 1
        or evaluation.get("datasetSha256") != dataset_sha256
        or not isinstance(evaluation.get("rows"), list)
    ):
        raise DatasetValidationError("Baseline evaluation does not match the shadow dataset.")
    if (
        not isinstance(config, dict)
        or config.get("schemaVersion") != 1
        or config.get("modelVersion") != evaluation.get("modelVersion")
        or not isinstance(config.get("datasetSha256"), str)
        or len(config["datasetSha256"]) != 64
    ):
        raise DatasetValidationError("Model config is not bound to the evaluation model version.")


def _validate_ledger(ledger: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(ledger, dict)
        or ledger.get("schemaVersion") != 1
        or ledger.get("artifactType") != "PredictionLedger"
        or ledger.get("lifecycleStatus") != "predicted"
        or ledger.get("immutable") is not True
        or not isinstance(ledger.get("runManifest"), dict)
        or not isinstance(ledger.get("predictions"), list)
        or ledger.get("predictionCount") != len(ledger["predictions"])
    ):
        raise DatasetValidationError("Invalid prediction ledger contract.")
    predictions = ledger["predictions"]
    if not predictions:
        raise DatasetValidationError("Prediction ledger cannot be empty.")
    dates: list[str] = []
    for item in predictions:
        if not isinstance(item, dict) or "actualRecession" in item or "actualOutcome" in item:
            raise DatasetValidationError("Prediction ledger must not contain outcome labels.")
        required = {"predictionId", "asOfDate", "predictedRecession", "recessionProbability"}
        if not required <= item.keys() or not isinstance(item["predictedRecession"], bool):
            raise DatasetValidationError("Prediction ledger row is incomplete.")
        probability = item["recessionProbability"]
        if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
            raise DatasetValidationError("Prediction probability must be between zero and one.")
        dates.append(item["asOfDate"])
    if dates != sorted(set(dates)):
        raise DatasetValidationError("Prediction ledger dates must be unique and sorted.")
    return predictions


def _probability_metrics(actual: dict[str, bool], probabilities: dict[str, float]) -> dict[str, float]:
    if set(actual) != set(probabilities):
        raise DatasetValidationError("Actual and probability keys do not match.")
    brier = sum((probabilities[key] - float(actual[key])) ** 2 for key in actual) / len(actual)
    epsilon = 1e-15
    log_loss = -sum(
        math.log(min(1.0 - epsilon, max(epsilon, probabilities[key])))
        if actual[key]
        else math.log(min(1.0 - epsilon, max(epsilon, 1.0 - probabilities[key])))
        for key in actual
    ) / len(actual)
    return {"brierScore": round(brier, 8), "logLoss": round(log_loss, 8)}


def _source_fingerprint() -> str:
    digest = hashlib.sha256()
    root = Path(__file__).resolve().parent
    for path in sorted(root.glob("*.py"), key=lambda value: value.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _sha256_value(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value.lower()
    )


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable artifact already exists: '{destination}'.") from exc
    return destination


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _iso_date(value: Any, location: str) -> date:
    if not isinstance(value, str):
        raise DatasetValidationError(f"{location} must be an ISO date string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid ISO date.") from exc


def _utc_datetime(value: Any, location: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DatasetValidationError(f"{location} must be an ISO UTC timestamp ending in Z.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid timestamp.") from exc
    if parsed.tzinfo != timezone.utc:
        raise DatasetValidationError(f"{location} must be UTC.")
    return parsed
