from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e13_shortlist import write_e13_shortlist


class E13ShortlistTests(unittest.TestCase):
    def test_selects_distinct_financial_profiles_and_blocks_recession(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            selected = payload["selection"]["selected"]
            self.assertEqual(2, len(selected))
            self.assertEqual(
                {"coverage", "precision"}, {item["selectionRole"] for item in selected}
            )
            self.assertEqual(
                {"e13-financial-8ec8415452", "e13-financial-7452a93533"},
                {item["candidateId"] for item in selected},
            )
            self.assertEqual(0, payload["blockedTasks"][0]["candidateCountSelected"])
            self.assertFalse(payload["lifecycle"]["promotionAuthorized"])
            self.assertFalse(payload["lifecycle"]["outerOosOpened"])

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E13 shortlist"):
                _write(first)

    def test_rejects_contract_that_authorizes_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e13-shortlist-contract-v1.json").read_text(encoding="utf-8"))
            contract["promotionAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "shortlist contract is invalid"):
                _write(root / "shortlist.json", unsafe)


def _write(output: Path, contract: Path = Path("models/e13-shortlist-contract-v1.json")) -> Path:
    return write_e13_shortlist(
        Path("../../data/historical-real-v12-2008-2025/challengers/e13-loeo-evaluation-v1.json"),
        Path("models/e13-loeo-evaluation-contract-v1.json"),
        Path("models/e13-generated-candidates-v1.json"),
        contract,
        output,
    )


if __name__ == "__main__":
    unittest.main()
