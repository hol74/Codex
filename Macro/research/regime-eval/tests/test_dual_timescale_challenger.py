from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dual_timescale_challenger import write_dual_timescale_report


class DualTimescaleChallengerTests(unittest.TestCase):
    def test_is_deterministic_label_independent_causal_and_development_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = _write(root / "dataset.json", _dataset())
            evaluation = _write(root / "evaluation.json", _evaluation(_sha(dataset)))
            plan = _write(root / "plan.json", _plan())
            stress = _write(root / "stress.json", _stress())
            truth_short = _write(root / "truth-short.json", _truth("2020-06-01"))
            config_short = _write(
                root / "config-short.json",
                _config(_sha(dataset), _sha(evaluation), _sha(plan), _sha(truth_short), _sha(stress)),
            )
            first = write_dual_timescale_report(
                evaluation, dataset, plan, truth_short, stress, config_short, root / "first.json"
            )
            repeated = write_dual_timescale_report(
                evaluation, dataset, plan, truth_short, stress, config_short, root / "repeated.json"
            )

            truth_long = _write(root / "truth-long.json", _truth("2020-07-01"))
            config_long = _write(
                root / "config-long.json",
                _config(_sha(dataset), _sha(evaluation), _sha(plan), _sha(truth_long), _sha(stress)),
            )
            changed_labels = write_dual_timescale_report(
                evaluation, dataset, plan, truth_long, stress, config_long, root / "changed-labels.json"
            )

            future_value = _evaluation(_sha(dataset))
            for feature in future_value["rows"][-1]["featureScores"]:
                feature["normalizedScore"] = 0.01
            future_evaluation = _write(root / "future-evaluation.json", future_value)
            future_config = _write(
                root / "future-config.json",
                _config(_sha(dataset), _sha(future_evaluation), _sha(plan), _sha(truth_short), _sha(stress)),
            )
            changed_future = write_dual_timescale_report(
                future_evaluation, dataset, plan, truth_short, stress, future_config, root / "changed-future.json"
            )

            first_report = json.loads(first.read_text(encoding="utf-8"))
            label_report = json.loads(changed_labels.read_text(encoding="utf-8"))
            future_report = json.loads(changed_future.read_text(encoding="utf-8"))
            first_predictions = first_report["uniqueOutOfSample"]["predictions"]
            label_predictions = label_report["uniqueOutOfSample"]["predictions"]

            self.assertEqual(first.read_bytes(), repeated.read_bytes())
            self.assertEqual(
                [item["predictedRecession"] for item in first_predictions],
                [item["predictedRecession"] for item in label_predictions],
            )
            self.assertEqual(first_predictions[0]["recessionProbability"], future_report["uniqueOutOfSample"]["predictions"][0]["recessionProbability"])
            self.assertEqual("DEVELOPMENT_DIAGNOSTIC_ONLY", first_report["modelGate"]["status"])
            self.assertFalse(first_report["modelGate"]["passedAutomaticMetrics"])
            self.assertIn("protected-v2", first_report["stressDiagnostics"]["partitions"])


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dates() -> list[str]:
    return ["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30", "2020-05-31", "2020-06-30", "2020-07-31", "2020-08-31"]


def _dataset() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "from": _dates()[0],
        "to": _dates()[-1],
        "forwardReturnHorizonsDays": [28],
        "rows": [{
            "asOfDate": value,
            "macroObservations": [{"observationDate": value, "publicationDate": value, "vintageDate": value, "value": 1}],
            "marketObservations": [{"symbol": "SPY", "observationDate": value, "availabilityDate": value, "value": 100}],
            "forwardReturns": [{"symbol": "SPY", "horizonDays": 28, "fromDate": value, "toDate": "2020-09-30", "startValue": 100, "endValue": 100, "returnValue": 0}],
        } for value in _dates()],
    }


def _evaluation(dataset_sha: str) -> dict[str, object]:
    growth = [0.8, 0.7, 0.6, 0.5, 0.25, 0.15, 0.3, 0.7]
    risk = [0.8, 0.7, 0.6, 0.5, 0.2, 0.1, 0.3, 0.8]
    rows = []
    for value, growth_value, risk_value in zip(_dates(), growth, risk):
        rows.append({
            "asOfDate": value,
            "primaryRegime": "DeflationBust" if growth_value < 0.3 else "Goldilocks",
            "operationalRegime": "DeflationBust" if growth_value < 0.3 else "Goldilocks",
            "featureScores": [
                {"featureCode": "GROWTH_MOM", "normalizedScore": growth_value},
                {"featureCode": "INFL_PRESS", "normalizedScore": 0.4},
                {"featureCode": "RISK_APPETITE", "normalizedScore": risk_value},
                {"featureCode": "MONETARY_COND", "normalizedScore": 0.4},
                {"featureCode": "CREDIT_STRESS", "normalizedScore": risk_value},
            ],
        })
    return {"schemaVersion": 1, "datasetSha256": dataset_sha, "modelVersion": "test-v1", "rows": rows}


def _plan() -> dict[str, object]:
    return {"foldCount": 1, "folds": [{"number": 1, "train_from": "2020-01-31", "train_to": "2020-04-30", "test_from": "2020-05-01", "test_to": "2020-08-31"}]}


def _truth(trough: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "groundTruthId": "test-recession",
        "mappingPolicy": "after peak through trough",
        "coverageFrom": "2020-01-01",
        "coverageTo": "2020-12-31",
        "limitations": ["test"],
        "periods": [{"name": "test", "peakMonth": "2020-04-01", "firstRecessionMonth": "2020-05-01", "troughMonth": trough}],
    }


def _stress() -> dict[str, object]:
    return {
        "schemaVersion": 2,
        "groundTruthId": "test-stress",
        "evidenceStatus": "test",
        "scopePolicy": "test",
        "coverageFrom": "2020-01-01",
        "coverageTo": "2020-12-31",
        "limitations": ["test"],
        "sources": [{"id": "source"}],
        "taxonomy": [{
            "code": "financial_stress",
            "label": "Financial stress",
            "expectedPrimaryRegimes": ["DeflationBust"],
            "expectedDimensions": {"financialStress": {"minimum": 0.55}},
        }],
        "episodes": [{
            "id": "episode",
            "name": "protected test",
            "firstMonth": "2020-08-01",
            "lastMonth": "2020-08-01",
            "labels": ["financial_stress"],
            "sourceIds": ["source"],
            "validationRole": "protected-v2",
            "boundaryRationale": "test",
        }],
    }


def _config(dataset: str, evaluation: str, plan: str, recession: str, stress: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "role": "challenger",
        "modelId": "test-dual",
        "modelFamily": "test",
        "benchmarkScope": "development-diagnostic-only",
        "baselineModelVersion": "test-v1",
        "expectedInputs": {
            "datasetSha256": dataset,
            "baselineEvaluationSha256": evaluation,
            "walkForwardPlanSha256": plan,
            "recessionGroundTruthSha256": recession,
            "stressGroundTruthSha256": stress,
        },
        "featureCodes": ["GROWTH_MOM", "INFL_PRESS", "RISK_APPETITE", "MONETARY_COND", "CREDIT_STRESS"],
        "dimensionFormulaVersion": "macro-financial-dimensions-v1",
        "slowComponent": {"growthWeight": 0.75, "monetaryWeight": 0.25, "causalEwmaAlpha": 0.25},
        "fastComponent": {"causalEwmaAlpha": 0.65},
        "recessionProbability": {"entryThreshold": 0.55, "exitThreshold": 0.45},
        "uniqueDateAggregation": "earliest eligible fold prediction wins",
    }


if __name__ == "__main__":
    unittest.main()
