from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e12_foundation import write_e12_foundation_report


class E12FoundationTests(unittest.TestCase):
    def test_freezes_hashes_and_reports_missing_sofr_by_fold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = _write(root / "dataset.json", _dataset())
            corpus = _write(root / "corpus.json", _corpus())
            plan = _write(root / "plan.json", _plan())
            lifecycle = _write(root / "lifecycle.json", _lifecycle())

            output = write_e12_foundation_report(corpus, dataset, plan, lifecycle, root / "freeze.json")
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual("frozen", report["status"])
            self.assertEqual(24, len(report["freezeId"]))
            self.assertEqual(0.5, report["featureCoverage"]["SOFR_EFFR_MONTHLY_MAX"]["coverageRatio"])
            self.assertEqual(0.0, report["foldCoverage"][0]["train"]["features"]["SOFR_EFFR_MONTHLY_MAX"]["coverageRatio"])
            self.assertEqual(1.0, report["foldCoverage"][0]["test"]["features"]["SOFR_EFFR_MONTHLY_MAX"]["coverageRatio"])
            self.assertEqual(64, len(report["inputs"]["dataset"]["sha256"]))
            with self.assertRaisesRegex(DatasetValidationError, "Immutable E12 foundation freeze"):
                write_e12_foundation_report(corpus, dataset, plan, lifecycle, output)

    def test_rejects_corpus_counts_that_do_not_match_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus_payload = _corpus()
            corpus_payload["intramonthFeatureObservationCounts"]["SOFR_EFFR_MONTHLY_MAX"] = 2
            with self.assertRaisesRegex(DatasetValidationError, "do not match"):
                write_e12_foundation_report(
                    _write(root / "corpus.json", corpus_payload),
                    _write(root / "dataset.json", _dataset()),
                    _write(root / "plan.json", _plan()),
                    _write(root / "lifecycle.json", _lifecycle()),
                    root / "freeze.json",
                )


def _dataset() -> dict[str, object]:
    rows = []
    for as_of, funding in (("2020-01-31", False), ("2021-01-29", True)):
        codes = ["SAHM", "INDPRO_YOY", "YC_10Y2Y", "VIX_MONTHLY_MAX", "SPY_MONTHLY_MAX_DRAWDOWN", "HYG_MONTHLY_MAX_DRAWDOWN", "HY_OAS"]
        if funding:
            codes.append("SOFR_EFFR_MONTHLY_MAX")
        rows.append({
            "asOfDate": as_of,
            "macroObservations": [{
                "seriesCode": code, "observationDate": as_of,
                "publicationDate": as_of, "vintageDate": as_of, "value": 1.0,
            } for code in codes],
            "marketObservations": [{
                "symbol": "SPY", "observationDate": as_of,
                "availabilityDate": as_of, "value": 100.0,
            }],
            "forwardReturns": [{
                "symbol": "SPY", "horizonDays": 28, "fromDate": as_of,
                "toDate": "2020-02-28" if not funding else "2021-02-26",
                "startValue": 100.0, "endValue": 100.0, "returnValue": 0.0,
            }],
        })
    return {"schemaVersion": 1, "from": "2020-01-31", "to": "2021-01-29", "forwardReturnHorizonsDays": [28], "rows": rows}


def _corpus() -> dict[str, object]:
    return {
        "schemaVersion": 2, "requestedFrom": "2020-01-31", "requestedTo": "2021-01-29",
        "macroSnapshotCount": 2,
        "intramonthFeatureObservationCounts": {
            "VIX_MONTHLY_MAX": 2, "SOFR_EFFR_MONTHLY_MAX": 1,
            "SPY_MONTHLY_MAX_DRAWDOWN": 2, "HYG_MONTHLY_MAX_DRAWDOWN": 2,
        },
    }


def _plan() -> dict[str, object]:
    return {"foldCount": 1, "folds": [{
        "number": 1, "train_from": "2020-01-01", "train_to": "2020-12-31",
        "test_from": "2021-01-01", "test_to": "2021-12-31",
    }]}


def _lifecycle() -> dict[str, object]:
    return {
        "schemaVersion": 1, "contractId": "e12-task-lifecycle-v1", "frozenAt": "2026-07-14",
        "maximumLifecycleBeforeFreshProspectiveEvidence": "shadow-candidate",
        "selectionPolicy": "Nested inner rolling validation only",
        "missingnessPolicy": {"SOFR_EFFR_MONTHLY_MAX": "absent"},
        "tasks": {
            "recession-signal": {"requiredInputs": ["SAHM", "INDPRO_YOY", "YC_10Y2Y"]},
            "financial-stress-signal": {"requiredInputs": ["VIX_MONTHLY_MAX", "SOFR_EFFR_MONTHLY_MAX", "SPY_MONTHLY_MAX_DRAWDOWN", "HYG_MONTHLY_MAX_DRAWDOWN", "HY_OAS"]},
        },
    }


def _write(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
