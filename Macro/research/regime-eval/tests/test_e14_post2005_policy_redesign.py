from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_policy_redesign import (
    STATUS,
    write_e14_post2005_policy_redesign_proposal,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025/challengers"


class E14Post2005PolicyRedesignTests(unittest.TestCase):
    def test_materializes_hash_bound_proposal_and_opens_only_independent_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outputs = _write(Path(directory))
            self.assertEqual(5, len(outputs))
            audit = json.loads(outputs[-1].read_text(encoding="utf-8"))
            queue = json.loads(outputs[-2].read_text(encoding="utf-8"))
            proposal = json.loads(outputs[0].read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(["broad-market-repricing", "funding-liquidity"], proposal["preservedReadyMechanisms"])
            self.assertEqual(2, len(queue["dossiers"]))
            self.assertEqual([], queue["receipts"])
            self.assertTrue(audit["decision"]["independentReviewHandoffAuthorized"])
            self.assertFalse(audit["decision"]["policyActivationAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["decision"]["featureTransformationAuthorized"])
            for dossier in queue["dossiers"]:
                path = Path(directory) / "dossiers" / dossier["fileName"]
                self.assertEqual(dossier["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_updated_hash_cannot_hide_missing_g5_months(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads((MODEL / "e14-post2005-policy-redesign-evidence-v1.json").read_text(encoding="utf-8"))
            evidence["replacementSource"]["missingReleaseMonthsBeforeTaper"] = ["2008-06"]
            evidence_path = root / "evidence.json"
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["redesignEvidenceSha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "outputs", contract_path, evidence_path)

    def test_outputs_are_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root)


def _write(root: Path, contract: Path | None = None, evidence: Path | None = None) -> tuple[Path, ...]:
    return write_e14_post2005_policy_redesign_proposal(
        contract or MODEL / "e14-post2005-policy-redesign-contract-v1.json",
        DATA / "e14-post2005-vintage-fitness-audit-v1.json",
        DATA / "e14-post2005-vintage-remediation-audit-v1.json",
        MODEL / "e14-post2005-scope-feasibility-plan-v1.json",
        MODEL / "e14-post2005-vintage-fitness-audit-plan-v1.json",
        evidence or MODEL / "e14-post2005-policy-redesign-evidence-v1.json",
        MODEL / "e14-post2005-policy-redesign-plan-v1.json",
        MODEL / "e14-post2005-policy-redesign-schema-v1.json",
        MODEL / "e14-independent-review-schema-v2.json",
        root / "proposal.json",
        root / "dossiers",
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
