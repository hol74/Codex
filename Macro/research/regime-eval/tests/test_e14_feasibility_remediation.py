from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_feasibility_remediation import (
    write_e14_feasibility_remediation_audit,
)


class E14FeasibilityRemediationTests(unittest.TestCase):
    def test_preregisters_exact_remediation_and_only_opens_reaudit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual("FEASIBILITY_REMEDIATION_PREREGISTERED_REAUDIT_REQUIRED", audit["status"])
            self.assertEqual(3, audit["inventory"]["preservedConditionalFamilyCount"])
            self.assertEqual(5, audit["inventory"]["retiredFamilyCount"])
            self.assertEqual(7, audit["inventory"]["replacementSourceCount"])
            self.assertEqual(5, audit["inventory"]["replacementFamilyCount"])
            self.assertTrue(all(item["nominalCoverageSatisfied"] for item in audit["replacementAssessments"]))
            self.assertTrue(audit["decision"]["sourceFeasibilityReauditAuthorized"])
            self.assertFalse(audit["decision"]["replacementSourceReadinessEstablished"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["protocol"]["seriesObservationDownloaded"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            preserved = {item["familyId"] for item in audit["preservedConditionalFamilies"]}
            self.assertEqual({
                "bank-balance-sheet-flow", "cross-dollar-shock", "cross-bank-flow-contraction",
            }, preserved)
            retired = {item["familyId"] for item in audit["retiredFamilies"]}
            self.assertEqual({
                "bank-loss-absorption", "broad-equity-drawdown",
                "broad-credit-quality-dispersion", "funding-unsecured-tiering",
                "funding-secured-repo-dislocation",
            }, retired)

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_rejects_preserving_a_previously_blocked_family(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["preservedConditionalFamilies"][0]["familyId"] = "bank-loss-absorption"
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            unsafe_contract = _contract_for_plan(root, unsafe_plan)
            with self.assertRaisesRegex(DatasetValidationError, "preserve/retire sets differ"):
                _write(root / "out.json", contract=unsafe_contract, plan=unsafe_plan)

    def test_rejects_contract_that_opens_source_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["sourceAcquisitionAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe)

    def test_rejects_insufficient_replacement_history_with_updated_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["replacementSources"][0]["coverageFrom"] = "1984-01-01"
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            unsafe_contract = _contract_for_plan(root, unsafe_plan)
            with self.assertRaisesRegex(DatasetValidationError, "nominal coverage violates"):
                _write(root / "out.json", contract=unsafe_contract, plan=unsafe_plan)


def _contract() -> Path:
    return Path("models/e14-feasibility-remediation-contract-v1.json")


def _plan() -> Path:
    return Path("models/e14-feasibility-remediation-plan-v1.json")


def _contract_for_plan(root: Path, plan: Path) -> Path:
    contract = json.loads(_contract().read_text(encoding="utf-8"))
    contract["inputHashes"]["remediationPlanV1Sha256"] = hashlib.sha256(plan.read_bytes()).hexdigest()
    path = root / "unsafe-contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def _write(output: Path, contract: Path | None = None, plan: Path | None = None) -> Path:
    return write_e14_feasibility_remediation_audit(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-new-information-hypothesis-plan-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-new-information-hypothesis-audit-v1.json"),
        Path("models/e14-source-vintage-feasibility-contract-v1.json"),
        Path("models/e14-source-vintage-feasibility-evidence-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-source-vintage-feasibility-audit-v1.json"),
        plan or _plan(),
        Path("models/e14-feasibility-remediation-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
