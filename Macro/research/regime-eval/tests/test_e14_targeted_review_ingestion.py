from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_targeted_review_ingestion import write_e14_targeted_review_ingestion


class E14TargetedReviewIngestionTests(unittest.TestCase):
    def test_merges_four_accepts_with_eight_preserved_accepts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _receipts(root / "receipts")
            queue_a, audit_a = _write(root / "a", receipts)
            queue_b, audit_b = _write(root / "b", receipts)
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual(queue_a.read_bytes(), queue_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual("READY_FOR_LABEL_FOUNDATION_GATE", audit["status"])
            self.assertEqual(8, audit["inventory"]["preservedAcceptedCount"])
            self.assertEqual(4, audit["inventory"]["targetedAcceptedCount"])
            self.assertEqual(12, audit["inventory"]["totalAcceptedCount"])
            self.assertTrue(audit["decision"]["labelFoundationGateAuthorized"])
            self.assertTrue(audit["protocol"]["onlyChangedHashesRereviewed"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a", receipts)

    def test_rejects_accept_with_unsupported_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _receipts(root / "receipts")
            path = next(receipts.glob("*.json"))
            receipt = json.loads(path.read_text(encoding="utf-8"))
            receipt["checks"]["boundariesSupported"] = False
            path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "invalid or not independent"):
                _write(root / "invalid", receipts)


def _receipts(root: Path) -> Path:
    root.mkdir()
    queue = json.loads(Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v4.json").read_text())
    for item in queue["dossiers"]:
        if item["reviewStatus"] != "awaiting-targeted-independent-rereview":
            continue
        slug = item["dossierId"].removeprefix("e14-dossier-")
        payload = {
            "schemaVersion": 2,
            "reviewId": f"e14-review-{slug}-test-reviewer",
            "dossierId": item["dossierId"],
            "dossierSha256": item["sha256"],
            "reviewerId": "independent-test-reviewer",
            "reviewerAffiliation": "Test review office",
            "independenceDeclaration": "I did not author the dossier or its evidence pack and reviewed the cited evidence independently.",
            "reviewedAt": "2026-07-14",
            "decision": "accept",
            "rationale": "Independent test rationale confirms the mechanism, both monthly boundaries, sources and counterevidence for this revised dossier.",
            "checks": {
                "sourceLocatorsOpened": True,
                "mechanismClaimSupported": True,
                "boundariesSupported": True,
                "counterEvidenceConsidered": True,
                "noModelOutputUsed": True,
            },
        }
        (root / f"{slug}.json").write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return root


def _write(root: Path, receipts: Path):
    return write_e14_targeted_review_ingestion(
        Path("models/e14-targeted-review-ingestion-contract-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v4.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-targeted-dossier-revision-audit-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        receipts,
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
