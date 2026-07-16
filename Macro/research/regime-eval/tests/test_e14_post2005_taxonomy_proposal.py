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
from regime_eval.e14_post2005_taxonomy_proposal import (
    write_e14_post2005_taxonomy_proposal,
)


class E14Post2005TaxonomyProposalTests(unittest.TestCase):
    def test_writes_separate_inactive_proposal_and_hash_bound_review_queue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "a")
            second = _write(root / "b")
            self.assertEqual(first[0].read_bytes(), second[0].read_bytes())
            self.assertEqual(first[1].read_bytes(), second[1].read_bytes())
            self.assertEqual(first[2].read_bytes(), second[2].read_bytes())

            proposal = json.loads(first[0].read_text(encoding="utf-8"))
            queue = json.loads(first[1].read_text(encoding="utf-8"))
            audit = json.loads(first[2].read_text(encoding="utf-8"))
            self.assertEqual("us-financial-stress-post2005-v1", proposal["proposedTaxonomyId"])
            self.assertFalse(proposal["activation"]["active"])
            self.assertFalse(proposal["activation"]["labelsAccepted"])
            self.assertEqual(2, len(proposal["proposedBankingHardNegativeControls"]))
            self.assertEqual(2, len(queue["dossiers"]))
            self.assertEqual([], queue["receipts"])
            self.assertTrue(audit["checks"]["proposalIdentifiersDoNotReuseLegacyEventIds"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["protocol"]["datasetRead"])

            dossier_paths = sorted((root / "a" / "dossiers").glob("*.json"))
            self.assertEqual(2, len(dossier_paths))
            for manifest, dossier in zip(queue["dossiers"], dossier_paths, strict=True):
                self.assertEqual(
                    manifest["sha256"], hashlib.sha256(dossier.read_bytes()).hexdigest()
                )

    def test_outputs_are_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            _write(root)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root)

    def test_rejects_contract_that_authorizes_scope_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["post2005ScopeActivationAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance"):
                _write(root / "out", contract=unsafe)

    def test_rejects_dossier_without_independent_evidence_providers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["evidenceAssertions"][1]["independenceGroup"] = "fdic"
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["inputHashes"]["proposalPlanV1Sha256"] = hashlib.sha256(
                unsafe_plan.read_bytes()
            ).hexdigest()
            unsafe_contract = root / "unsafe-contract.json"
            unsafe_contract.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "dossier blueprint"):
                _write(root / "out", contract=unsafe_contract, plan=unsafe_plan)


def _contract() -> Path:
    return Path("models/e14-post2005-taxonomy-proposal-contract-v1.json")


def _plan() -> Path:
    return Path("models/e14-post2005-taxonomy-proposal-plan-v1.json")


def _feasibility(output: Path) -> Path:
    return write_e14_post2005_scope_feasibility_audit(
        Path("models/e14-post2005-scope-feasibility-contract-v1.json"),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-vintage-policy-decision-contract-v1.json"),
        Path("models/e14-vintage-policy-decision-plan-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-vintage-policy-decision-audit-v1.json"),
        Path("models/e14-post2005-scope-feasibility-plan-v1.json"),
        Path("models/e14-post2005-source-feasibility-evidence-v1.json"),
        Path("models/e14-post2005-scope-feasibility-schema-v1.json"),
        output,
    )


def _write(
    root: Path,
    contract: Path | None = None,
    plan: Path | None = None,
) -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    feasibility = root / "scope-feasibility.json"
    if not feasibility.exists():
        _feasibility(feasibility)
    return write_e14_post2005_taxonomy_proposal(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        feasibility,
        Path("models/e14-post2005-scope-feasibility-plan-v1.json"),
        Path("models/e14-post2005-source-feasibility-evidence-v1.json"),
        plan or _plan(),
        Path("models/e14-post2005-taxonomy-proposal-schema-v1.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        root / "taxonomy-proposal.json",
        root / "dossiers",
        root / "review-queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
