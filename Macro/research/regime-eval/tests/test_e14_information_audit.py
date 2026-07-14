from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_information_audit import write_e14_information_audit


class E14InformationAuditTests(unittest.TestCase):
    def test_real_audit_is_deterministic_diagnostic_only_and_inner_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(0, payload["protocol"]["outerTestRowCountUsed"])
            self.assertFalse(payload["protocol"]["candidateGenerated"])
            self.assertFalse(payload["protocol"]["rankingProduced"])
            self.assertFalse(payload["protocol"]["promotionAuthorized"])
            self.assertEqual(3, payload["coverage"]["financialEpisodeCount"])
            self.assertEqual(1, payload["coverage"]["observableRecessionEpisodeCount"])
            self.assertEqual(5, len(payload["featureSeparability"]))
            self.assertFalse(payload["labelAudit"]["absenceOfFinancialLabelIsConfirmedNegative"])

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E14"):
                _write(first)

    def test_rejects_contract_that_opens_outer_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-information-audit-contract-v1.json").read_text(encoding="utf-8"))
            contract["outerOosPolicy"] = "Allowed for diagnosis."
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "contract is invalid"):
                _write(root / "audit.json", unsafe)


def _write(output: Path, contract: Path = Path("models/e14-information-audit-contract-v1.json")) -> Path:
    data = Path("../../data/historical-real-v12-2008-2025")
    return write_e14_information_audit(
        data / "dataset/historical-dataset-2008-04-01-2025-12-31.json",
        data / "dataset/walk-forward-plan.json",
        Path("ground-truth/us-non-recession-stress-v2.json"),
        Path("ground-truth/nber-us-recessions-v1.json"),
        Path("models/e12-data-foundation-lock-v1.json"),
        Path("models/e13-financial-gate-decisions-v1.json"),
        contract,
        output,
    )


if __name__ == "__main__":
    unittest.main()
