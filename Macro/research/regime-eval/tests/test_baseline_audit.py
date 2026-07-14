from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.baseline_audit import write_baseline_audit
from regime_eval.cli import main


class BaselineAuditTests(unittest.TestCase):
    def test_reports_saturation_and_regime_concentration_without_hiding_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = root / "dataset.json"
            dataset_path.write_text(json.dumps(_dataset()), encoding="utf-8")
            dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
            evaluation_path = root / "evaluation.json"
            evaluation_path.write_text(json.dumps(_evaluation(dataset_sha)), encoding="utf-8")
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(_plan()), encoding="utf-8")
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config()), encoding="utf-8")

            output = write_baseline_audit(
                evaluation_path, dataset_path, plan_path, config_path, root / "audit.json"
            )
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertFalse(report["gate"]["passed"])
            self.assertEqual(2, report["uniqueOutOfSample"]["rowCount"])
            feature = report["uniqueOutOfSample"]["featureDiagnostics"][0]
            self.assertEqual("CREDIT_STRESS", feature["featureCode"])
            self.assertEqual(1.0, feature["ceilingRate"])
            codes = {item["code"] for item in report["gate"]["violations"]}
            self.assertIn("FEATURE_BOUNDARY_SATURATION", codes)
            self.assertIn("INSUFFICIENT_PRIMARY_REGIME_DIVERSITY", codes)
            self.assertIn("DOMINANT_PRIMARY_REGIME", codes)

            exit_code = main([
                "baseline-audit",
                "--evaluation", str(evaluation_path),
                "--dataset", str(dataset_path),
                "--plan", str(plan_path),
                "--config", str(config_path),
                "--output", str(root / "audit-cli.json"),
            ])
            self.assertEqual(3, exit_code)


def _dataset() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "from": "2020-01-31",
        "to": "2020-02-29",
        "forwardReturnHorizonsDays": [28],
        "rows": [_row("2020-01-31"), _row("2020-02-29")],
    }


def _row(as_of: str) -> dict[str, object]:
    return {
        "asOfDate": as_of,
        "macroObservations": [{"observationDate": as_of, "publicationDate": as_of, "vintageDate": as_of, "value": 1}],
        "marketObservations": [{"symbol": "SPY", "observationDate": as_of, "availabilityDate": as_of, "value": 100}],
        "forwardReturns": [{"symbol": "SPY", "horizonDays": 28, "fromDate": as_of, "toDate": "2020-03-31", "startValue": 100, "endValue": 101, "returnValue": 0.01}],
    }


def _evaluation(dataset_sha: str) -> dict[str, object]:
    rows = []
    for as_of in ("2020-01-31", "2020-02-29"):
        rows.append({
            "asOfDate": as_of,
            "primaryRegime": "Goldilocks",
            "operationalRegime": "Goldilocks",
            "confidence": 0.7,
            "warnings": [],
            "featureScores": [{"featureCode": "CREDIT_STRESS", "normalizedScore": 1.0}],
            "probabilities": [{"regime": "Goldilocks", "probability": 0.6}, {"regime": "Reflation", "probability": 0.2}],
        })
    return {
        "schemaVersion": 1,
        "datasetSha256": dataset_sha,
        "modelName": "Baseline",
        "modelVersion": "0.1-demo",
        "modelEffectiveFrom": "2026-07-01",
        "featureSetName": "Features",
        "featureSetVersion": "0.1",
        "confirmationThreshold": 0.55,
        "rows": rows,
    }


def _plan() -> dict[str, object]:
    return {"foldCount": 1, "folds": [{"test_from": "2020-01-01", "test_to": "2020-12-31"}]}


def _config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "expectedFeatureCodes": ["CREDIT_STRESS"],
        "featureBoundaryFloor": 0.05,
        "featureBoundaryCeiling": 0.95,
        "maxFeatureBoundaryRate": 0.25,
        "minPrimaryRegimeCount": 3,
        "maxDominantPrimaryRegimeRate": 0.80,
        "maxUncertainTransitionRate": 0.50,
    }


if __name__ == "__main__":
    unittest.main()
