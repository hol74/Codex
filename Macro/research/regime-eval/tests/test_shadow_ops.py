from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.cli import main
from regime_eval.dataset import DatasetValidationError
from regime_eval.shadow_ops import (
    CSHARP_SOURCE_PATHS,
    REQUIRED_MACRO_SERIES,
    ensure_shadow_ledger,
    write_shadow_preflight,
)


class ShadowOperationsTests(unittest.TestCase):
    def test_preflight_cycle_retry_and_index_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = _source_tree(root / "source")
            dataset = _write(root / "dataset.json", _dataset())
            evaluation = _write(
                root / "evaluation.json", _evaluation(_sha(dataset), probability=0.2)
            )
            config = _write(root / "config.json", _config())
            preflight = root / "preflight.json"
            ledger = root / "ledgers" / "ledger-2026-06-30.json"
            index = root / "ledgers" / "shadow-index.json"

            self.assertEqual(0, main([
                "shadow-preflight",
                "--evaluation", str(evaluation),
                "--dataset", str(dataset),
                "--model-config", str(config),
                "--as-of", "2026-06-30",
                "--generated-at-utc", "2026-07-01T01:00:00Z",
                "--source-root", str(source_root),
                "--output", str(preflight),
            ]))
            prepared = json.loads(preflight.read_text(encoding="utf-8"))
            self.assertEqual("passed", prepared["status"])
            self.assertNotIn("actualOutcome", preflight.read_text(encoding="utf-8"))
            self.assertNotIn("actualRecession", preflight.read_text(encoding="utf-8"))
            self.assertEqual(64, len(prepared["implementation"]["csharpSourceSha256"]))
            self.assertEqual(64, len(prepared["implementation"]["pythonSourceSha256"]))

            self.assertEqual(0, main([
                "shadow-cycle",
                "--evaluation", str(evaluation),
                "--dataset", str(dataset),
                "--model-config", str(config),
                "--preflight", str(preflight),
                "--as-of", "2026-06-30",
                "--generated-at-utc", "2026-07-01T01:05:00Z",
                "--output", str(ledger),
                "--index", str(index),
            ]))
            frozen = ledger.read_bytes()
            frozen_index = index.read_bytes()
            ledger_payload = json.loads(frozen)
            self.assertEqual(_sha(preflight), ledger_payload["runManifest"]["inputs"]["preflightSha256"])
            self.assertNotIn(b"actualOutcome", frozen)
            self.assertEqual(1, json.loads(frozen_index)["entryCount"])

            recovered = ensure_shadow_ledger(
                evaluation, dataset, config, preflight, ["2026-06-30"],
                "2026-07-02T09:00:00Z", ledger,
            )
            self.assertEqual(ledger, recovered)
            self.assertEqual(frozen, ledger.read_bytes())
            self.assertEqual(0, main([
                "shadow-index", "--ledger-dir", str(ledger.parent), "--output", str(index)
            ]))
            self.assertEqual(frozen_index, index.read_bytes())

    def test_preflight_rejects_open_information_month(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, evaluation, config = _inputs(root)
            with self.assertRaisesRegex(DatasetValidationError, "not complete"):
                write_shadow_preflight(
                    evaluation, dataset, config, ["2026-06-30"],
                    "2026-06-30T23:59:59Z", _source_tree(root / "source"),
                    root / "preflight.json",
                )

    def test_preflight_rejects_stale_required_series(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _dataset()
            payload["rows"][0]["macroObservations"][0]["observationDate"] = "2026-02-01"
            dataset = _write(root / "dataset.json", payload)
            evaluation = _write(root / "evaluation.json", _evaluation(_sha(dataset)))
            config = _write(root / "config.json", _config())
            with self.assertRaisesRegex(DatasetValidationError, "stale macro series"):
                write_shadow_preflight(
                    evaluation, dataset, config, ["2026-06-30"],
                    "2026-07-01T01:00:00Z", _source_tree(root / "source"),
                    root / "preflight.json",
                )

    def test_retry_rejects_inputs_conflicting_with_frozen_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, evaluation, config = _inputs(root)
            preflight = write_shadow_preflight(
                evaluation, dataset, config, ["2026-06-30"],
                "2026-07-01T01:00:00Z", _source_tree(root / "source"),
                root / "preflight.json",
            )
            ledger = ensure_shadow_ledger(
                evaluation, dataset, config, preflight, ["2026-06-30"],
                "2026-07-01T01:05:00Z", root / "ledger.json",
            )
            changed = _write(
                root / "changed-evaluation.json", _evaluation(_sha(dataset), probability=0.3)
            )
            with self.assertRaisesRegex(DatasetValidationError, "conflicts"):
                ensure_shadow_ledger(
                    changed, dataset, config, preflight, ["2026-06-30"],
                    "2026-07-01T01:10:00Z", ledger,
                )


def _inputs(root: Path) -> tuple[Path, Path, Path]:
    dataset = _write(root / "dataset.json", _dataset())
    evaluation = _write(root / "evaluation.json", _evaluation(_sha(dataset)))
    config = _write(root / "config.json", _config())
    return dataset, evaluation, config


def _source_tree(root: Path) -> Path:
    for relative in CSHARP_SOURCE_PATHS:
        path = root / relative
        if path.suffix == ".cs":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"// {relative}\n", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / "Contract.cs").write_text(f"// {relative}\n", encoding="utf-8")
    return root


def _write(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dataset() -> dict[str, object]:
    as_of = "2026-06-30"
    return {
        "schemaVersion": 1,
        "from": as_of,
        "to": as_of,
        "forwardReturnHorizonsDays": [28],
        "rows": [{
            "asOfDate": as_of,
            "macroObservations": [{
                "seriesCode": code,
                "observationDate": "2026-05-01",
                "publicationDate": "2026-06-15",
                "vintageDate": "2026-06-15",
                "value": index + 1,
            } for index, code in enumerate(sorted(REQUIRED_MACRO_SERIES))],
            "marketObservations": [{
                "symbol": "SPY",
                "observationDate": as_of,
                "availabilityDate": as_of,
                "value": 100,
            }],
            "forwardReturns": [],
        }],
    }


def _evaluation(dataset_sha: str, probability: float = 0.2) -> dict[str, object]:
    remaining = (1.0 - probability) / 5
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelName": "Macro baseline",
        "modelVersion": "1.4-candidate",
        "rows": [{
            "asOfDate": "2026-06-30",
            "primaryRegime": "Goldilocks",
            "operationalRegime": "Goldilocks",
            "warnings": [],
            "probabilities": [{
                "regime": name,
                "probability": probability if name == "DeflationBust" else remaining,
            } for name in [
                "Goldilocks", "Reflation", "LateCycleOverheating", "Stagflation",
                "DeflationBust", "UncertainTransition",
            ]],
        }],
    }


def _config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "name": "baseline-v1-4-preregistered",
        "modelVersion": "1.4-candidate",
        "datasetSha256": "d" * 64,
    }


if __name__ == "__main__":
    unittest.main()
