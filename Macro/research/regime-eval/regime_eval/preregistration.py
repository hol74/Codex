from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .dataset import DatasetValidationError


MODEL_IDS = {
    "baseline-v1-5-dimensional",
    "changepoint-duration-v1",
    "rare-event-logit-v1",
}
EXPECTED_INPUT_KEYS = {
    "datasetSha256",
    "baselineEvaluationSha256",
    "walkForwardPlanSha256",
    "recessionGroundTruthSha256",
    "stressGroundTruthSha256",
}


def write_preregistration_manifest(
    gate_path: str | Path,
    model_config_paths: Iterable[str | Path],
    output_path: str | Path,
) -> Path:
    gate_file, gate_bytes, gate = _read_json(gate_path, "E11 gate")
    _validate_gate(gate)
    config_inputs = [_read_json(path, "E11 model config") for path in model_config_paths]
    if len(config_inputs) != gate["maximumRegisteredCandidates"]:
        raise DatasetValidationError("E11 requires exactly the preregistered candidate count.")

    candidates: list[dict[str, Any]] = []
    common_inputs: dict[str, str] | None = None
    ids: set[str] = set()
    for config_file, config_bytes, config in config_inputs:
        _validate_config(config, gate)
        model_id = config["modelId"]
        if model_id in ids:
            raise DatasetValidationError("E11 model ids must be unique.")
        ids.add(model_id)
        expected = config["expectedInputs"]
        if common_inputs is None:
            common_inputs = expected
        elif expected != common_inputs:
            raise DatasetValidationError("All E11 candidates must bind the same input artifacts.")
        candidates.append({
            "modelId": model_id,
            "modelFamily": config["modelFamily"],
            "role": config["role"],
            "lifecycleStatus": config["lifecycleStatus"],
            "promotionTarget": config["promotionTarget"],
            "configFileName": config_file.name,
            "configSha256": hashlib.sha256(config_bytes).hexdigest(),
        })
    if ids != set(gate["registeredModelIds"]) or ids != MODEL_IDS:
        raise DatasetValidationError("E11 candidate ids do not match the frozen gate.")

    candidates.sort(key=lambda item: item["modelId"])
    seed = {
        "gateSha256": hashlib.sha256(gate_bytes).hexdigest(),
        "candidateHashes": [item["configSha256"] for item in candidates],
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "ExperimentPreregistrationManifest",
        "immutable": True,
        "status": "preregistered",
        "registrationId": hashlib.sha256(_canonical_bytes(seed)).hexdigest()[:24],
        "frozenAt": gate["frozenAt"],
        "promotionBoundary": {
            "maximumBeforeFreshOutcomes": gate["targetLifecycle"],
            "forbiddenWithoutProspectiveEvidence": gate["forbiddenLifecycle"],
        },
        "selectionDataPolicy": gate["selectionDataPolicy"],
        "gate": {
            "fileName": gate_file.name,
            "sha256": hashlib.sha256(gate_bytes).hexdigest(),
            "contractId": gate["contractId"],
        },
        "expectedInputs": common_inputs,
        "candidateCount": len(candidates),
        "candidates": candidates,
        "implementation": {
            "module": "regime_eval.preregistration",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _validate_gate(gate: Any) -> None:
    if (
        not isinstance(gate, dict)
        or gate.get("schemaVersion") != 1
        or gate.get("contractId") != "e11-shadow-candidate-gate-v1"
        or gate.get("targetLifecycle") != "shadow-candidate"
        or gate.get("forbiddenLifecycle") != "operational-approved"
        or gate.get("maximumRegisteredCandidates") != 3
    ):
        raise DatasetValidationError("Unsupported E11 shadow-candidate gate.")
    registered = gate.get("registeredModelIds")
    if not isinstance(registered, list) or len(registered) != len(set(registered)) or set(registered) != MODEL_IDS:
        raise DatasetValidationError("E11 gate candidate registry is invalid.")
    _iso_date(gate.get("frozenAt"), "gate.frozenAt")
    data_policy = gate.get("selectionDataPolicy")
    technical = gate.get("technicalRequirements")
    validation = gate.get("innerValidation")
    if (
        not isinstance(data_policy, dict)
        or "outer OOS" not in str(data_policy.get("forbidden"))
        or "cannot select" not in str(data_policy.get("outerOosAfterFreeze"))
        or not isinstance(technical, dict)
        or not all(technical.get(key) is True for key in (
            "deterministicOutput", "testLabelIndependence", "causalPrediction",
            "trainOnlyTransforms", "configurationHashBound", "modelCardRequired",
            "humanReviewRequired",
        ))
        or not isinstance(validation, dict)
        or validation.get("minimumEligibleFolds", 0) < 1
    ):
        raise DatasetValidationError("E11 gate policies are incomplete or unsafe.")


def _validate_config(config: Any, gate: dict[str, Any]) -> None:
    if (
        not isinstance(config, dict)
        or config.get("schemaVersion") != 1
        or config.get("role") not in {"challenger", "challenger-baseline"}
        or config.get("lifecycleStatus") != "research-challenger"
        or config.get("promotionTarget") != gate["targetLifecycle"]
        or config.get("benchmarkScope") != "inner-validation-only"
        or not isinstance(config.get("modelId"), str)
        or not isinstance(config.get("modelFamily"), str)
    ):
        raise DatasetValidationError("Unsupported E11 candidate configuration.")
    if _iso_date(config.get("frozenAt"), "config.frozenAt") > _iso_date(gate["frozenAt"], "gate.frozenAt"):
        raise DatasetValidationError("E11 config cannot be frozen after its gate.")
    expected = config.get("expectedInputs")
    if not isinstance(expected, dict) or set(expected) != EXPECTED_INPUT_KEYS or any(
        not _sha256(value) for value in expected.values()
    ):
        raise DatasetValidationError("E11 expected input hashes are incomplete.")
    if (
        "Forbidden for selection" not in str(config.get("outerOosPolicy"))
        or not str(config.get("labelUse", "")).strip()
        or not str(config.get("selectionPolicy", "")).strip()
    ):
        raise DatasetValidationError("E11 candidate leakage/selection policy is invalid.")

    model_id = config["modelId"]
    if model_id == "baseline-v1-5-dimensional":
        if not isinstance(config.get("causalImpulsePolicy"), dict) or not _sha256(config.get("baseModelConfigSha256")):
            raise DatasetValidationError("Baseline v1.5 preregistration is incomplete.")
    elif model_id == "changepoint-duration-v1":
        if not all(isinstance(config.get(key), dict) for key in (
            "trainOnlyRobustScaling", "entryPolicy", "durationPolicy"
        )) or "causal" not in str(config.get("testInference", "")):
            raise DatasetValidationError("Changepoint preregistration is incomplete.")
    elif model_id == "rare-event-logit-v1":
        thresholds = config.get("decisionThresholdPolicy", {}).get("candidates")
        if (
            not isinstance(config.get("optimizer"), dict)
            or not isinstance(config.get("rareEventPolicy"), dict)
            or thresholds != [0.25, 0.35, 0.5]
        ):
            raise DatasetValidationError("Rare-event logit preregistration is incomplete.")
    else:
        raise DatasetValidationError("Unregistered E11 model id.")


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable preregistration manifest exists: '{destination}'.") from exc
    return destination


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def _iso_date(value: Any, location: str) -> date:
    if not isinstance(value, str):
        raise DatasetValidationError(f"{location} must be an ISO date.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid ISO date.") from exc
