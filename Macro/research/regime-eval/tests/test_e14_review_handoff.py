from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_review_handoff import write_e14_review_handoff_bundle


class E14ReviewHandoffTests(unittest.TestCase):
    def test_builds_deterministic_non_ingestible_external_review_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "a")
            second = _write(root / "b")
            report = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("AWAITING_EXTERNAL_REVIEW", report["status"])
            self.assertEqual(12, report["inventory"]["dossierCount"])
            self.assertEqual(12, report["inventory"]["worksheetCount"])
            self.assertEqual(12, report["inventory"]["receiptTemplateCount"])
            self.assertEqual(0, report["inventory"]["independentReviewReceiptCount"])
            self.assertFalse(report["protocol"]["reviewPerformedByBundleGenerator"])
            self.assertFalse(report["decision"]["labelFoundationGateAuthorized"])

            for folder, expected in (("dossiers", 12), ("worksheets", 12), ("receipt-templates", 12)):
                self.assertEqual(expected, len(list((root / "a" / "bundle" / folder).iterdir())))
            template = json.loads(next((root / "a" / "bundle" / "receipt-templates").glob("*.json")).read_text())
            self.assertTrue(template["reviewerId"].startswith("__REQUIRED"))
            self.assertIsNone(template["checks"]["sourceLocatorsOpened"])
            self.assertIn("Templates are intentionally invalid", (root / "a" / "bundle" / "README.md").read_text())

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_queue_dossier_hash_tampering_before_bundle_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = json.loads(Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v2.json").read_text())
            queue["dossiers"][0]["sha256"] = "0" * 64
            queue_path = root / "queue.json"
            queue_path.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            contract = json.loads(Path("models/e14-review-handoff-contract-v1.json").read_text())
            contract["inputHashes"]["reviewQueueSha256"] = hashlib.sha256(queue_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "hash or content"):
                _write(root / "invalid", contract_path, queue_path)
            self.assertFalse((root / "invalid" / "bundle").exists())


def _write(
    root: Path,
    contract: Path = Path("models/e14-review-handoff-contract-v1.json"),
    queue: Path = Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v2.json"),
) -> Path:
    return write_e14_review_handoff_bundle(
        contract,
        queue,
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-adjudication-readiness-v2.json"),
        Path("models/e14-independent-review-schema-v1.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2"),
        root / "bundle",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
