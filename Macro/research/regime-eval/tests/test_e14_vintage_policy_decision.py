from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_vintage_policy_decision import write_e14_vintage_policy_decision_audit


class E14VintagePolicyDecisionTests(unittest.TestCase):
    def test_selects_blocked_post2005_scope_without_reopening_legacy_e14(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual("separately-versioned-post-2005-research-scope", audit["decision"]["selectedPolicy"])
            self.assertFalse(audit["selectedPolicy"]["legacyE14Reopened"])
            self.assertFalse(audit["selectedPolicy"]["post2005ScopeActivated"])
            scope = audit["post2005ScopeAssessment"]
            self.assertEqual("2006-01-01", scope["cutoffInclusive"])
            self.assertEqual({
                "banking-credit": 2, "broad-market-repricing": 4,
                "cross-border-growth": 2, "funding-liquidity": 2,
            }, scope["positiveEpisodeCounts"])
            self.assertEqual({
                "banking-credit": 0, "broad-market-repricing": 2,
                "cross-border-growth": 2, "funding-liquidity": 2,
            }, scope["hardNegativeEpisodeCounts"])
            self.assertEqual(2, scope["requiredBankingHardNegativeAdditions"])
            self.assertTrue(audit["decision"]["bankingHardNegativeFeasibilityDesignAuthorized"])
            self.assertFalse(audit["decision"]["taxonomyMutationAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["protocol"]["datasetRead"])
            self.assertFalse(audit["protocol"]["loeoScoreRead"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_rejects_post_hoc_cutoff_change_even_when_plan_hash_is_updated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["post2005Scope"]["cutoffInclusive"] = "2010-01-01"
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            unsafe_contract = _contract_for_plan(root, unsafe_plan)
            with self.assertRaisesRegex(DatasetValidationError, "cutoff differs"):
                _write(root / "out.json", contract=unsafe_contract, plan=unsafe_plan)

    def test_rejects_selecting_archival_acquisition_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["alternatives"][1]["decision"] = "selected-conditionally"
            plan["alternatives"][2]["decision"] = "not-selected"
            plan["selectedPolicy"] = "fund-provider-primary-archival-reconstruction"
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            unsafe_contract = _contract_for_plan(root, unsafe_plan)
            with self.assertRaisesRegex(DatasetValidationError, "selected policy differs"):
                _write(root / "out.json", contract=unsafe_contract, plan=unsafe_plan)

    def test_rejects_contract_that_opens_taxonomy_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["taxonomyMutationAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe)


def _contract() -> Path:
    return Path("models/e14-vintage-policy-decision-contract-v1.json")


def _plan() -> Path:
    return Path("models/e14-vintage-policy-decision-plan-v1.json")


def _contract_for_plan(root: Path, plan: Path) -> Path:
    contract = json.loads(_contract().read_text(encoding="utf-8"))
    contract["inputHashes"]["vintagePolicyPlanV1Sha256"] = hashlib.sha256(plan.read_bytes()).hexdigest()
    path = root / "unsafe-contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def _write(output: Path, contract: Path | None = None, plan: Path | None = None) -> Path:
    return write_e14_vintage_policy_decision_audit(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-new-information-hypothesis-plan-v1.json"),
        Path("models/e14-replacement-source-feasibility-contract-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-replacement-source-feasibility-audit-v1.json"),
        plan or _plan(),
        Path("models/e14-vintage-policy-decision-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
