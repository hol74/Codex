from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_label_foundation_gate import _conflicts, write_e14_label_foundation_gate


class E14LabelFoundationGateTests(unittest.TestCase):
    def test_builds_conflict_free_mechanism_month_proposal_but_keeps_candidates_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal_a, audit_a = _write(root / "a")
            proposal_b, audit_b = _write(root / "b")
            proposal = json.loads(proposal_a.read_text(encoding="utf-8"))
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual(proposal_a.read_bytes(), proposal_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual("FOUNDATION_MERGE_READY_MORE_EVIDENCE_REQUIRED", audit["status"])
            self.assertEqual(12, audit["inventory"]["acceptedDossierCount"])
            self.assertEqual(0, audit["inventory"]["sameMechanismMonthConflictCount"])
            self.assertEqual(0, audit["inventory"]["taxonomyMergeConflictCount"])
            self.assertGreater(audit["inventory"]["mixedMechanismMonthCount"], 0)
            self.assertTrue(audit["decision"]["foundationMergeAuthorized"])
            self.assertFalse(audit["decision"]["coverageSufficientForCandidateGeneration"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])
            self.assertTrue(audit["coverage"]["positiveThresholdsSatisfied"])
            self.assertFalse(audit["coverage"]["hardNegativeThresholdsSatisfied"])
            self.assertEqual(12, len(proposal["dossierLabels"]))

            mexico = [item for item in proposal["monthlyMechanismLabels"] if item["month"] == "1995-01-01"]
            self.assertIn("positive", {item["state"] for item in mexico})
            self.assertIn("hard-negative", {item["state"] for item in mexico})

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_contract_that_allows_implicit_negatives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-label-foundation-gate-contract-v1.json").read_text())
            contract["conflictPolicy"]["unlabeledNeverBecomesHardNegative"] = False
            unsafe = root / "contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "unsafe", unsafe)

    def test_conflict_key_is_month_and_mechanism(self) -> None:
        labels = [
            {
                "month": "1995-01-01",
                "mechanism": "banking-credit",
                "state": "positive",
                "episodeId": "positive-bank",
            },
            {
                "month": "1995-01-01",
                "mechanism": "banking-credit",
                "state": "hard-negative",
                "episodeId": "negative-bank",
            },
            {
                "month": "1995-01-01",
                "mechanism": "cross-border-growth",
                "state": "positive",
                "episodeId": "positive-cross-border",
            },
        ]

        conflicts = _conflicts(labels)

        self.assertEqual(1, len(conflicts))
        self.assertEqual("1995-01-01", conflicts[0]["month"])
        self.assertEqual("banking-credit", conflicts[0]["mechanism"])
        self.assertEqual(["hard-negative", "positive"], conflicts[0]["states"])


def _write(root: Path, contract: Path = Path("models/e14-label-foundation-gate-contract-v1.json")):
    return write_e14_label_foundation_gate(
        contract,
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-targeted-review-ingestion-audit-v1.json"),
        Path("ground-truth/us-financial-stress-v3.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-label-foundation-proposal-schema-v1.json"),
        Path("models/e14-label-audit-contract-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-revised-dossiers-v1"),
        root / "proposal.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
