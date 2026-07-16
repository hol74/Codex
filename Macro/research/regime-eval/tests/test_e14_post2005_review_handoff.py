from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_review_handoff import write_e14_post2005_review_handoff


class E14Post2005ReviewHandoffTests(unittest.TestCase):
    def test_builds_deterministic_bundle_without_performing_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "a")
            second = _write(root / "b")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual("POST_2005_EXTERNAL_REVIEW_HANDOFF_READY", audit["status"])
            self.assertEqual(2, audit["inventory"]["dossierCount"])
            self.assertEqual(2, audit["inventory"]["receiptTemplateCount"])
            self.assertEqual(0, audit["inventory"]["independentReviewReceiptCount"])
            self.assertFalse(audit["protocol"]["reviewPerformedByBundleGenerator"])
            self.assertFalse(audit["decision"]["scopeActivationAuthorized"])
            for folder, count in (("dossiers", 2), ("worksheets", 2), ("receipt-templates", 2)):
                self.assertEqual(count, len(list((root / "a" / "bundle" / folder).iterdir())))
            template = json.loads(next((root / "a" / "bundle" / "receipt-templates").glob("*.json")).read_text())
            self.assertEqual(2, template["schemaVersion"])
            self.assertTrue(template["reviewerId"].startswith("__REQUIRED"))
            self.assertIsNone(template["checks"]["sourceLocatorsOpened"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_dossier_hash_tampering_before_bundle_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = json.loads(_queue().read_text(encoding="utf-8"))
            queue["dossiers"][0]["sha256"] = "0" * 64
            unsafe_queue = root / "queue.json"
            unsafe_queue.write_text(json.dumps(queue), encoding="utf-8")
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["inputHashes"]["reviewQueueSha256"] = hashlib.sha256(unsafe_queue.read_bytes()).hexdigest()
            unsafe_contract = root / "contract.json"
            unsafe_contract.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "hash or content"):
                _write(root / "unsafe", unsafe_contract, unsafe_queue)
            self.assertFalse((root / "unsafe" / "bundle").exists())


def _contract() -> Path:
    return Path("models/e14-post2005-review-handoff-contract-v1.json")


def _queue() -> Path:
    return Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-review-queue-v1.json")


def _write(root: Path, contract: Path | None = None, queue: Path | None = None) -> Path:
    return write_e14_post2005_review_handoff(
        contract or _contract(),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-taxonomy-proposal-v1.json"),
        queue or _queue(),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-taxonomy-proposal-audit-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-dossiers-v1"),
        root / "bundle",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
