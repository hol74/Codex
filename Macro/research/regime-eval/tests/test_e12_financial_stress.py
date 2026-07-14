from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e12_financial_stress import (
    financial_stress_prediction,
    write_e12_financial_preregistration,
)


ROOT = Path(__file__).resolve().parents[1]


class E12FinancialStressTests(unittest.TestCase):
    def test_funding_overlay_is_causal_optional_and_never_zero_imputed(self) -> None:
        config = json.loads((ROOT / "models/event-aware-financial-stress-v1.json").read_text(encoding="utf-8"))
        base = _row(None)
        repo = _row(295.0)

        without_funding = financial_stress_prediction(base, config)
        with_funding = financial_stress_prediction(repo, config)

        self.assertFalse(without_funding["fundingAvailable"])
        self.assertIsNone(without_funding["severities"]["funding"])
        self.assertEqual(without_funding["baseScore"], without_funding["finalScore"])
        self.assertTrue(with_funding["fundingAvailable"])
        self.assertGreater(with_funding["finalScore"], with_funding["baseScore"])
        self.assertTrue(with_funding["predictedFinancialStress"])

    def test_prediction_rejects_missing_base_feature(self) -> None:
        config = json.loads((ROOT / "models/event-aware-financial-stress-v1.json").read_text(encoding="utf-8"))
        row = _row(None)
        row["macroObservations"] = row["macroObservations"][:-1]
        with self.assertRaisesRegex(DatasetValidationError, "lacks base inputs"):
            financial_stress_prediction(row, config)

    def test_preregistration_binds_candidate_gate_and_foundation_lock_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"
            result = write_e12_financial_preregistration(
                ROOT / "models/event-aware-financial-stress-v1.json",
                ROOT / "models/e12-financial-stress-gate-v1.json",
                ROOT / "models/e12-data-foundation-lock-v1.json",
                output,
            )
            manifest = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual("preregistered", manifest["status"])
            self.assertEqual(64, len(manifest["candidate"]["sha256"]))
            self.assertEqual("shadow-candidate", manifest["maximumLifecycle"])
            with self.assertRaisesRegex(DatasetValidationError, "Immutable E12 financial preregistration"):
                write_e12_financial_preregistration(
                    ROOT / "models/event-aware-financial-stress-v1.json",
                    ROOT / "models/e12-financial-stress-gate-v1.json",
                    ROOT / "models/e12-data-foundation-lock-v1.json",
                    output,
                )


def _row(funding: float | None) -> dict[str, object]:
    values = {
        "VIX_MONTHLY_MAX": 19.66,
        "SPY_MONTHLY_MAX_DRAWDOWN": 1.5,
        "HYG_MONTHLY_MAX_DRAWDOWN": 0.51,
        "HY_OAS": 2.2,
    }
    if funding is not None:
        values["SOFR_EFFR_MONTHLY_MAX"] = funding
    return {
        "asOfDate": "2019-09-30",
        "macroObservations": [
            {"seriesCode": code, "value": value} for code, value in values.items()
        ],
    }


if __name__ == "__main__":
    unittest.main()
