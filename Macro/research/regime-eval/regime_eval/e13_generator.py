from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


TASKS = {"financial-stress-signal", "recession-signal"}
ALLOWED_AGGREGATORS = {
    "financial-stress-signal": {"noisy-or", "top-two-mean"},
    "recession-signal": {"max-confirmation", "weighted-hazard"},
}


def write_e13_candidate_manifest(protocol_path: str | Path, output_path: str | Path) -> Path:
    protocol_file = Path(protocol_path).resolve()
    try:
        protocol_bytes = protocol_file.read_bytes()
        protocol = json.loads(protocol_bytes)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid E13 protocol JSON '{protocol_file}'.") from exc
    _validate_protocol(protocol)

    candidates: list[dict[str, Any]] = []
    for task in sorted(TASKS):
        grammar = protocol["tasks"][task]
        for aggregator, entry, recovery in itertools.product(
            sorted(grammar["aggregators"]),
            sorted(grammar["entryPersistenceMonths"]),
            sorted(grammar["recoveryPersistenceMonths"]),
        ):
            parameters = {
                "aggregator": aggregator,
                "entryPersistenceMonths": entry,
                "recoveryPersistenceMonths": recovery,
                "thresholdCandidates": protocol["thresholdSelection"]["values"],
                "thresholdSelectionScope": "inner-fit-only",
            }
            identity = {"protocolId": protocol["protocolId"], "task": task, "parameters": parameters}
            suffix = hashlib.sha256(_canonical_bytes(identity)).hexdigest()[:10]
            candidates.append({
                "candidateId": f"e13-{_task_slug(task)}-{suffix}",
                "task": task,
                "lifecycleStatus": "research-generated",
                "parameters": parameters,
            })

    if len(candidates) != protocol["candidateBudget"]:
        raise DatasetValidationError("E13 grammar expansion does not match the frozen candidate budget.")
    ids = [candidate["candidateId"] for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise DatasetValidationError("E13 generated candidate ids are not unique.")

    payload = {
        "schemaVersion": 1,
        "artifactType": "GeneratedCandidateManifest",
        "immutable": True,
        "status": "generated-not-evaluated",
        "generationId": hashlib.sha256(_canonical_bytes({
            "protocolSha256": hashlib.sha256(protocol_bytes).hexdigest(),
            "candidateIds": ids,
        })).hexdigest()[:24],
        "protocol": {
            "fileName": protocol_file.name,
            "protocolId": protocol["protocolId"],
            "sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        },
        "foundationLockSha256": protocol["foundationLockSha256"],
        "candidateCount": len(candidates),
        "outerOosOpened": False,
        "selectionPolicy": protocol["selectionPolicy"],
        "candidates": candidates,
        "implementation": {
            "module": "regime_eval.e13_generator",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _validate_protocol(protocol: Any) -> None:
    if (
        not isinstance(protocol, dict)
        or protocol.get("schemaVersion") != 1
        or protocol.get("protocolId") != "e13-candidate-generation-protocol-v1"
        or protocol.get("candidateBudget") != 16
        or protocol.get("lifecycleBoundary") != "research-generated"
        or not _sha256(protocol.get("foundationLockSha256"))
    ):
        raise DatasetValidationError("Unsupported E13 candidate-generation protocol.")
    tasks = protocol.get("tasks")
    if not isinstance(tasks, dict) or set(tasks) != TASKS:
        raise DatasetValidationError("E13 must keep the two task grammars separate.")
    for task, grammar in tasks.items():
        if (
            not isinstance(grammar, dict)
            or set(grammar.get("aggregators", [])) != ALLOWED_AGGREGATORS[task]
            or grammar.get("entryPersistenceMonths") != [1, 2]
            or grammar.get("recoveryPersistenceMonths") != [1, 2]
        ):
            raise DatasetValidationError(f"E13 grammar is invalid for task '{task}'.")
    thresholds = protocol.get("thresholdSelection")
    selection = protocol.get("selectionPolicy")
    constraints = protocol.get("constraints")
    if (
        not isinstance(thresholds, dict)
        or thresholds.get("values") != [0.35, 0.5, 0.65]
        or thresholds.get("scope") != "inner-fit-only"
        or not isinstance(selection, dict)
        or selection.get("method") != "leave-one-episode-out-within-inner-validation"
        or selection.get("maximumShortlistPerTask") != 2
        or "Forbidden" not in str(selection.get("outerOos"))
        or not isinstance(constraints, dict)
        or not all(constraints.get(key) is True for key in (
            "deterministicEnumeration", "causalFeaturesOnly", "trainOnlyTransforms",
            "missingValuesRemainExplicit",
        ))
        or constraints.get("crossTaskFusion") is not False
        or constraints.get("reuseRejectedE12CandidateIds") is not False
    ):
        raise DatasetValidationError("E13 selection and leakage controls are incomplete.")


def _task_slug(task: str) -> str:
    return "financial" if task == "financial-stress-signal" else "recession"


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E13 candidate manifest exists: '{destination}'.") from exc
    return destination


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
