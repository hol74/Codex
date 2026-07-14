from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dimensional_baseline import archetype_scenarios, dimensional_prediction, write_dimensional_baseline_gate
from regime_eval.dataset import DatasetValidationError


ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "research" / "regime-eval"


class DimensionalBaselineTests(unittest.TestCase):
    def test_archetypes_and_causal_impulses_follow_frozen_formulas(self) -> None:
        candidate = json.loads((LAB / "models" / "baseline-v1-5-dimensional.json").read_text())
        geometry = json.loads((LAB / "models" / "baseline-v1-4-preregistered.json").read_text())
        self.assertTrue(all(item["passed"] for item in archetype_scenarios(candidate, geometry)))

        previous = _row("2020-01-31", growth=0.8, risk=0.8, credit=0.8)
        shock = _row("2020-02-29", growth=0.4, risk=0.2, credit=0.2)
        prediction = dimensional_prediction(shock, previous, candidate, geometry)
        adjusted = {item["featureCode"]: item["normalizedScore"] for item in prediction["adjustedFeatureScores"]}
        self.assertGreater(prediction["financialStressImpulse"], 0)
        self.assertGreater(prediction["growthDeteriorationImpulse"], 0)
        self.assertLess(adjusted["RISK_APPETITE"], 0.2)
        self.assertLess(adjusted["GROWTH_MOM"], 0.4)

        changed_future = _row("2020-03-31", growth=1.0, risk=1.0, credit=1.0)
        before = dimensional_prediction(shock, previous, candidate, geometry)
        dimensional_prediction(changed_future, shock, candidate, geometry)
        after = dimensional_prediction(shock, previous, candidate, geometry)
        self.assertEqual(before, after)

    def test_real_gate_is_deterministic_and_never_uses_outer_test_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            arguments = (
                ROOT / "data/historical-real-v11-2008-2025/baseline/baseline-evaluation-2008-04-01-2025-12-31-v1-4-candidate.json",
                ROOT / "data/historical-real-v11-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json",
                ROOT / "data/historical-real-v11-2008-2025/dataset/walk-forward-plan.json",
                LAB / "ground-truth/nber-us-recessions-v1.json",
                LAB / "ground-truth/us-non-recession-stress-v2.json",
                LAB / "models/baseline-v1-5-dimensional.json",
                LAB / "models/baseline-v1-4-preregistered.json",
                LAB / "models/e11-shadow-candidate-gate-v1.json",
                LAB / "models/e11-preregistration-manifest.json",
            )
            first = write_dimensional_baseline_gate(*arguments, root / "first.json")
            second = write_dimensional_baseline_gate(*arguments, root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            report = json.loads(first.read_text())
            self.assertEqual("inner-validation-only", report["protocol"]["scope"])
            self.assertEqual(0, report["protocol"]["outerTestRowCountUsed"])
            self.assertTrue(all(item["outerTestRowCountUsed"] == 0 for item in report["folds"]))
            self.assertEqual(6, report["coverage"]["foldCount"])
            self.assertFalse(report["gate"]["operationalApprovalAuthorized"])

            altered_gate = json.loads(arguments[-2].read_text())
            altered_gate["innerValidation"]["maximumExpectedCalibrationError"] = 1.0
            altered_path = root / "altered-gate.json"
            altered_path.write_text(json.dumps(altered_gate))
            with self.assertRaises(DatasetValidationError):
                write_dimensional_baseline_gate(
                    *arguments[:-2], altered_path, arguments[-1], root / "altered.json"
                )


def _row(as_of: str, *, growth: float, risk: float, credit: float) -> dict[str, object]:
    return {
        "asOfDate": as_of,
        "featureScores": [
            {"featureCode": "GROWTH_MOM", "normalizedScore": growth},
            {"featureCode": "INFL_PRESS", "normalizedScore": 0.4},
            {"featureCode": "RISK_APPETITE", "normalizedScore": risk},
            {"featureCode": "MONETARY_COND", "normalizedScore": 0.6},
            {"featureCode": "CREDIT_STRESS", "normalizedScore": credit},
        ],
    }


if __name__ == "__main__":
    unittest.main()
