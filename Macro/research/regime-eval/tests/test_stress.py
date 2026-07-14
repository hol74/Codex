from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.stress import write_stress_report


class StressReportTests(unittest.TestCase):
    def test_reports_multilabel_alignment_without_negative_class_accuracy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = root / "dataset.json"
            dataset_path.write_text(json.dumps(_dataset()), encoding="utf-8")
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = root / "evaluation.json"
            evaluation_path.write_text(json.dumps(_evaluation(dataset_sha)), encoding="utf-8")
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(_plan()), encoding="utf-8")
            stress_path = root / "stress.json"
            stress_path.write_text(json.dumps(_stress()), encoding="utf-8")
            recession_path = root / "recession.json"
            recession_path.write_text(json.dumps(_recession([])), encoding="utf-8")

            output = write_stress_report(
                evaluation_path,
                dataset_path,
                plan_path,
                stress_path,
                recession_path,
                root / "report.json",
            )
            repeated = write_stress_report(
                evaluation_path,
                dataset_path,
                plan_path,
                stress_path,
                recession_path,
                root / "report-repeat.json",
            )
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(output.read_bytes(), repeated.read_bytes())
            label = report["aggregateOutOfSample"]["labels"]["inflation_shock"]
            self.assertEqual(2, label["rowCount"])
            self.assertEqual(0.5, label["primaryExpectedRate"])
            self.assertEqual(0.5, label["operationalExpectedRate"])
            self.assertEqual(0.5, label["operationalUncertainRate"])
            self.assertEqual("not computed", report["alignmentPolicy"]["negativeClassMetrics"])

    def test_rejects_episode_that_overlaps_nber_recession(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = root / "dataset.json"
            dataset_path.write_text(json.dumps(_dataset()), encoding="utf-8")
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            paths = {
                "evaluation": root / "evaluation.json",
                "plan": root / "plan.json",
                "stress": root / "stress.json",
                "recession": root / "recession.json",
            }
            paths["evaluation"].write_text(json.dumps(_evaluation(dataset_sha)), encoding="utf-8")
            paths["plan"].write_text(json.dumps(_plan()), encoding="utf-8")
            paths["stress"].write_text(json.dumps(_stress()), encoding="utf-8")
            paths["recession"].write_text(
                json.dumps(_recession([{
                    "name": "test",
                    "peakMonth": "2020-01-01",
                    "firstRecessionMonth": "2020-02-01",
                    "troughMonth": "2020-02-01",
                }])),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(DatasetValidationError, "overlaps NBER recession month"):
                write_stress_report(
                    paths["evaluation"],
                    dataset_path,
                    paths["plan"],
                    paths["stress"],
                    paths["recession"],
                    root / "report.json",
                )


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
            {"asOfDate": "2020-02-29", "primaryRegime": "Stagflation", "operationalRegime": "UncertainTransition"},
            {"asOfDate": "2020-03-31", "primaryRegime": "Goldilocks", "operationalRegime": "Stagflation"},
            {"asOfDate": "2020-04-30", "primaryRegime": "Goldilocks", "operationalRegime": "Goldilocks"},
        ],
    }


def _plan() -> dict[str, object]:
    return {"foldCount": 1, "folds": [{"number": 1, "test_from": "2020-01-31", "test_to": "2020-04-30"}]}


def _stress() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "groundTruthId": "test-stress-v1",
        "evidenceStatus": "curated-ex-post",
        "scopePolicy": "non-recession months only",
        "coverageFrom": "2020-01-01",
        "coverageTo": "2020-12-31",
        "limitations": ["test"],
        "sources": [{"id": "source", "name": "test", "url": "https://example.test"}],
        "taxonomy": [{
            "code": "inflation_shock",
            "label": "Inflation shock",
            "expectedPrimaryRegimes": ["Stagflation", "LateCycleOverheating"],
        }],
        "episodes": [{
            "id": "episode",
            "name": "test episode",
            "firstMonth": "2020-02-01",
            "lastMonth": "2020-03-01",
            "labels": ["inflation_shock"],
            "sourceIds": ["source"],
            "boundaryRationale": "test boundary",
        }],
    }


def _recession(periods: list[dict[str, str]]) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "groundTruthId": "test-recession-v1",
        "mappingPolicy": "after peak through trough",
        "coverageFrom": "2020-01-01",
        "coverageTo": "2020-12-31",
        "limitations": ["test"],
        "periods": periods,
    }


if __name__ == "__main__":
    unittest.main()
