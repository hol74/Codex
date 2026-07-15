from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_scope_feasibility import (
    write_e14_post2005_scope_feasibility_audit,
)


class E14Post2005ScopeFeasibilityTests(unittest.TestCase):
    def test_authorizes_only_separate_taxonomy_proposal_preregistration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))

            self.assertTrue(audit["scopeAssessment"]["positiveIdentifiabilitySatisfied"])
            self.assertTrue(audit["scopeAssessment"]["hardNegativeIdentifiabilitySatisfied"])
            self.assertEqual(
                {
                    "banking-credit": 2,
                    "broad-market-repricing": 2,
                    "cross-border-growth": 2,
                    "funding-liquidity": 2,
                },
                audit["scopeAssessment"]["hardNegativeEpisodeCountsAfterCandidates"],
            )
            self.assertEqual(
                {
                    "banking-credit": 1,
                    "broad-market-repricing": 1,
                    "cross-border-growth": 1,
                    "funding-liquidity": 1,
                },
                audit["readyFeatureFamilyCounts"],
            )
            self.assertTrue(audit["decision"]["taxonomyProposalPreregistrationAuthorized"])
            self.assertFalse(audit["decision"]["post2005ScopeActivated"])
            self.assertFalse(audit["decision"]["taxonomyMutationAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["protocol"]["seriesObservationDownloaded"])
            self.assertFalse(audit["protocol"]["loeoScoreRead"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_rejects_banking_candidate_that_overlaps_positive_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["bankingHardNegativeCandidates"][0]["firstMonth"] = "2011-07-01"
            plan["bankingHardNegativeCandidates"][0]["lastMonth"] = "2011-10-01"
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            contract = _contract_with_hash(root, "scopePlanV1Sha256", unsafe_plan)
            with self.assertRaisesRegex(DatasetValidationError, "candidates are not feasible"):
                _write(root / "out.json", contract=contract, plan=unsafe_plan)

    def test_rejects_source_without_release_proof(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads(_evidence().read_text(encoding="utf-8"))
            evidence["sources"][0]["releaseProofComplete"] = False
            evidence["sources"][0]["blockingReasons"] = ["release-proof-removed"]
            unsafe_evidence = root / "unsafe-evidence.json"
            unsafe_evidence.write_text(json.dumps(evidence), encoding="utf-8")
            contract = _contract_with_hash(
                root, "sourceEvidenceV1Sha256", unsafe_evidence
            )
            with self.assertRaisesRegex(DatasetValidationError, "source/family feasibility gate failed"):
                _write(root / "out.json", contract=contract, evidence=unsafe_evidence)

    def test_rejects_contract_that_activates_taxonomy_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["taxonomyMutationAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe)


def _contract() -> Path:
    return Path("models/e14-post2005-scope-feasibility-contract-v1.json")


def _plan() -> Path:
    return Path("models/e14-post2005-scope-feasibility-plan-v1.json")


def _evidence() -> Path:
    return Path("models/e14-post2005-source-feasibility-evidence-v1.json")


def _contract_with_hash(root: Path, key: str, artifact: Path) -> Path:
    contract = json.loads(_contract().read_text(encoding="utf-8"))
    contract["inputHashes"][key] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    path = root / f"contract-{key}.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def _write(
    output: Path,
    contract: Path | None = None,
    plan: Path | None = None,
    evidence: Path | None = None,
) -> Path:
    return write_e14_post2005_scope_feasibility_audit(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-vintage-policy-decision-contract-v1.json"),
        Path("models/e14-vintage-policy-decision-plan-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-vintage-policy-decision-audit-v1.json"),
        plan or _plan(),
        evidence or _evidence(),
        Path("models/e14-post2005-scope-feasibility-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
