from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError, load_dataset, write_manifest


class DatasetTests(unittest.TestCase):
    def test_load_dataset_validates_and_builds_reproducible_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "historical-dataset.json"
            path.write_text(json.dumps(_dataset()), encoding="utf-8")

            dataset = load_dataset(path)
            manifest = dataset.manifest()

            self.assertEqual(1, manifest["coverage"]["rowCount"])
            self.assertEqual([28], manifest["forwardReturnHorizonsDays"])
            self.assertEqual(["SPY"], manifest["marketSymbols"])
            self.assertEqual(64, len(manifest["dataset"]["sha256"]))
            output = write_manifest(dataset, Path(directory) / "manifest.json")
            self.assertEqual(manifest, json.loads(output.read_text(encoding="utf-8")))

    def test_load_dataset_rejects_future_macro_availability(self) -> None:
        payload = _dataset()
        payload["rows"][0]["macroObservations"][0]["availabilityDate"] = "2020-01-03"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leaking.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "leaks future information"):
                load_dataset(path)

    def test_load_dataset_accepts_dotnet_macro_vintage_date_contract(self) -> None:
        payload = _dataset()
        observation = payload["rows"][0]["macroObservations"][0]
        observation["vintageDate"] = observation.pop("availabilityDate")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dotnet-contract.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            dataset = load_dataset(path)

            self.assertEqual(1, len(dataset.rows))

    def test_load_dataset_rejects_inconsistent_forward_return(self) -> None:
        payload = _dataset()
        payload["rows"][0]["forwardReturns"][0]["returnValue"] = 0.2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-return.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "inconsistent with prices"):
                load_dataset(path)


def _dataset() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "from": "2020-01-02",
        "to": "2020-01-02",
        "forwardReturnHorizonsDays": [28],
        "rows": [
            {
                "asOfDate": "2020-01-02",
                "macroObservations": [
                    {
                        "observationDate": "2019-12-31",
                        "publicationDate": "2020-01-02",
                        "availabilityDate": "2020-01-02",
                        "value": 2.0,
                    }
                ],
                "marketObservations": [
                    {
                        "symbol": "SPY",
                        "observationDate": "2020-01-02",
                        "availabilityDate": "2020-01-02",
                        "value": 100.0,
                    }
                ],
                "forwardReturns": [
                    {
                        "symbol": "SPY",
                        "horizonDays": 28,
                        "fromDate": "2020-01-02",
                        "toDate": "2020-01-30",
                        "startValue": 100.0,
                        "endValue": 110.0,
                        "returnValue": 0.1,
                    }
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
