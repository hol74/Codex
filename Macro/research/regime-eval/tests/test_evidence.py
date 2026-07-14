from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.evidence import write_model_evidence_report


class ModelEvidenceTests(unittest.TestCase):
    def test_reports_probability_calibration_temporal_errors_and_insufficient_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = _write(root / "dataset.json", _dataset())
            dataset_sha = hashlib.sha256(dataset.read_bytes()).hexdigest()
            evaluation = _write(root / "evaluation.json", _evaluation(dataset_sha))
            plan = _write(root / "plan.json", _plan())
            truth = _write(root / "truth.json", _truth())
            policy = _write(root / "policy.json", _policy(
                dataset_sha,
                hashlib.sha256(evaluation.read_bytes()).hexdigest(),
                hashlib.sha256(plan.read_bytes()).hexdigest(),
                hashlib.sha256(truth.read_bytes()).hexdigest(),
            ))

            first = write_model_evidence_report(
                evaluation, dataset, plan, truth, policy, root / "report.json"
            )
            second = write_model_evidence_report(
                evaluation, dataset, plan, truth, policy, root / "report-2.json"
            )
            report = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("INSUFFICIENT_EVIDENCE", report["promotionGate"]["status"])
            self.assertFalse(report["promotionGate"]["operationalPromotionAllowed"])
            self.assertEqual(1, report["coverage"]["positiveMonthCount"])
            self.assertEqual(1, report["temporalDiagnostics"]["maximumFalsePositiveRunMonths"])
            self.assertIn("brierScore", report["probabilityMetrics"])
            self.assertEqual(5, report["calibration"]["binCount"])
            self.assertEqual(100, report["uncertainty"]["replicates"])


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _dataset() -> dict[str, object]:
    dates = ["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30"]
    return {
        "schemaVersion": 1,
        "from": dates[0],
        "to": dates[-1],
        "forwardReturnHorizonsDays": [28],
        "rows": [{
            "asOfDate": value,
            "macroObservations": [{"observationDate": value, "publicationDate": value, "vintageDate": value, "value": 1}],
            "marketObservations": [{"symbol": "SPY", "observationDate": value, "availabilityDate": value, "value": 100}],
            "forwardReturns": [{"symbol": "SPY", "horizonDays": 28, "fromDate": value, "toDate": "2020-05-31", "startValue": 100, "endValue": 100, "returnValue": 0}],
        } for value in dates],
    }


def _evaluation(dataset_sha: str) -> dict[str, object]:
    dates = ["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30"]
    probabilities = [0.1, 0.8, 0.7, 0.2]
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelVersion": "test-v1",
        "rows": [{
            "asOfDate": value,
            "primaryRegime": "DeflationBust" if probability >= 0.5 else "Goldilocks",
            "operationalRegime": "DeflationBust" if probability >= 0.5 else "Goldilocks",
            "probabilities": [
                {"regime": "DeflationBust", "probability": probability},
                {"regime": "Goldilocks", "probability": 1 - probability},
            ],
        } for value, probability in zip(dates, probabilities)],
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
        "periods": [{"name": "test", "peakMonth": "2020-02-01", "firstRecessionMonth": "2020-03-01", "troughMonth": "2020-03-01"}],
    }


def _policy(dataset_sha: str, evaluation_sha: str, plan_sha: str, truth_sha: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "modelId": "test",
        "modelVersion": "test-v1",
        "currentLifecycle": "research-baseline",
        "benchmarkScope": "development-diagnostic-only",
        "expectedInputs": {
            "datasetSha256": dataset_sha,
            "evaluationSha256": evaluation_sha,
            "walkForwardPlanSha256": plan_sha,
            "groundTruthSha256": truth_sha,
        },
        "evidenceMinimums": {
            "outOfSampleRows": 10,
            "positiveMonths": 2,
            "positiveEpisodes": 2,
            "negativeMonths": 2,
        },
        "calibrationBins": 5,
        "bootstrap": {"replicates": 100, "blockMonths": 2, "seed": 42},
    }


if __name__ == "__main__":
    unittest.main()
