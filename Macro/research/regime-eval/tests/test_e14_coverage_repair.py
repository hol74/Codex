from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_coverage_repair import write_e14_coverage_repair_audit


class E14CoverageRepairTests(unittest.TestCase):
    def test_preregisters_three_source_repair_without_opening_fitting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit_a = _write(root / "a.json")
            audit_b = _write(root / "b.json")
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual("STRUCTURAL_COVERAGE_REPAIR_PREREGISTERED_MATERIALIZATION_REQUIRED", audit["status"])
            self.assertEqual(3, audit["decision"]["replacementSourceCount"])
            self.assertEqual(28, audit["decision"]["projectedEligibleCandidateCount"])
            self.assertEqual(
                {"banking-credit": 4, "broad-market-repricing": 16,
                 "cross-border-growth": 4, "funding-liquidity": 4},
                audit["decision"]["projectedEligibleCandidateCountByMechanism"],
            )
            self.assertTrue(all(item["projectedStructurallyReady"] for item in audit["replacementSourceProjections"]))
            self.assertTrue(audit["decision"]["sourceMaterializationAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])
            self.assertFalse(audit["decision"]["candidateFittingAuthorized"])
            self.assertFalse(audit["decision"]["outerOosAuthorized"])
            self.assertFalse(audit["protocol"]["sourceDownloaded"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a.json")

    def test_rejects_post_hoc_history_reduction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(Path("models/e14-structural-coverage-repair-plan-v1.json").read_text())
            plan["historyPolicy"]["minimumHistoryMonths"] = 12
            unsafe = root / "unsafe-plan.json"
            unsafe.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", plan=unsafe)

    def test_rejects_contract_that_opens_fitting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-structural-coverage-repair-contract-v1.json").read_text())
            contract["authorizationPolicy"]["candidateFittingAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe)


def _write(
    output: Path,
    contract: Path = Path("models/e14-structural-coverage-repair-contract-v1.json"),
    plan: Path = Path("models/e14-structural-coverage-repair-plan-v1.json"),
) -> Path:
    return write_e14_coverage_repair_audit(
        contract,
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json"),
        Path("models/e14-four-detector-loeo-preregistration-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-loeo-preregistration-audit-v1.json"),
        plan,
        Path("models/e14-structural-coverage-repair-plan-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
