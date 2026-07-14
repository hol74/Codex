from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.cli import main
from regime_eval.shadow_ops import CSHARP_SOURCE_PATHS, REQUIRED_MACRO_SERIES
from regime_eval.shadow_orchestrator import CommandResult, run_shadow_operations


class ShadowOrchestratorTests(unittest.TestCase):
    def test_no_eligible_month_writes_receipt_without_starting_a_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = _source_tree(root / "source")
            operations = root / "operations"
            _write(operations / "ledger" / "june.json", _ledger("2026-06-30"))
            config = _write(root / "config.json", _config())
            result = root / "no-eligible.json"

            self.assertEqual(0, main([
                "shadow-operations",
                "--source-root", str(source),
                "--operations-root", str(operations),
                "--model-config", str(config),
                "--generated-at-utc", "2026-07-14T08:00:00Z",
                "--mode", "prepare-only",
                "--result", str(result),
            ]))
            payload = _read(result)
            self.assertEqual("no-eligible-month", payload["status"])
            self.assertEqual(0, payload["commandsExecuted"])
            self.assertEqual("2026-06-30", payload["request"]["latestClosedMonth"])
            self.assertFalse((operations / "cycles").exists())

    def test_prepare_only_can_resume_as_full_without_repeating_csharp_steps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = _source_tree(root / "source")
            operations = root / "operations"
            _write(operations / "ledger" / "june.json", _ledger("2026-06-30"))
            config = _write(root / "config.json", _config())
            calls: list[str] = []

            prepared = run_shadow_operations(
                source, operations, config, "2026-08-01T08:00:00Z", "prepare-only",
                root / "prepared.json", runner=_successful_runner(calls),
            )
            prepared_payload = _read(prepared)
            self.assertEqual("prepared", prepared_payload["status"])
            self.assertEqual(["population", "dataset-build", "evaluation"], calls)
            self.assertFalse((operations / "ledger" / "prediction-ledger-2026-07-31-v1-4.json").exists())

            calls.clear()
            frozen = run_shadow_operations(
                source, operations, config, "2026-08-01T09:00:00Z", "full",
                root / "frozen.json", runner=_unexpected_runner(calls),
            )
            frozen_payload = _read(frozen)
            self.assertEqual("ledger-frozen", frozen_payload["status"])
            self.assertEqual([], calls)
            ledger = operations / "ledger" / "prediction-ledger-2026-07-31-v1-4.json"
            index = operations / "ledger" / "shadow-index.json"
            self.assertTrue(ledger.is_file())
            self.assertEqual(2, _read(index)["entryCount"])
            self.assertEqual(
                ["2026-06-30", "2026-07-31"],
                [entry["asOfDate"] for entry in _read(index)["entries"]],
            )
            self.assertFalse(_read(ledger)["predictions"][0].get("actualOutcome"))

            cycle = operations / "cycles" / "2026-07"
            state = _read(cycle / "cycle-state.json")
            self.assertEqual("ledger-frozen", state["status"])
            self.assertEqual(
                {"population", "dataset-build", "evaluation", "preflight", "ledger"},
                set(state["steps"]),
            )
            commands = json.dumps(state["steps"])
            self.assertNotIn("--fred-api-key", commands)
            self.assertNotIn("ground-truth", commands)

    def test_failed_build_is_recorded_and_retry_resumes_after_population(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = _source_tree(root / "source")
            operations = root / "operations"
            config = _write(root / "config.json", _config())
            first_calls: list[str] = []

            failed = run_shadow_operations(
                source, operations, config, "2026-08-01T08:00:00Z", "prepare-only",
                root / "failed.json", runner=_failing_build_runner(first_calls),
            )
            self.assertEqual("failed", _read(failed)["status"])
            self.assertEqual(["population", "dataset-build"], first_calls)

            retry_calls: list[str] = []
            recovered = run_shadow_operations(
                source, operations, config, "2026-08-01T08:30:00Z", "prepare-only",
                root / "recovered.json", runner=_successful_runner(retry_calls),
            )
            self.assertEqual("prepared", _read(recovered)["status"])
            self.assertEqual(["dataset-build", "evaluation"], retry_calls)
            state = _read(operations / "cycles" / "2026-07" / "cycle-state.json")
            self.assertEqual(1, len(state["steps"]["population"]["attempts"]))
            self.assertEqual(2, len(state["steps"]["dataset-build"]["attempts"]))
            self.assertEqual(2, state["steps"]["dataset-build"]["attempts"][0]["exitCode"])


def _successful_runner(calls: list[str]):
    def run(command: list[str], _: Path) -> CommandResult:
        step = _step(command)
        calls.append(step)
        if step == "population":
            macro = Path(_arg(command, "--macro-data-dir"))
            market = Path(_arg(command, "--market-data-dir"))
            as_of = _arg(command, "--dataset-to")
            _write(macro / f"macro-data-{as_of}.json", {"source": "test"})
            _write(market / f"market-data-{as_of}.json", {"source": "test"})
            _write(Path(_arg(command, "--corpus-manifest")), {"artifactType": "test"})
        elif step == "dataset-build":
            as_of = _arg(command, "--dataset-to")
            output = Path(_arg(command, "--output-dir")) / f"historical-dataset-{as_of}-{as_of}.json"
            _write(output, _dataset(as_of))
        else:
            dataset = Path(_arg(command, "--dataset-file"))
            as_of = _read(dataset)["to"]
            output = Path(_arg(command, "--output-dir")) / f"baseline-evaluation-{as_of}-{as_of}-v1-4-candidate.json"
            _write(output, _evaluation(_sha(dataset), as_of))
        return CommandResult(0, f"{step} completed\n", "")
    return run


def _failing_build_runner(calls: list[str]):
    successful = _successful_runner(calls)

    def run(command: list[str], working_directory: Path) -> CommandResult:
        if _step(command) == "dataset-build":
            calls.append("dataset-build")
            return CommandResult(2, "", "injected build failure")
        return successful(command, working_directory)
    return run


def _unexpected_runner(calls: list[str]):
    def run(command: list[str], _: Path) -> CommandResult:
        calls.append(_step(command))
        return CommandResult(99, "", "runner should not have been called")
    return run


def _step(command: list[str]) -> str:
    if "--populate-historical-data" in command:
        return "population"
    if "--build-historical-dataset" in command:
        return "dataset-build"
    if "--evaluate-historical-baseline" in command:
        return "evaluation"
    raise AssertionError(f"Unknown command: {command}")


def _arg(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def _source_tree(root: Path) -> Path:
    _write_text(root / "MacroRegime.slnx", "<Solution />\n")
    for relative in CSHARP_SOURCE_PATHS:
        path = root / relative
        if path.suffix == ".cs":
            _write_text(path, f"// {relative}\n")
        else:
            _write_text(path / "Contract.cs", f"// {relative}\n")
    return root


def _dataset(as_of: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "from": as_of,
        "to": as_of,
        "forwardReturnHorizonsDays": [28, 56, 91],
        "rows": [{
            "asOfDate": as_of,
            "macroObservations": [{
                "seriesCode": code,
                "observationDate": as_of,
                "publicationDate": as_of,
                "vintageDate": as_of,
                "value": index + 1,
            } for index, code in enumerate(sorted(REQUIRED_MACRO_SERIES))],
            "marketObservations": [{
                "symbol": "SPY", "observationDate": as_of,
                "availabilityDate": as_of, "value": 100,
            }],
            "forwardReturns": [],
        }],
    }


def _evaluation(dataset_sha: str, as_of: str) -> dict[str, object]:
    names = [
        "Goldilocks", "Reflation", "LateCycleOverheating", "Stagflation",
        "DeflationBust", "UncertainTransition",
    ]
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelName": "CRS Geometric Archetype Research Candidate",
        "modelVersion": "1.4-candidate",
        "rows": [{
            "asOfDate": as_of,
            "primaryRegime": "Goldilocks",
            "operationalRegime": "Goldilocks",
            "warnings": [],
            "probabilities": [{"regime": name, "probability": 1 / 6} for name in names],
        }],
    }


def _config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "name": "baseline-v1-4-preregistered",
        "modelVersion": "1.4-candidate",
        "datasetSha256": "d" * 64,
    }


def _ledger(as_of: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "artifactType": "PredictionLedger",
        "lifecycleStatus": "predicted",
        "immutable": True,
        "runManifest": {
            "runId": "test-run",
            "runMode": "shadow-live",
            "generatedAtUtc": "2026-07-13T12:59:41Z",
            "inputs": {},
        },
        "model": {"modelId": "baseline", "modelVersion": "1.4-candidate"},
        "predictionCount": 1,
        "predictions": [{
            "predictionId": "test-prediction",
            "asOfDate": as_of,
            "predictedRecession": False,
            "recessionProbability": 0.1,
            "operationalRegime": "Goldilocks",
        }],
    }


def _write(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _write_text(path: Path, value: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return path


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
