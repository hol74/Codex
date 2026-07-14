from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_review_ingestion import write_e14_review_ingestion


class E14ReviewIngestionTests(unittest.TestCase):
    def test_ingests_real_independent_reviews_and_requires_four_revisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_a, audit_a = _write(root / "a")
            queue_b, audit_b = _write(root / "b")
            audit = json.loads(audit_a.read_text(encoding="utf-8"))
            queue = json.loads(queue_a.read_text(encoding="utf-8"))

            self.assertEqual(queue_a.read_bytes(), queue_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual("DOSSIER_REVISIONS_REQUIRED", audit["status"])
            self.assertEqual(12, audit["inventory"]["receiptCount"])
            self.assertEqual(8, audit["inventory"]["acceptedCount"])
            self.assertEqual(0, audit["inventory"]["rejectedCount"])
            self.assertEqual(4, audit["inventory"]["needsRevisionCount"])
            self.assertTrue(audit["decision"]["independentReviewComplete"])
            self.assertFalse(audit["decision"]["allDossiersAccepted"])
            self.assertFalse(audit["decision"]["labelFoundationGateAuthorized"])
            self.assertEqual("REVIEW_COMPLETE_REVISIONS_REQUIRED", queue["status"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_accept_receipt_with_unopened_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = root / "receipts"
            receipts.mkdir()
            source = Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-reviews-v1")
            for path in source.glob("*.json"):
                payload = json.loads(path.read_text(encoding="utf-8"))
                if payload["decision"] == "accept":
                    payload["checks"]["sourceLocatorsOpened"] = False
                    (receipts / path.name).write_text(json.dumps(payload), encoding="utf-8")
                    break
            with self.assertRaisesRegex(DatasetValidationError, "invalid or not independent"):
                _write(root / "invalid", receipts)
            self.assertFalse((root / "invalid" / "queue.json").exists())


def _write(root: Path, receipts: Path | None = None) -> tuple[Path, Path]:
    return write_e14_review_ingestion(
        Path("models/e14-review-ingestion-contract-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-adjudication-readiness-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-review-handoff-audit-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        receipts or Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-reviews-v1"),
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
