from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .dataset import DatasetValidationError
from .shadow import _validate_ledger
from .shadow_ops import ensure_shadow_ledger, write_shadow_index, write_shadow_preflight


ORCHESTRATION_POLICY = "shadow-operations-v1"
FINAL_STATUSES = {"no-eligible-month", "prepared", "ledger-frozen", "failed"}


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


CommandRunner = Callable[[list[str], Path], CommandResult]


def run_shadow_operations(
    source_root: str | Path,
    operations_root: str | Path,
    model_config_path: str | Path,
    generated_at_utc: str,
    mode: str,
    result_path: str | Path,
    dotnet_executable: str = "dotnet",
    runner: CommandRunner | None = None,
) -> Path:
    if mode not in {"prepare-only", "full"}:
        raise DatasetValidationError("Shadow operations mode must be 'prepare-only' or 'full'.")
    generated_at = _utc_datetime(generated_at_utc)
    source = Path(source_root).resolve()
    operations = Path(operations_root).resolve()
    model_config = Path(model_config_path).resolve()
    if not (source / "MacroRegime.slnx").is_file():
        raise DatasetValidationError(f"Macro Regime source root is invalid: '{source}'.")
    if not model_config.is_file():
        raise DatasetValidationError(f"Shadow model config is missing: '{model_config}'.")

    ledger_directory = operations / "ledger"
    latest_closed = _latest_closed_month(generated_at.date())
    ledger_dates = _shadow_ledger_dates(ledger_directory)
    candidate = _next_candidate(ledger_dates, latest_closed)
    request = {
        "generatedAtUtc": generated_at_utc,
        "mode": mode,
        "latestClosedMonth": latest_closed.isoformat(),
        "lastLedgerAsOfDate": ledger_dates[-1].isoformat() if ledger_dates else None,
        "modelConfigFileName": model_config.name,
        "modelConfigSha256": _file_sha(model_config),
    }
    if candidate is None:
        return _write_result(result_path, {
            "schemaVersion": 1,
            "artifactType": "ShadowOperationsRun",
            "immutable": True,
            "policy": ORCHESTRATION_POLICY,
            "status": "no-eligible-month",
            "request": request,
            "operationalSideEffects": "result-only",
            "commandsExecuted": 0,
            "outcomesUsed": False,
        })

    paths = _cycle_paths(operations, candidate)
    state = _load_or_initialize_state(paths, candidate, request)
    actual_runner = runner or _subprocess_runner
    try:
        population_command = [
            dotnet_executable, "run", "--project", str(source / "src" / "MacroRegime.Cli"), "--",
            "--populate-historical-data",
            "--dataset-from", candidate.isoformat(),
            "--dataset-to", candidate.isoformat(),
            "--macro-data-dir", str(paths["macro"]),
            "--market-data-dir", str(paths["market"]),
            "--corpus-manifest", str(paths["corpus_manifest"]),
            "--forward-return-days", "28,56,91",
            "--output-dir", str(paths["source"]),
        ]
        _ensure_command_step(
            state, paths, "population", population_command, source, actual_runner,
            lambda: _population_artifacts(paths, candidate),
        )

        build_command = [
            dotnet_executable, "run", "--project", str(source / "src" / "MacroRegime.Cli"), "--",
            "--build-historical-dataset",
            "--dataset-from", candidate.isoformat(),
            "--dataset-to", candidate.isoformat(),
            "--macro-data-dir", str(paths["macro"]),
            "--market-data-dir", str(paths["market"]),
            "--forward-return-days", "28,56,91",
            "--output-dir", str(paths["dataset_dir"]),
        ]
        _ensure_command_step(
            state, paths, "dataset-build", build_command, source, actual_runner,
            lambda: [paths["dataset"]],
        )

        evaluation_command = [
            dotnet_executable, "run", "--project", str(source / "src" / "MacroRegime.Cli"), "--",
            "--evaluate-historical-baseline",
            "--dataset-file", str(paths["dataset"]),
            "--baseline-version", "v1.4",
            "--output-dir", str(paths["evaluation_dir"]),
        ]
        _ensure_command_step(
            state, paths, "evaluation", evaluation_command, source, actual_runner,
            lambda: [paths["evaluation"]],
        )

        _ensure_preflight_step(
            state, paths, source, model_config, candidate, generated_at_utc
        )
        if mode == "prepare-only":
            state["status"] = "prepared"
        else:
            _ensure_ledger_step(
                state, paths, model_config, candidate, generated_at_utc, ledger_directory
            )
            state["status"] = "ledger-frozen"
        state["lastUpdatedAtUtc"] = _now_utc()
        _write_state(paths["state"], state)
        return _write_result(result_path, _result_payload(state, request, paths))
    except (DatasetValidationError, OSError) as exc:
        state["status"] = "failed"
        state["lastUpdatedAtUtc"] = _now_utc()
        state["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        _write_state(paths["state"], state)
        payload = _result_payload(state, request, paths)
        payload["failure"] = state["failure"]
        return _write_result(result_path, payload)


def _ensure_command_step(
    state: dict[str, Any],
    paths: dict[str, Path],
    name: str,
    command: list[str],
    working_directory: Path,
    runner: CommandRunner,
    artifacts: Callable[[], list[Path]],
) -> None:
    step = state["steps"].setdefault(name, {"status": "pending", "attempts": []})
    command_sha = _sha256_json(command)
    if step["status"] == "completed":
        if step.get("commandSha256") != command_sha:
            raise DatasetValidationError(f"Completed shadow step '{name}' has a different command.")
        _validate_artifact_records(step.get("artifacts"), paths["cycle"])
        return
    attempt_number = len(step["attempts"]) + 1
    started = _now_utc()
    try:
        result = runner(command, working_directory)
    except Exception as exc:  # runner boundary: persist the failure before returning
        result = CommandResult(-1, "", f"{type(exc).__name__}: {exc}")
    finished = _now_utc()
    paths["logs"].mkdir(parents=True, exist_ok=True)
    stdout = paths["logs"] / f"{name}-attempt-{attempt_number:02d}.stdout.log"
    stderr = paths["logs"] / f"{name}-attempt-{attempt_number:02d}.stderr.log"
    stdout.write_text(result.stdout, encoding="utf-8", newline="\n")
    stderr.write_text(result.stderr, encoding="utf-8", newline="\n")
    attempt = {
        "attempt": attempt_number,
        "startedAtUtc": started,
        "finishedAtUtc": finished,
        "exitCode": result.exit_code,
        "stdoutFileName": stdout.name,
        "stdoutSha256": _file_sha(stdout),
        "stderrFileName": stderr.name,
        "stderrSha256": _file_sha(stderr),
    }
    step.update({
        "status": "failed" if result.exit_code else "running",
        "command": command,
        "commandSha256": command_sha,
    })
    step["attempts"].append(attempt)
    _write_state(paths["state"], state)
    if result.exit_code:
        raise DatasetValidationError(
            f"Shadow operations step '{name}' failed with exit code {result.exit_code}."
        )
    produced = artifacts()
    if not produced or any(not path.is_file() for path in produced):
        raise DatasetValidationError(f"Shadow operations step '{name}' did not produce its contract artifacts.")
    step["artifacts"] = [_artifact_record(path, paths["cycle"]) for path in produced]
    step["status"] = "completed"
    _write_state(paths["state"], state)


def _ensure_preflight_step(
    state: dict[str, Any],
    paths: dict[str, Path],
    source_root: Path,
    model_config: Path,
    candidate: date,
    generated_at_utc: str,
) -> None:
    step = state["steps"].setdefault("preflight", {"status": "pending"})
    if step["status"] == "completed":
        _validate_artifact_records(step.get("artifacts"), paths["cycle"])
        return
    write_shadow_preflight(
        paths["evaluation"], paths["dataset"], model_config,
        [candidate.isoformat()], generated_at_utc, source_root, paths["preflight"],
    )
    step.update({
        "status": "completed",
        "implementation": "regime_eval.shadow_ops.write_shadow_preflight",
        "artifacts": [_artifact_record(paths["preflight"], paths["cycle"])],
    })
    _write_state(paths["state"], state)


def _ensure_ledger_step(
    state: dict[str, Any],
    paths: dict[str, Path],
    model_config: Path,
    candidate: date,
    generated_at_utc: str,
    ledger_directory: Path,
) -> None:
    step = state["steps"].setdefault("ledger", {"status": "pending"})
    ledger = ledger_directory / f"prediction-ledger-{candidate.isoformat()}-v1-4.json"
    index = ledger_directory / "shadow-index.json"
    if step["status"] == "completed":
        _validate_artifact_records(step.get("artifacts"), ledger_directory)
        return
    ensure_shadow_ledger(
        paths["evaluation"], paths["dataset"], model_config, paths["preflight"],
        [candidate.isoformat()], generated_at_utc, ledger,
    )
    write_shadow_index(ledger_directory, index)
    step.update({
        "status": "completed",
        "implementation": "regime_eval.shadow_ops.ensure_shadow_ledger",
        "artifacts": [
            _artifact_record(ledger, ledger_directory),
            _artifact_record(index, ledger_directory),
        ],
    })
    _write_state(paths["state"], state)


def _load_or_initialize_state(
    paths: dict[str, Path], candidate: date, request: dict[str, Any]
) -> dict[str, Any]:
    paths["cycle"].mkdir(parents=True, exist_ok=True)
    if paths["state"].exists():
        try:
            state = json.loads(paths["state"].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise DatasetValidationError("Cannot resume an invalid shadow cycle state.") from exc
        if (
            not isinstance(state, dict)
            or state.get("artifactType") != "ShadowCycleState"
            or state.get("asOfDate") != candidate.isoformat()
            or state.get("modelConfigSha256") != request["modelConfigSha256"]
            or not isinstance(state.get("steps"), dict)
        ):
            raise DatasetValidationError("Existing shadow cycle state conflicts with this request.")
        state.pop("failure", None)
        state["status"] = "resuming"
        state["lastRequestedMode"] = request["mode"]
        _write_state(paths["state"], state)
        return state
    return {
        "schemaVersion": 1,
        "artifactType": "ShadowCycleState",
        "authoritative": False,
        "policy": ORCHESTRATION_POLICY,
        "asOfDate": candidate.isoformat(),
        "status": "initialized",
        "createdAtUtc": _now_utc(),
        "lastUpdatedAtUtc": _now_utc(),
        "lastRequestedMode": request["mode"],
        "modelConfigFileName": request["modelConfigFileName"],
        "modelConfigSha256": request["modelConfigSha256"],
        "steps": {},
    }


def _cycle_paths(operations: Path, candidate: date) -> dict[str, Path]:
    cycle = operations / "cycles" / candidate.strftime("%Y-%m")
    source = cycle / "source"
    dataset_dir = cycle / "dataset"
    evaluation_dir = cycle / "evaluation"
    return {
        "cycle": cycle,
        "source": source,
        "macro": source / "macro",
        "market": source / "market",
        "corpus_manifest": source / "corpus-manifest.json",
        "dataset_dir": dataset_dir,
        "dataset": dataset_dir / f"historical-dataset-{candidate.isoformat()}-{candidate.isoformat()}.json",
        "evaluation_dir": evaluation_dir,
        "evaluation": evaluation_dir / f"baseline-evaluation-{candidate.isoformat()}-{candidate.isoformat()}-v1-4-candidate.json",
        "preflight": cycle / "preflight" / f"shadow-preflight-{candidate.isoformat()}.json",
        "logs": cycle / "logs",
        "state": cycle / "cycle-state.json",
    }


def _population_artifacts(paths: dict[str, Path], candidate: date) -> list[Path]:
    macro = paths["macro"] / f"macro-data-{candidate.isoformat()}.json"
    market = sorted(paths["market"].glob("market-data-*.json"))
    if not market:
        raise DatasetValidationError("Historical population produced no market snapshots.")
    return [paths["corpus_manifest"], macro, *market]


def _shadow_ledger_dates(directory: Path) -> list[date]:
    dates: list[date] = []
    if not directory.exists():
        return dates
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
        try:
            ledger = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(ledger, dict) or ledger.get("artifactType") != "PredictionLedger":
            continue
        predictions = _validate_ledger(ledger)
        if ledger["runManifest"].get("runMode") != "shadow-live":
            continue
        if len(predictions) != 1:
            raise DatasetValidationError("Operational shadow ledgers must contain one prediction.")
        dates.append(date.fromisoformat(predictions[0]["asOfDate"]))
    if dates != sorted(set(dates)):
        raise DatasetValidationError("Operational shadow ledger dates must be unique.")
    return dates


def _next_candidate(existing: list[date], latest_closed: date) -> date | None:
    if not existing:
        return latest_closed
    candidate = _next_month_end(existing[-1])
    return candidate if candidate <= latest_closed else None


def _latest_closed_month(today: date) -> date:
    return date(today.year, today.month, 1) - timedelta(days=1)


def _next_month_end(value: date) -> date:
    next_month = date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)
    following = date(next_month.year + (next_month.month == 12), 1 if next_month.month == 12 else next_month.month + 1, 1)
    return following - timedelta(days=1)


def _result_payload(
    state: dict[str, Any], request: dict[str, Any], paths: dict[str, Path]
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "artifactType": "ShadowOperationsRun",
        "immutable": True,
        "policy": ORCHESTRATION_POLICY,
        "status": state["status"],
        "request": request,
        "asOfDate": state["asOfDate"],
        "cycleStateFileName": paths["state"].name,
        "cycleStateSha256": _file_sha(paths["state"]),
        "completedSteps": sorted(
            name for name, step in state["steps"].items() if step.get("status") == "completed"
        ),
        "commandsExecuted": sum(len(step.get("attempts", [])) for step in state["steps"].values()),
        "outcomesUsed": False,
    }


def _artifact_record(path: Path, relative_root: Path) -> dict[str, str]:
    return {
        "path": path.resolve().relative_to(relative_root.resolve()).as_posix(),
        "sha256": _file_sha(path),
    }


def _validate_artifact_records(value: Any, relative_root: Path) -> None:
    if not isinstance(value, list) or not value:
        raise DatasetValidationError("Completed shadow step has no artifact records.")
    for record in value:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise DatasetValidationError("Shadow step artifact record is invalid.")
        path = (relative_root / record["path"]).resolve()
        try:
            path.relative_to(relative_root.resolve())
        except ValueError as exc:
            raise DatasetValidationError("Shadow step artifact escapes its operational root.") from exc
        if not path.is_file() or _file_sha(path) != record.get("sha256"):
            raise DatasetValidationError(f"Completed shadow artifact changed or is missing: '{path}'.")


def _write_result(path: str | Path, payload: dict[str, Any]) -> Path:
    if payload.get("status") not in FINAL_STATUSES:
        raise DatasetValidationError("Shadow operations result has an invalid final status.")
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable shadow operations result exists: '{destination}'.") from exc
    return destination


def _write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _subprocess_runner(command: list[str], working_directory: Path) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=working_directory,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _utc_datetime(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DatasetValidationError("generatedAtUtc must be an ISO UTC timestamp ending in Z.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise DatasetValidationError("generatedAtUtc is not a valid timestamp.") from exc
    if parsed.tzinfo != timezone.utc:
        raise DatasetValidationError("generatedAtUtc must be UTC.")
    return parsed


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
