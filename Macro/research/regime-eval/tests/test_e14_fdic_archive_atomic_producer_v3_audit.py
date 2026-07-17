from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV3AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads((DATA / "e14-fdic-archive-atomic-producer-v3-audit-v1.json").read_text())
        self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-v3-audit-schema-v1.json").read_text())

    def test_closed_schema(self) -> None: _validate_schema_value(self.audit, self.schema, self.schema, "$")

    def test_all_hashes_and_execution_receipt_are_exact(self) -> None:
        expected_inputs = {"contractSha256": MODELS / "e14-fdic-archive-atomic-producer-v3-implementation-contract-v1.json", "blockedReviewSha256": DATA / "e14-fdic-archive-atomic-producer-v2-independent-review-v1.json", "planSha256": MODELS / "e14-fdic-archive-atomic-producer-v3-plan-v1.json", "envelopeSchemaSha256": MODELS / "e14-fdic-response-envelope-schema-v1.json", "bundleAuditSchemaSha256": MODELS / "e14-fdic-archive-producer-v3-bundle-audit-schema-v1.json"}
        for key, path in expected_inputs.items(): self.assertEqual(self.audit["inputs"][key], _sha(path))
        expected_impl = {"moduleSha256": Path("regime_eval/e14_fdic_archive_atomic_producer_v3.py"), "testRunnerSha256": Path("regime_eval/e14_hash_bound_test_runner.py"), "testsSha256": Path("tests/test_e14_fdic_archive_atomic_producer_v3.py")}
        for key, path in expected_impl.items(): self.assertEqual(self.audit["implementation"][key], _sha(path))
        receipt_path = DATA / "e14-fdic-archive-atomic-producer-v3-test-receipt-v1.json"
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(self.audit["testReceipt"]["sha256"], _sha(receipt_path))
        self.assertTrue(receipt["passed"]); self.assertEqual(6, receipt["testsRun"])
        self.assertEqual(self.audit["implementation"]["testsSha256"], receipt["testArtifacts"][0]["sha256"])

    def test_downstream_closed(self) -> None:
        self.assertEqual(0, self.audit["protocol"]["networkRequestsMade"])
        self.assertFalse(self.audit["decision"]["discoveryCatalogAuthorized"])
        self.assertFalse(self.audit["decision"]["executionGateAuthorized"])


def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
if __name__ == "__main__": unittest.main()
