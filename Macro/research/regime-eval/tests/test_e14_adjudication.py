from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_adjudication import INDEPENDENCE_DECLARATION, write_e14_adjudication_queue


class E14AdjudicationTests(unittest.TestCase):
    def test_builds_four_hard_negatives_and_review_queue_without_self_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_a, audit_a = _write(root / "a")
            queue_b, audit_b = _write(root / "b")
            audit = json.loads(audit_a.read_text(encoding="utf-8"))
            queue = json.loads(queue_a.read_text(encoding="utf-8"))

            self.assertEqual(queue_a.read_bytes(), queue_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual("INDEPENDENT_REVIEW_REQUIRED", audit["status"])
            self.assertEqual(4, audit["inventory"]["hardNegativeReviewedDossierCount"])
            self.assertEqual(12, audit["inventory"]["queuedDossierCount"])
            self.assertEqual(0, audit["inventory"]["independentReviewReceiptCount"])
            self.assertEqual(0, audit["inventory"]["independentlyAcceptedDossierCount"])
            self.assertTrue(all(value == 1 for value in audit["hardNegativeMechanismCoverage"].values()))
            self.assertTrue(all(item["reviewStatus"] == "awaiting-independent-review" for item in queue["dossiers"]))
            self.assertFalse(audit["decision"]["labelFoundationGateAuthorized"])
            self.assertFalse(audit["decision"]["groundTruthMutationAuthorized"])
            self.assertEqual(4, len(list((root / "a" / "negative").glob("*.json"))))

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_receipt_authored_by_dossier_author_before_writing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue, _ = _write(root / "source")
            manifest = json.loads(queue.read_text(encoding="utf-8"))["dossiers"][0]
            receipts = root / "invalid" / "receipts"
            receipts.mkdir(parents=True)
            receipt = {
                "schemaVersion": 1,
                "reviewId": "e14-review-self-authored",
                "dossierId": manifest["dossierId"],
                "dossierSha256": manifest["sha256"],
                "reviewerId": "codex-primary-source-review-2026-07-14",
                "reviewerAffiliation": "repository author",
                "independenceDeclaration": INDEPENDENCE_DECLARATION,
                "reviewedAt": "2026-07-14",
                "decision": "accept",
                "rationale": "This deliberately invalid receipt is long enough for structural validation but must fail because its reviewer authored the evidence pack and dossier.",
                "checks": {
                    "sourceLocatorsOpened": True,
                    "mechanismClaimSupported": True,
                    "boundariesSupported": True,
                    "counterEvidenceConsidered": True,
                    "noModelOutputUsed": True,
                },
            }
            (receipts / "self.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "not independent"):
                _write(root / "invalid", receipts)
            self.assertFalse((root / "invalid" / "negative").exists())
            self.assertFalse((root / "invalid" / "queue.json").exists())

    def test_complete_mixed_review_finishes_review_but_requires_dossier_revisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = root / "receipts"
            receipts.mkdir()
            queue = json.loads(Path(
                "../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v2.json"
            ).read_text(encoding="utf-8"))
            for index, manifest in enumerate(queue["dossiers"]):
                decision = "accept" if index == 0 else "needs-revision"
                receipt = {
                    "schemaVersion": 1,
                    "reviewId": f"e14-review-fixture-{index}",
                    "dossierId": manifest["dossierId"],
                    "dossierSha256": manifest["sha256"],
                    "reviewerId": "independent-test-reviewer",
                    "reviewerAffiliation": "test fixture",
                    "independenceDeclaration": INDEPENDENCE_DECLARATION,
                    "reviewedAt": "2026-07-14",
                    "decision": decision,
                    "rationale": "Independent test rationale long enough to validate complete review handling without implying that every dossier has been accepted.",
                    "checks": {
                        "sourceLocatorsOpened": True,
                        "mechanismClaimSupported": decision == "accept",
                        "boundariesSupported": decision == "accept",
                        "counterEvidenceConsidered": True,
                        "noModelOutputUsed": True,
                    },
                }
                (receipts / f"receipt-{index}.json").write_text(json.dumps(receipt), encoding="utf-8")

            _, audit_path = _write(root / "mixed", receipts)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual("DOSSIER_REVISIONS_REQUIRED", audit["status"])
            self.assertTrue(audit["decision"]["independentReviewComplete"])
            self.assertFalse(audit["decision"]["allDossiersAccepted"])
            self.assertFalse(audit["decision"]["labelFoundationGateAuthorized"])
            self.assertEqual(1, audit["inventory"]["independentlyAcceptedDossierCount"])
            self.assertEqual(11, audit["inventory"]["needsRevisionDossierCount"])


def _write(root: Path, receipts: Path | None = None) -> tuple[Path, Path]:
    receipts = receipts or root / "receipts"
    return write_e14_adjudication_queue(
        Path("models/e14-hard-negative-dossier-pack-v1.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-independent-review-schema-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        Path("models/e14-positive-dossier-pack-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-positive-dossier-curation-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1"),
        root / "negative",
        receipts,
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
