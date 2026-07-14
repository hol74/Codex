from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e13_gate import write_e13_financial_gate_decisions


class E13AbsoluteGateTests(unittest.TestCase):
    def test_rejects_both_profiles_independently_without_outer_or_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("completed-no-eligible-candidates", payload["status"])
            self.assertEqual(0, payload["protocol"]["passedCount"])
            self.assertFalse(payload["protocol"]["relativeRankingUsed"])
            self.assertFalse(payload["protocol"]["fallbackCandidateAllowed"])
            decisions = {item["candidateId"]: item for item in payload["decisions"]}
            self.assertEqual(
                ["maximumMeanControlFalsePositiveRate"],
                decisions["e13-financial-8ec8415452"]["failedChecks"],
            )
            self.assertEqual(
                ["minimumEpisodeHitRate", "minimumMeanEpisodeRecall", "minimumWorstEpisodeRecall"],
                decisions["e13-financial-7452a93533"]["failedChecks"],
            )
            self.assertFalse(payload["phaseDecision"]["outerOosOpened"])
            self.assertFalse(payload["phaseDecision"]["fusionAllowed"])

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E13 gate decisions"):
                _write(first)

    def test_rejects_gate_that_reopens_outer_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gate = json.loads(Path("models/e13-financial-absolute-gate-v1.json").read_text(encoding="utf-8"))
            gate["outerOosPolicy"] = "Allowed for candidate rescue."
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(gate), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "absolute gate contract is invalid"):
                _write(root / "decision.json", unsafe)


def _write(output: Path, gate: Path = Path("models/e13-financial-absolute-gate-v1.json")) -> Path:
    return write_e13_financial_gate_decisions(
        Path("models/e13-financial-shortlist-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e13-loeo-evaluation-v1.json"),
        gate,
        output,
    )


if __name__ == "__main__":
    unittest.main()
