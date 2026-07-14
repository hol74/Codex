from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e12_recession_hazard import (
    recession_hazard_predictions,
    write_e12_recession_preregistration,
)


ROOT = Path(__file__).resolve().parents[1]


class E12RecessionHazardTests(unittest.TestCase):
    def test_prediction_is_causal_and_future_rows_do_not_change_history(self) -> None:
        config = _config()
        history = [_row("2020-01-31", 0.0, 1.0, -0.5), _row("2020-02-28", 0.0, 0.0, 0.2)]
        before = recession_hazard_predictions(history, config)
        after = recession_hazard_predictions(history + [_row("2020-03-31", 4.0, -15.0, 0.5)], config)
        self.assertEqual(before, after[:2])
        self.assertGreater(before[1]["components"]["curveTransition"], 0.0)

    def test_sahm_and_production_deterioration_raise_hazard(self) -> None:
        prediction = recession_hazard_predictions(
            [_row("2020-04-30", 0.3, -5.95, 0.44)], _config()
        )[0]
        self.assertTrue(prediction["predictedRecession"])
        self.assertGreaterEqual(prediction["hazardScore"], 0.5)

    def test_preregistration_is_hash_bound_and_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"
            result = write_e12_recession_preregistration(
                ROOT / "models/sahm-yield-hazard-v1.json",
                ROOT / "models/e12-recession-hazard-gate-v1.json",
                ROOT / "models/e12-data-foundation-lock-v1.json",
                output,
            )
            manifest = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual("sahm-yield-hazard-v1", manifest["modelId"])
            self.assertEqual("preregistered", manifest["status"])
            with self.assertRaisesRegex(DatasetValidationError, "Immutable E12 recession preregistration"):
                write_e12_recession_preregistration(
                    ROOT / "models/sahm-yield-hazard-v1.json",
                    ROOT / "models/e12-recession-hazard-gate-v1.json",
                    ROOT / "models/e12-data-foundation-lock-v1.json",
                    output,
                )


def _config() -> dict[str, object]:
    return json.loads((ROOT / "models/sahm-yield-hazard-v1.json").read_text(encoding="utf-8"))


def _row(as_of: str, sahm: float, indpro: float, curve: float) -> dict[str, object]:
    return {
        "asOfDate": as_of,
        "macroObservations": [
            {"seriesCode": "SAHM", "value": sahm},
            {"seriesCode": "INDPRO_YOY", "value": indpro},
            {"seriesCode": "YC_10Y2Y", "value": curve},
        ],
    }


if __name__ == "__main__":
    unittest.main()
