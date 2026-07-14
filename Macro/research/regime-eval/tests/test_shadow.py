from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.cli import main
from regime_eval.dataset import DatasetValidationError
from regime_eval.shadow import (
    write_baseline_prediction_ledger,
    write_gate_decision,
    write_shadow_score,
)


class ShadowLedgerTests(unittest.TestCase):
    def test_prediction_is_immutable_label_free_and_scored_separately(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = _write(root / "dataset.json", _dataset())
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = _write(root / "evaluation.json", _evaluation(dataset_sha))
            config_path = _write(root / "config.json", _config("d" * 64))
            truth_path = _write(root / "truth.json", _truth())
            ledger_path = root / "ledger.json"

            ledger = write_baseline_prediction_ledger(
                evaluation_path,
                dataset_path,
                config_path,
                ["2020-03-31", "2020-04-30"],
                "2026-07-13T12:00:00Z",
                "dry-run",
                ledger_path,
            )
            frozen = ledger.read_bytes()
            payload = json.loads(frozen)
            self.assertEqual("predicted", payload["lifecycleStatus"])
            self.assertEqual(2, payload["predictionCount"])
            self.assertEqual("d" * 64, payload["model"]["developmentDatasetSha256"])
            self.assertEqual(dataset_sha, payload["runManifest"]["inputs"]["datasetSha256"])
            self.assertNotIn(b"actualRecession", frozen)
            self.assertEqual(0.7, payload["predictions"][0]["recessionProbability"])
            self.assertEqual(64, len(payload["runManifest"]["implementation"]["sourceSha256"]))

            score = write_shadow_score(
                ledger, truth_path, "2026-07-13T12:05:00Z", root / "score.json"
            )
            score_payload = json.loads(score.read_text(encoding="utf-8"))
            self.assertEqual(frozen, ledger.read_bytes())
            self.assertEqual(hashlib.sha256(frozen).hexdigest(), score_payload["predictionLedger"]["sha256"])
            self.assertEqual(0.5, score_payload["metrics"]["recall"])
            self.assertIn("brierScore", score_payload["probabilityMetrics"])

            with self.assertRaises(DatasetValidationError):
                write_baseline_prediction_ledger(
                    evaluation_path,
                    dataset_path,
                    config_path,
                    ["2020-03-31", "2020-04-30"],
                    "2026-07-13T12:00:00Z",
                    "dry-run",
                    ledger_path,
                )

            cli_ledger = root / "cli-ledger.json"
            self.assertEqual(0, main([
                "shadow-predict",
                "--evaluation", str(evaluation_path),
                "--dataset", str(dataset_path),
                "--model-config", str(config_path),
                "--as-of", "2020-03-31",
                "--as-of", "2020-04-30",
                "--generated-at-utc", "2026-07-13T12:00:00Z",
                "--run-mode", "dry-run",
                "--output", str(cli_ledger),
            ]))
            self.assertEqual(frozen, cli_ledger.read_bytes())
            self.assertEqual(0, main([
                "shadow-score",
                "--ledger", str(cli_ledger),
                "--ground-truth", str(truth_path),
                "--scored-at-utc", "2026-07-13T12:05:00Z",
                "--output", str(root / "cli-score.json"),
            ]))

    def test_gate_decision_cannot_approve_failed_automatic_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = _write(root / "report.json", {
                "reportVersion": 1,
                "challenger": {"modelId": "gaussian-hmm-recession-v1"},
                "modelGate": {
                    "passedAutomaticMetrics": False,
                    "humanReviewRequired": True,
                    "violations": ["RECALL_REGRESSION"],
                },
            })
            with self.assertRaises(DatasetValidationError):
                write_gate_decision(
                    report,
                    "approved",
                    "research-owner",
                    "override",
                    "2026-07-13T12:10:00Z",
                    root / "invalid.json",
                )
            decision = write_gate_decision(
                report,
                "rejected",
                "research-owner",
                "Automatic recall gate failed.",
                "2026-07-13T12:10:00Z",
                root / "decision.json",
            )
            payload = json.loads(decision.read_text(encoding="utf-8"))
            self.assertEqual("rejected", payload["model"]["lifecycleStatus"])
            self.assertEqual(hashlib.sha256(report.read_bytes()).hexdigest(), payload["sourceReport"]["sha256"])
            self.assertEqual(0, main([
                "gate-decision",
                "--report", str(report),
                "--decision", "rejected",
                "--reviewer", "research-owner",
                "--rationale", "Automatic recall gate failed.",
                "--decided-at-utc", "2026-07-13T12:10:00Z",
                "--output", str(root / "cli-decision.json"),
            ]))


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _dataset() -> dict[str, object]:
    dates = ["2020-03-31", "2020-04-30"]
    return {
        "schemaVersion": 1,
        "from": dates[0],
        "to": dates[-1],
        "forwardReturnHorizonsDays": [28],
        "rows": [
            {
                "asOfDate": value,
                "macroObservations": [{
                    "observationDate": value,
                    "publicationDate": value,
                    "vintageDate": value,
                    "value": 1,
                }],
                "marketObservations": [{
                    "symbol": "SPY",
                    "observationDate": value,
                    "availabilityDate": value,
                    "value": 100,
                }],
                "forwardReturns": [{
                    "symbol": "SPY",
                    "horizonDays": 28,
                    "fromDate": value,
                    "toDate": "2020-05-31" if value == dates[0] else "2020-06-30",
                    "startValue": 100,
                    "endValue": 100,
                    "returnValue": 0,
                }],
            }
            for value in dates
        ],
    }


def _evaluation(dataset_sha: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelName": "Macro baseline",
        "modelVersion": "1.4-candidate",
        "rows": [
            _evaluation_row("2020-03-31", "UncertainTransition", 0.7),
            _evaluation_row("2020-04-30", "DeflationBust", 0.8),
        ],
    }


def _evaluation_row(as_of: str, operational: str, recession_probability: float) -> dict[str, object]:
    remaining = round((1.0 - recession_probability) / 5, 10)
    return {
        "asOfDate": as_of,
        "primaryRegime": "DeflationBust",
        "operationalRegime": operational,
        "warnings": [],
        "probabilities": [
            {"regime": name, "probability": recession_probability if name == "DeflationBust" else remaining}
            for name in [
                "Goldilocks", "Reflation", "LateCycleOverheating", "Stagflation",
                "DeflationBust", "UncertainTransition",
            ]
        ],
    }


def _config(dataset_sha: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "name": "baseline-v1-4-preregistered",
        "modelVersion": "1.4-candidate",
        "datasetSha256": dataset_sha,
    }


def _truth() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "groundTruthId": "test-recession-v1",
        "mappingPolicy": "month after peak through trough",
        "coverageFrom": "2020-03-01",
        "coverageTo": "2020-04-30",
        "limitations": ["test"],
        "periods": [{
            "name": "test",
            "peakMonth": "2020-02-01",
            "firstRecessionMonth": "2020-03-01",
            "troughMonth": "2020-04-01",
        }],
    }


if __name__ == "__main__":
    unittest.main()
