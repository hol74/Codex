from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.baseline import write_baseline_report


class BaselineReportTests(unittest.TestCase):
    def test_writes_deterministic_fold_and_unique_out_of_sample_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = root / "dataset.json"
            dataset_path.write_text(json.dumps(_dataset()), encoding="utf-8")
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = root / "evaluation.json"
            evaluation_path.write_text(json.dumps(_evaluation(dataset_sha)), encoding="utf-8")
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(_plan()), encoding="utf-8")

            output = write_baseline_report(evaluation_path, dataset_path, plan_path, root / "report.json")
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(2, report["coverage"]["uniqueOutOfSampleRowCount"])
            self.assertEqual(2, report["folds"][0]["rowCount"])
            self.assertEqual(0.5, report["aggregateOutOfSample"]["uncertainTransitionRate"])
            self.assertEqual(1.0, report["aggregateOutOfSample"]["operationalTransitionRate"])
            self.assertEqual(0.15, report["aggregateOutOfSample"]["assetForwardReturns"][0]["meanReturn"])
            self.assertEqual(
                "not computed: no versioned external regime ground truth is included yet",
                report["methodology"]["accuracyStatus"],
            )
            self.assertIn("retrospective", report["methodology"]["historicalStatus"])


def _dataset() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "from": "2020-01-31",
        "to": "2020-02-29",
        "forwardReturnHorizonsDays": [28],
        "rows": [_row("2020-01-31", 0.1), _row("2020-02-29", 0.2)],
    }


def _row(as_of: str, return_value: float) -> dict[str, object]:
    return {
        "asOfDate": as_of,
        "macroObservations": [{
            "observationDate": as_of,
            "publicationDate": as_of,
            "vintageDate": as_of,
            "value": 1,
        }],
        "marketObservations": [{
            "symbol": "SPY",
            "observationDate": as_of,
            "availabilityDate": as_of,
            "value": 100,
        }],
        "forwardReturns": [{
            "symbol": "SPY",
            "horizonDays": 28,
            "fromDate": as_of,
            "toDate": "2020-03-31" if as_of == "2020-01-31" else "2020-04-30",
            "startValue": 100,
            "endValue": 100 * (1 + return_value),
            "returnValue": return_value,
        }],
    }


def _evaluation(dataset_sha: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelName": "Baseline",
        "modelVersion": "1",
        "modelEffectiveFrom": "2026-07-01",
        "featureSetName": "Features",
        "featureSetVersion": "1",
        "confirmationThreshold": 0.55,
        "rows": [
            {"asOfDate": "2020-01-31", "primaryRegime": "Goldilocks", "operationalRegime": "Goldilocks", "confidence": 0.7, "warnings": []},
            {"asOfDate": "2020-02-29", "primaryRegime": "DeflationBust", "operationalRegime": "UncertainTransition", "confidence": 0.4, "warnings": []},
        ],
    }


def _plan() -> dict[str, object]:
    return {
        "foldCount": 1,
        "folds": [{
            "number": 1,
            "train_from": "2010-01-31",
            "train_to": "2020-01-30",
            "test_from": "2020-01-31",
            "test_to": "2020-02-29",
        }],
    }


if __name__ == "__main__":
    unittest.main()
