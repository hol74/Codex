from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.challenger import write_clustering_challenger_report
from regime_eval.cli import main
from regime_eval.hmm_challenger import write_hmm_challenger_report


class ClusteringChallengerTests(unittest.TestCase):
    def test_is_deterministic_and_test_labels_do_not_change_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = _write(root / "dataset.json", _dataset())
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = _write(root / "evaluation.json", _evaluation(dataset_sha))
            plan_path = _write(root / "plan.json", _plan())
            config_path = _write(root / "config.json", _config())
            truth_short = _write(root / "truth-short.json", _truth("2019-12-01"))
            truth_long = _write(root / "truth-long.json", _truth("2020-02-01"))

            first = write_clustering_challenger_report(
                evaluation_path, dataset_path, plan_path, truth_short, config_path, root / "first.json"
            )
            second = write_clustering_challenger_report(
                evaluation_path, dataset_path, plan_path, truth_short, config_path, root / "second.json"
            )
            changed_test_labels = write_clustering_challenger_report(
                evaluation_path, dataset_path, plan_path, truth_long, config_path, root / "changed.json"
            )

            first_report = json.loads(first.read_text(encoding="utf-8"))
            changed_report = json.loads(changed_test_labels.read_text(encoding="utf-8"))
            first_predictions = [item["predictedRecession"] for item in first_report["folds"][0]["predictions"]]
            changed_predictions = [item["predictedRecession"] for item in changed_report["folds"][0]["predictions"]]
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_predictions, changed_predictions)
            self.assertEqual([True, False], first_predictions)
            self.assertEqual(2, first_report["folds"][0]["trainRecessionCount"])
            self.assertTrue(first_report["folds"][0]["converged"])
            selected = first_report["folds"][0]["recessionCluster"]
            selected_summary = next(
                item for item in first_report["folds"][0]["clusterTrainingSummary"]
                if item["cluster"] == selected
            )
            self.assertGreater(selected_summary["recessionCount"], 0)

    def test_hmm_is_deterministic_causal_and_independent_of_test_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = _write(root / "dataset.json", _dataset())
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = _write(root / "evaluation.json", _evaluation(dataset_sha))
            evaluation_sha = hashlib.sha256(evaluation_path.read_bytes()).hexdigest()
            plan_path = _write(root / "plan.json", _plan())
            config_path = _write(root / "hmm-config.json", _hmm_config(evaluation_sha))
            truth_short = _write(root / "truth-short.json", _truth("2019-12-01"))
            truth_long = _write(root / "truth-long.json", _truth("2020-02-01"))

            first = write_hmm_challenger_report(
                evaluation_path, dataset_path, plan_path, truth_short, config_path, root / "hmm-first.json"
            )
            second = write_hmm_challenger_report(
                evaluation_path, dataset_path, plan_path, truth_short, config_path, root / "hmm-second.json"
            )
            changed = write_hmm_challenger_report(
                evaluation_path, dataset_path, plan_path, truth_long, config_path, root / "hmm-changed.json"
            )
            future_evaluation = _evaluation(dataset_sha)
            for feature in future_evaluation["rows"][-1]["featureScores"]:
                feature["normalizedScore"] = 0.01
            future_evaluation_path = _write(root / "evaluation-future.json", future_evaluation)
            future_sha = hashlib.sha256(future_evaluation_path.read_bytes()).hexdigest()
            future_config_path = _write(root / "hmm-config-future.json", _hmm_config(future_sha))
            future_changed = write_hmm_challenger_report(
                future_evaluation_path, dataset_path, plan_path, truth_short,
                future_config_path, root / "hmm-future-changed.json"
            )
            cli_output = root / "hmm-cli.json"
            self.assertEqual(0, main([
                "hmm-report",
                "--evaluation", str(evaluation_path),
                "--dataset", str(dataset_path),
                "--plan", str(plan_path),
                "--ground-truth", str(truth_short),
                "--config", str(config_path),
                "--output", str(cli_output),
            ]))

            first_report = json.loads(first.read_text(encoding="utf-8"))
            changed_report = json.loads(changed.read_text(encoding="utf-8"))
            future_report = json.loads(future_changed.read_text(encoding="utf-8"))
            first_predictions = [item["predictedRecession"] for item in first_report["folds"][0]["predictions"]]
            changed_predictions = [item["predictedRecession"] for item in changed_report["folds"][0]["predictions"]]
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.read_bytes(), cli_output.read_bytes())
            self.assertEqual(first_predictions, changed_predictions)
            self.assertEqual(
                first_report["folds"][0]["predictions"][0],
                future_report["folds"][0]["predictions"][0],
            )
            self.assertTrue(first_report["folds"][0]["converged"])
            self.assertEqual(2, len(first_report["folds"][0]["transitionMatrix"]))
            self.assertTrue(all(
                0.0 <= item["stateProbability"] <= 1.0
                for item in first_report["folds"][0]["predictions"]
            ))
            selected = first_report["folds"][0]["recessionState"]
            selected_summary = next(
                item for item in first_report["folds"][0]["stateTrainingSummary"]
                if item["state"] == selected
            )
            self.assertGreater(selected_summary["recessionCount"], 0)


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _dataset() -> dict[str, object]:
    dates = ["2019-09-30", "2019-10-31", "2019-11-30", "2019-12-31", "2020-01-31", "2020-02-29"]
    return {
        "schemaVersion": 1,
        "from": dates[0],
        "to": dates[-1],
        "forwardReturnHorizonsDays": [28],
        "rows": [_dataset_row(item) for item in dates],
    }


def _dataset_row(as_of: str) -> dict[str, object]:
    return {
        "asOfDate": as_of,
        "macroObservations": [{"observationDate": as_of, "publicationDate": as_of, "vintageDate": as_of, "value": 1}],
        "marketObservations": [{"symbol": "SPY", "observationDate": as_of, "availabilityDate": as_of, "value": 100}],
        "forwardReturns": [{"symbol": "SPY", "horizonDays": 28, "fromDate": as_of, "toDate": "2020-04-30", "startValue": 100, "endValue": 100, "returnValue": 0}],
    }


def _evaluation(dataset_sha: str) -> dict[str, object]:
    values = [0.8, 0.7, 0.1, 0.2, 0.15, 0.75]
    dates = ["2019-09-30", "2019-10-31", "2019-11-30", "2019-12-31", "2020-01-31", "2020-02-29"]
    codes = ["GROWTH_MOM", "INFL_PRESS", "RISK_APPETITE", "MONETARY_COND", "CREDIT_STRESS"]
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelVersion": "1.4-candidate",
        "rows": [
            {
                "asOfDate": as_of,
                "primaryRegime": "DeflationBust" if value < 0.3 else "Goldilocks",
                "operationalRegime": "DeflationBust" if value < 0.3 else "Goldilocks",
                "featureScores": [
                    {"featureCode": code, "normalizedScore": value} for code in codes
                ],
            }
            for as_of, value in zip(dates, values)
        ],
    }


def _plan() -> dict[str, object]:
    return {
        "foldCount": 1,
        "folds": [{
            "number": 1,
            "train_from": "2019-09-30",
            "train_to": "2019-12-31",
            "test_from": "2020-01-01",
            "test_to": "2020-02-29",
        }],
    }


def _config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "modelId": "test-kmeans",
        "role": "challenger",
        "featureCodes": ["GROWTH_MOM", "INFL_PRESS", "RISK_APPETITE", "MONETARY_COND", "CREDIT_STRESS"],
        "clusterCount": 2,
        "maxIterations": 20,
        "convergenceTolerance": 1e-10,
        "uniqueDateAggregation": "earliest fold prediction",
    }


def _hmm_config(evaluation_sha: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "modelId": "test-hmm",
        "modelFamily": "Gaussian HMM",
        "role": "challenger",
        "baselineModelVersion": "1.4-candidate",
        "baselineEvaluationSha256": evaluation_sha,
        "featureCodes": ["GROWTH_MOM", "INFL_PRESS", "RISK_APPETITE", "MONETARY_COND", "CREDIT_STRESS"],
        "stateCount": 2,
        "maxIterations": 100,
        "convergenceTolerance": 1e-6,
        "varianceFloor": 0.05,
        "transitionPseudoCount": 1.0,
        "labelSmoothing": 1.0,
        "testInference": "causal filtered posterior",
        "uniqueDateAggregation": "earliest eligible fold prediction wins",
        "promotionPolicy": {
            "minimumRecallDeltaVsBaselineOperational": 0.0,
            "minimumF1DeltaVsBaselineOperational": 0.0,
            "requireConvergenceEveryFold": True,
            "humanModelGateRequired": True,
        },
    }


def _truth(trough: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "groundTruthId": "test",
        "mappingPolicy": "month after peak through trough",
        "coverageFrom": "2019-09-01",
        "coverageTo": "2020-02-29",
        "limitations": ["test"],
        "periods": [{
            "name": "test recession",
            "peakMonth": "2019-10-01",
            "firstRecessionMonth": "2019-11-01",
            "troughMonth": trough,
        }],
    }


if __name__ == "__main__":
    unittest.main()
