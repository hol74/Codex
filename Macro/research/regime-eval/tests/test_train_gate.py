from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from regime_eval.cli import main
from regime_eval.train_gate import write_baseline_train_gate


class BaselineTrainGateTests(unittest.TestCase):
    def test_uses_only_inner_validation_and_excludes_outer_test_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dates = ["2018-01-31", "2020-01-31", "2020-06-30", "2021-12-31", "2022-06-30"]
            dataset_path = root / "dataset.json"
            dataset_path.write_text(json.dumps(_dataset(dates)), encoding="utf-8")
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = root / "evaluation.json"
            evaluation_path.write_text(json.dumps(_evaluation(dataset_sha, dates)), encoding="utf-8")
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(_plan()), encoding="utf-8")
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(dataset_sha)), encoding="utf-8")

            output = write_baseline_train_gate(
                evaluation_path, dataset_path, plan_path, config_path, root / "gate.json"
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            fold = report["folds"][0]

            self.assertTrue(report["gate"]["eligibleForOuterOos"])
            self.assertEqual(3, fold["summary"]["rowCount"])
            self.assertEqual("2021-12-31", fold["innerValidationTo"])
            self.assertEqual(0, fold["outerTestRowCountUsed"])
            self.assertNotIn("DeflationBust", {
                item["regime"] for item in fold["summary"]["primaryRegimeDistribution"]
            })
            self.assertEqual(0, main([
                "baseline-train-gate",
                "--evaluation", str(evaluation_path),
                "--dataset", str(dataset_path),
                "--plan", str(plan_path),
                "--config", str(config_path),
                "--output", str(root / "gate-cli.json"),
            ]))

    def test_v2_separates_aggregate_integrity_and_coverage_from_fold_operations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dates = [
                "2018-01-31", "2020-01-31", "2020-06-30", "2021-12-31",
                "2022-06-30", "2022-12-31", "2023-06-30",
            ]
            regimes = [
                "Goldilocks", "Goldilocks", "Reflation", "Goldilocks",
                "Stagflation", "Goldilocks", "DeflationBust",
            ]
            dataset_path = root / "dataset.json"
            dataset_path.write_text(json.dumps(_dataset(dates)), encoding="utf-8")
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = root / "evaluation.json"
            evaluation_path.write_text(
                json.dumps(_evaluation(dataset_sha, dates, regimes)), encoding="utf-8"
            )
            evaluation_sha = hashlib.sha256(evaluation_path.read_bytes()).hexdigest()
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(_plan_v2()), encoding="utf-8")
            config_path = root / "config-v2.json"
            config_path.write_text(
                json.dumps(_config_v2(dataset_sha, evaluation_sha)), encoding="utf-8"
            )

            output = write_baseline_train_gate(
                evaluation_path, dataset_path, plan_path, config_path, root / "gate-v2.json"
            )
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(2, report["reportVersion"])
            self.assertTrue(report["gate"]["eligibleForOuterOos"])
            self.assertTrue(report["gate"]["featureIntegrity"]["passed"])
            self.assertTrue(report["gate"]["regimeCoverage"]["passed"])
            self.assertEqual(2, report["gate"]["operationalRobustness"]["passingFoldCount"])
            self.assertEqual(3, report["aggregateUniqueInnerValidation"]["primaryRegimeCount"])
            self.assertEqual(5, report["aggregateUniqueInnerValidation"]["rowCount"])
            self.assertTrue(all(
                fold["summary"]["primaryRegimeCount"] < 3 for fold in report["folds"]
            ))
            self.assertNotIn("DeflationBust", {
                item["regime"]
                for item in report["aggregateUniqueInnerValidation"]["primaryRegimeDistribution"]
            })

            saturated = json.loads(evaluation_path.read_text(encoding="utf-8"))
            for row in saturated["rows"]:
                if row["asOfDate"] in {"2020-01-31", "2020-06-30"}:
                    row["featureScores"][0]["normalizedScore"] = 1.0
            evaluation_path.write_text(json.dumps(saturated), encoding="utf-8")
            saturated_sha = hashlib.sha256(evaluation_path.read_bytes()).hexdigest()
            config_path.write_text(
                json.dumps(_config_v2(dataset_sha, saturated_sha)), encoding="utf-8"
            )
            failed_output = write_baseline_train_gate(
                evaluation_path, dataset_path, plan_path, config_path, root / "gate-v2-failed.json"
            )
            failed = json.loads(failed_output.read_text(encoding="utf-8"))
            self.assertFalse(failed["gate"]["eligibleForOuterOos"])
            self.assertFalse(failed["gate"]["featureIntegrity"]["passed"])
            self.assertTrue(failed["gate"]["regimeCoverage"]["passed"])
            self.assertTrue(failed["gate"]["operationalRobustness"]["passed"])


def _dataset(dates: list[str]) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "from": dates[0],
        "to": dates[-1],
        "forwardReturnHorizonsDays": [28],
        "rows": [_dataset_row(value) for value in dates],
    }


def _dataset_row(as_of: str) -> dict[str, object]:
    to_date = (date.fromisoformat(as_of) + timedelta(days=28)).isoformat()
    return {
        "asOfDate": as_of,
        "macroObservations": [{
            "observationDate": as_of, "publicationDate": as_of,
            "vintageDate": as_of, "value": 1,
        }],
        "marketObservations": [{
            "symbol": "SPY", "observationDate": as_of,
            "availabilityDate": as_of, "value": 100,
        }],
        "forwardReturns": [{
            "symbol": "SPY", "horizonDays": 28, "fromDate": as_of,
            "toDate": to_date, "startValue": 100, "endValue": 101, "returnValue": 0.01,
        }],
    }


def _evaluation(
    dataset_sha: str, dates: list[str], regimes: list[str] | None = None
) -> dict[str, object]:
    regimes = regimes or ["Goldilocks", "Goldilocks", "Reflation", "Stagflation", "DeflationBust"]
    rows = []
    for as_of, regime in zip(dates, regimes):
        rows.append({
            "asOfDate": as_of,
            "primaryRegime": regime,
            "operationalRegime": regime,
            "confidence": 0.7,
            "warnings": [],
            "featureScores": [{"featureCode": "GROWTH_MOM", "normalizedScore": 0.5}],
            "probabilities": [
                {"regime": regime, "probability": 0.6},
                {"regime": "UncertainTransition", "probability": 0.2},
            ],
        })
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelName": "Baseline",
        "modelVersion": "1.2-candidate",
        "modelEffectiveFrom": "2026-07-13",
        "featureSetName": "Features",
        "featureSetVersion": "1.2-candidate",
        "confirmationThreshold": 0.55,
        "rows": rows,
    }


def _plan() -> dict[str, object]:
    return {"foldCount": 1, "folds": [{
        "number": 1,
        "train_from": "2018-01-01", "train_to": "2021-12-31",
        "test_from": "2022-01-01", "test_to": "2022-12-31",
    }]}


def _plan_v2() -> dict[str, object]:
    return {"foldCount": 2, "folds": [
        {
            "number": 1,
            "train_from": "2018-01-01", "train_to": "2021-12-31",
            "test_from": "2022-01-01", "test_to": "2022-12-31",
        },
        {
            "number": 2,
            "train_from": "2019-01-01", "train_to": "2022-12-31",
            "test_from": "2023-01-01", "test_to": "2023-12-31",
        },
    ]}


def _config(dataset_sha: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "modelVersion": "1.2-candidate",
        "datasetSha256": dataset_sha,
        "innerValidationYears": 2,
        "minimumEligibleFoldCount": 1,
        "expectedFeatureCodes": ["GROWTH_MOM"],
        "featureBoundaryFloor": 0.05,
        "featureBoundaryCeiling": 0.95,
        "maxFeatureBoundaryRate": 0.25,
        "minPrimaryRegimeCount": 3,
        "maxDominantPrimaryRegimeRate": 0.80,
        "maxUncertainTransitionRate": 0.50,
    }


def _config_v2(dataset_sha: str, evaluation_sha: str) -> dict[str, object]:
    config = _config(dataset_sha)
    config.pop("minimumEligibleFoldCount")
    config.update({
        "gateVersion": 2,
        "evaluationSha256": evaluation_sha,
        "minimumOperationalFoldCount": 2,
        "aggregateDatePolicy": "Union of inner-validation dates; each as-of date is counted once.",
        "featureIntegrityScope": "aggregateUniqueInnerValidation",
        "coverageScope": "aggregateUniqueInnerValidation",
        "operationalScope": "perFold",
    })
    return config


if __name__ == "__main__":
    unittest.main()
