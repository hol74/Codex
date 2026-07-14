from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.ground_truth import write_recession_report


class RecessionReportTests(unittest.TestCase):
    def test_scores_primary_and_operational_signals_against_monthly_truth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = root / "dataset.json"
            dataset_path.write_text(json.dumps(_dataset()), encoding="utf-8")
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = root / "evaluation.json"
            evaluation_path.write_text(json.dumps(_evaluation(dataset_sha)), encoding="utf-8")
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(_plan()), encoding="utf-8")
            truth_path = root / "truth.json"
            truth_path.write_text(json.dumps(_truth()), encoding="utf-8")

            output = write_recession_report(
                evaluation_path, dataset_path, plan_path, truth_path, root / "report.json"
            )
            report = json.loads(output.read_text(encoding="utf-8"))

            primary = report["aggregateOutOfSample"]["primaryDeflationBust"]
            operational = report["aggregateOutOfSample"]["operationalDeflationBust"]
            self.assertEqual({"truePositive": 1, "falsePositive": 1, "trueNegative": 1, "falseNegative": 1}, primary["confusionMatrix"])
            self.assertEqual(0.5, primary["recall"])
            self.assertEqual(0.5, primary["precision"])
            self.assertEqual(0, operational["confusionMatrix"]["truePositive"])
            self.assertEqual(1.0, report["aggregateOutOfSample"]["uncertainDuringRecessionRate"])
            self.assertEqual(1, report["aggregateOutOfSample"]["episodeDiagnostics"][0]["primaryDetectionLagMonths"])


def _dataset() -> dict[str, object]:
    dates = ["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30"]
    return {
        "schemaVersion": 1,
        "from": dates[0],
        "to": dates[-1],
        "forwardReturnHorizonsDays": [28],
        "rows": [_row(item) for item in dates],
    }


def _row(as_of: str) -> dict[str, object]:
    return {
        "asOfDate": as_of,
        "macroObservations": [{"observationDate": as_of, "publicationDate": as_of, "vintageDate": as_of, "value": 1}],
        "marketObservations": [{"symbol": "SPY", "observationDate": as_of, "availabilityDate": as_of, "value": 100}],
        "forwardReturns": [{"symbol": "SPY", "horizonDays": 28, "fromDate": as_of, "toDate": "2020-05-31", "startValue": 100, "endValue": 100, "returnValue": 0}],
    }


def _evaluation(dataset_sha: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "rows": [
            {"asOfDate": "2020-01-31", "primaryRegime": "Goldilocks", "operationalRegime": "Goldilocks"},
            {"asOfDate": "2020-02-29", "primaryRegime": "DeflationBust", "operationalRegime": "Goldilocks"},
            {"asOfDate": "2020-03-31", "primaryRegime": "Goldilocks", "operationalRegime": "UncertainTransition"},
            {"asOfDate": "2020-04-30", "primaryRegime": "DeflationBust", "operationalRegime": "UncertainTransition"},
        ],
    }


def _plan() -> dict[str, object]:
    return {"foldCount": 1, "folds": [{"number": 1, "test_from": "2020-01-31", "test_to": "2020-04-30"}]}


def _truth() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "groundTruthId": "test",
        "mappingPolicy": "after peak through trough",
        "coverageFrom": "2020-01-01",
        "coverageTo": "2020-12-31",
        "limitations": ["test"],
        "periods": [{"name": "test recession", "peakMonth": "2020-02-01", "firstRecessionMonth": "2020-03-01", "troughMonth": "2020-04-01"}],
    }


if __name__ == "__main__":
    unittest.main()
