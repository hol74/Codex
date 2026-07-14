from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.e11_challengers import (
    _changepoint_step,
    _fit_weighted_logit,
    _logit_probability,
    write_e11_challenger_gate,
)


ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "research" / "regime-eval"
DATA = ROOT / "data" / "historical-real-v11-2008-2025"


class E11ChallengerTests(unittest.TestCase):
    def test_changepoint_probability_is_centered_on_frozen_thresholds(self) -> None:
        config = json.loads((LAB / "models/changepoint-duration-v1.json").read_text())
        state = {"active": False, "duration": 0, "exitStreak": 0}
        result = _changepoint_step(
            {"growthDeterioration": 0.6, "financialStress": 0.45},
            {"growthDeterioration": 2.5, "financialStress": 0.0},
            {"growthDeterioration": 0.0, "financialStress": 0.0},
            {"growthDeterioration": 1.0, "financialStress": 1.0},
            state,
            config,
        )
        self.assertEqual(0.5, result["probability"])
        self.assertTrue(result["active"])

    def test_weighted_logit_is_deterministic_and_finite(self) -> None:
        optimizer = json.loads((LAB / "models/rare-event-logit-v1.json").read_text())["optimizer"]
        vectors = [[-1.0, -0.5], [-0.5, 0.0], [0.5, 0.5], [1.0, 1.0]]
        labels = [False, False, True, True]
        first = _fit_weighted_logit(vectors, labels, 1.0, optimizer)
        second = _fit_weighted_logit(vectors, labels, 1.0, optimizer)
        self.assertEqual(first, second)
        self.assertTrue(all(0.0 < _logit_probability(first[0], row) < 1.0 for row in vectors))

    def test_real_inner_gates_are_deterministic_and_outer_oos_stays_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for model_id in ("changepoint-duration-v1", "rare-event-logit-v1"):
                arguments = (
                    DATA / "baseline/baseline-evaluation-2008-04-01-2025-12-31-v1-4-candidate.json",
                    DATA / "dataset/historical-dataset-2008-04-01-2025-12-31.json",
                    DATA / "dataset/walk-forward-plan.json",
                    LAB / "ground-truth/nber-us-recessions-v1.json",
                    LAB / "ground-truth/us-non-recession-stress-v2.json",
                    LAB / f"models/{model_id}.json",
                    LAB / "models/e11-shadow-candidate-gate-v1.json",
                    LAB / "models/e11-preregistration-manifest.json",
                )
                first = write_e11_challenger_gate(*arguments, root / f"{model_id}-first.json")
                second = write_e11_challenger_gate(*arguments, root / f"{model_id}-second.json")
                self.assertEqual(first.read_bytes(), second.read_bytes())
                report = json.loads(first.read_text())
                self.assertEqual("inner-validation-only", report["protocol"]["scope"])
                self.assertEqual(0, report["protocol"]["outerTestRowCountUsed"])
                self.assertTrue(all(item["outerTestRowCountUsed"] == 0 for item in report["folds"]))
                self.assertEqual(6, report["coverage"]["foldCount"])
                self.assertFalse(report["gate"]["operationalApprovalAuthorized"])


if __name__ == "__main__":
    unittest.main()
