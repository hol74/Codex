from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError, load_dataset


CONTRACT_ID = "e12-task-lifecycle-v1"
INTRAMONTH_FEATURES = (
    "VIX_MONTHLY_MAX",
    "SOFR_EFFR_MONTHLY_MAX",
    "SPY_MONTHLY_MAX_DRAWDOWN",
    "HYG_MONTHLY_MAX_DRAWDOWN",
)


def write_e12_foundation_report(
    corpus_manifest_path: str | Path,
    dataset_path: str | Path,
    plan_path: str | Path,
    lifecycle_path: str | Path,
    output_path: str | Path,
) -> Path:
    corpus_file, corpus_bytes, corpus = _read_json(corpus_manifest_path, "corpus manifest")
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    lifecycle_file, lifecycle_bytes, lifecycle = _read_json(lifecycle_path, "E12 lifecycle")
    dataset = load_dataset(dataset_path)
    _validate_inputs(corpus, dataset, plan, lifecycle)

    feature_codes = sorted({
        code
        for task in lifecycle["tasks"].values()
        for code in task["requiredInputs"]
    })
    by_date = {
        row["asOfDate"]: {
            str(item.get("seriesCode"))
            for item in row["macroObservations"]
            if item.get("seriesCode")
        }
        for row in dataset.rows
    }
    overall = {
        code: _coverage(code, tuple(by_date.items()))
        for code in feature_codes
    }
    folds = []
    for fold in plan["folds"]:
        train_from = _iso_date(fold["train_from"], "fold.train_from")
        train_to = _iso_date(fold["train_to"], "fold.train_to")
        test_from = _iso_date(fold["test_from"], "fold.test_from")
        test_to = _iso_date(fold["test_to"], "fold.test_to")
        train_rows = tuple((key, codes) for key, codes in by_date.items() if train_from <= date.fromisoformat(key) <= train_to)
        test_rows = tuple((key, codes) for key, codes in by_date.items() if test_from <= date.fromisoformat(key) <= test_to)
        folds.append({
            "number": fold["number"],
            "train": {"rowCount": len(train_rows), "features": {code: _coverage(code, train_rows) for code in feature_codes}},
            "test": {"rowCount": len(test_rows), "features": {code: _coverage(code, test_rows) for code in feature_codes}},
        })

    declared_counts = corpus["intramonthFeatureObservationCounts"]
    observed_counts = {code: overall[code]["presentRowCount"] for code in INTRAMONTH_FEATURES}
    if any(declared_counts.get(code) != count for code, count in observed_counts.items()):
        raise DatasetValidationError("Corpus intramonth coverage counts do not match the dataset.")

    input_hashes = {
        "corpusManifest": _artifact(corpus_file, corpus_bytes),
        "dataset": _artifact(dataset.path, dataset.path.read_bytes()),
        "walkForwardPlan": _artifact(plan_file, plan_bytes),
        "taskLifecycle": _artifact(lifecycle_file, lifecycle_bytes),
    }
    freeze_seed = {
        "contractId": CONTRACT_ID,
        "inputs": {key: value["sha256"] for key, value in input_hashes.items()},
        "coverage": overall,
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E12DataFoundationFreeze",
        "status": "frozen",
        "freezeId": hashlib.sha256(_canonical_bytes(freeze_seed)).hexdigest()[:24],
        "frozenAt": lifecycle["frozenAt"],
        "contractId": CONTRACT_ID,
        "decisionScope": "data-coverage-only; no candidate ranking, tuning or promotion",
        "inputs": input_hashes,
        "datasetCoverage": {
            "from": dataset.dates[0].isoformat(),
            "to": dataset.dates[-1].isoformat(),
            "rowCount": len(dataset.rows),
            "foldCount": len(folds),
        },
        "pointInTimeValidation": "passed",
        "corpusConsistency": {
            "passed": True,
            "macroSnapshotCount": corpus["macroSnapshotCount"],
            "intramonthFeatureObservationCounts": observed_counts,
        },
        "featureCoverage": overall,
        "foldCoverage": folds,
        "tasks": lifecycle["tasks"],
        "missingnessPolicy": lifecycle["missingnessPolicy"],
        "selectionPolicy": lifecycle["selectionPolicy"],
        "nextAllowedAction": "freeze task-specific candidate formulas and gates before inner-only evaluation",
    }
    return _write_new_json(output_path, payload)


def _coverage(code: str, rows: tuple[tuple[str, set[str]], ...]) -> dict[str, Any]:
    present = [key for key, codes in rows if code in codes]
    total = len(rows)
    return {
        "presentRowCount": len(present),
        "missingRowCount": total - len(present),
        "coverageRatio": round(len(present) / total, 8) if total else 0.0,
        "firstAvailableDate": present[0] if present else None,
        "lastAvailableDate": present[-1] if present else None,
    }


def _validate_inputs(corpus: Any, dataset: Any, plan: Any, lifecycle: Any) -> None:
    if not isinstance(corpus, dict) or corpus.get("schemaVersion") != 2:
        raise DatasetValidationError("E12 requires corpus manifest schema version 2.")
    if corpus.get("macroSnapshotCount") != len(dataset.rows):
        raise DatasetValidationError("Corpus macro snapshot count does not match dataset rows.")
    if corpus.get("requestedFrom") != dataset.declared_from.isoformat() or corpus.get("requestedTo") != dataset.declared_to.isoformat():
        raise DatasetValidationError("Corpus and dataset declared ranges differ.")
    counts = corpus.get("intramonthFeatureObservationCounts")
    if not isinstance(counts, dict) or set(counts) != set(INTRAMONTH_FEATURES):
        raise DatasetValidationError("Corpus intramonth feature coverage is incomplete.")
    if not isinstance(plan, dict) or plan.get("foldCount") != len(plan.get("folds", [])) or plan.get("foldCount", 0) < 1:
        raise DatasetValidationError("Walk-forward plan is empty or inconsistent.")
    if not isinstance(lifecycle, dict) or lifecycle.get("schemaVersion") != 1 or lifecycle.get("contractId") != CONTRACT_ID:
        raise DatasetValidationError("Unsupported E12 task lifecycle.")
    tasks = lifecycle.get("tasks")
    if not isinstance(tasks, dict) or set(tasks) != {"recession-signal", "financial-stress-signal"}:
        raise DatasetValidationError("E12 lifecycle tasks are incomplete.")
    if lifecycle.get("maximumLifecycleBeforeFreshProspectiveEvidence") != "shadow-candidate" or "Nested inner" not in lifecycle.get("selectionPolicy", ""):
        raise DatasetValidationError("E12 lifecycle promotion or selection policy is unsafe.")
    for task in tasks.values():
        if not isinstance(task.get("requiredInputs"), list) or not task["requiredInputs"]:
            raise DatasetValidationError("Every E12 task requires declared inputs.")


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


def _iso_date(value: Any, location: str) -> date:
    if not isinstance(value, str):
        raise DatasetValidationError(f"{location} must be an ISO date.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid ISO date.") from exc


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E12 foundation freeze exists: '{destination}'.") from exc
    return destination
