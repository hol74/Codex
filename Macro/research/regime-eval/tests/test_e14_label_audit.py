from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_label_audit import write_e14_label_audit


class E14LabelAuditTests(unittest.TestCase):
    def test_reports_missing_hard_negatives_without_inventing_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("NOT_READY_FOR_CANDIDATE_GENERATION", payload["status"])
            self.assertEqual(6, payload["inventory"]["fullPositiveEpisodeCount"])
            self.assertEqual(2, payload["inventory"]["fullAmbiguousEpisodeCount"])
            self.assertEqual(0, payload["inventory"]["fullHardNegativeEpisodeCount"])
            self.assertEqual(0, payload["protocol"]["implicitNegativesCreated"])
            self.assertEqual(0, payload["protocol"]["outerFeatureRowCountUsed"])
            self.assertIn("minimumHardNegativeEpisodes", payload["failedChecks"])
            self.assertFalse(payload["decision"]["candidateGenerationAuthorized"])

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E14 label audit"):
                _write(first)

    def test_rejects_implicit_negative_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-label-audit-contract-v1.json").read_text(encoding="utf-8"))
            contract["implicitNegativePolicy"] = "Unlabeled months are negatives."
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "contract is invalid"):
                _write(root / "audit.json", unsafe)


def _write(output: Path, contract: Path = Path("models/e14-label-audit-contract-v1.json")) -> Path:
    data = Path("../../data/historical-real-v12-2008-2025")
    return write_e14_label_audit(
        Path("ground-truth/us-financial-stress-v3.json"),
        data / "challengers/e14-information-audit-v1.json",
        data / "dataset/historical-dataset-2008-04-01-2025-12-31.json",
        data / "dataset/walk-forward-plan.json",
        contract,
        output,
    )


if __name__ == "__main__":
    unittest.main()
