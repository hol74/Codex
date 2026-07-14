from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e13_loeo import apply_persistence, write_e13_loeo_report


class E13LeaveOneEpisodeOutTests(unittest.TestCase):
    def test_persistence_has_distinct_entry_and_recovery(self) -> None:
        scores = [0.2, 0.7, 0.8, 0.4, 0.3, 0.8]
        self.assertEqual(
            [False, False, True, True, False, False],
            apply_persistence(scores, 0.5, entry_months=2, recovery_months=2),
        )

    def test_real_report_is_deterministic_inner_only_and_detects_episode_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(0, payload["protocol"]["outerTestRowCountUsed"])
            self.assertFalse(payload["protocol"]["shortlistProduced"])
            self.assertEqual(3, payload["coverage"]["financialEpisodeCount"])
            self.assertEqual(1, payload["coverage"]["recessionEpisodeCount"])
            self.assertEqual("LOEO_COMPLETE", payload["tasks"]["financial-stress-signal"]["status"])
            self.assertEqual("INSUFFICIENT_EPISODES", payload["tasks"]["recession-signal"]["status"])
            self.assertTrue(all(
                candidate["status"] == "LOEO_EVALUATED"
                for candidate in payload["tasks"]["financial-stress-signal"]["candidates"]
            ))
            self.assertTrue(all(
                candidate["aggregate"] is None
                for candidate in payload["tasks"]["recession-signal"]["candidates"]
            ))

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E13 LOEO"):
                _write(first)

    def test_rejects_contract_that_reopens_outer_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e13-loeo-evaluation-contract-v1.json").read_text(encoding="utf-8"))
            contract["outerOosPolicy"] = "Allowed to recover insufficient episodes."
            changed = root / "unsafe-contract.json"
            changed.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "evaluation contract is invalid"):
                _write(root / "report.json", changed)


def _write(output: Path, contract: Path = Path("models/e13-loeo-evaluation-contract-v1.json")) -> Path:
    data = Path("../../data/historical-real-v12-2008-2025")
    return write_e13_loeo_report(
        data / "dataset/historical-dataset-2008-04-01-2025-12-31.json",
        data / "dataset/walk-forward-plan.json",
        Path("ground-truth/us-non-recession-stress-v2.json"),
        Path("ground-truth/nber-us-recessions-v1.json"),
        Path("models/e13-candidate-generation-protocol-v1.json"),
        Path("models/e13-generated-candidates-v1.json"),
        Path("models/e12-data-foundation-lock-v1.json"),
        contract,
        output,
    )


if __name__ == "__main__":
    unittest.main()
