from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value
from regime_eval.e14_test_runner_trust import verify_pinned_test_receipt


DATA = Path("../../data/historical-real-v12-2008-2025/challengers"); MODELS = Path("models")


class E14FdicArchiveAtomicProducerV6AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads((DATA / "e14-fdic-archive-atomic-producer-v6-audit-v1.json").read_text()); self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-v6-audit-schema-v1.json").read_text())

    def test_closed_schema(self) -> None: _validate_schema_value(self.audit, self.schema, self.schema, "$")

    def test_hashes_are_exact(self) -> None:
        expected = {"implementationContract": MODELS / "e14-fdic-archive-atomic-producer-v6-implementation-contract-v1.json", "blockedReview": DATA / "e14-fdic-archive-atomic-producer-v5-independent-review-v1.json", "plan": MODELS / "e14-fdic-archive-atomic-producer-v6-plan-v1.json", "producer": Path("regime_eval/e14_fdic_archive_atomic_producer_v6.py"), "tests": Path("tests/test_e14_fdic_archive_atomic_producer_v6.py"), "runtimeValidationContract": MODELS / "e14-fdic-archive-producer-v5-runtime-test-contract-v1.json", "testReceipt": DATA / "e14-fdic-archive-atomic-producer-v6-test-receipt-v1.json", "testTranscript": DATA / "e14-fdic-archive-atomic-producer-v6-test-transcript-v1.txt", "projectConfiguration": Path("pyproject.toml")}
        for key, path in expected.items(): self.assertEqual(self.audit["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_pinned_receipt_and_downstream_closed(self) -> None:
        receipt = DATA / "e14-fdic-archive-atomic-producer-v6-test-receipt-v1.json"; transcript = DATA / "e14-fdic-archive-atomic-producer-v6-test-transcript-v1.txt"
        verify_pinned_test_receipt(receipt.read_bytes(), transcript.read_bytes(), "tests.test_e14_fdic_archive_atomic_producer_v6", "tests/test_e14_fdic_archive_atomic_producer_v6.py")
        self.assertIn(b"Ran 5 tests", transcript.read_bytes()); self.assertEqual(0, self.audit["protocol"]["networkRequestsMade"]); self.assertFalse(self.audit["decision"]["discoveryCatalogAuthorized"])


if __name__ == "__main__": unittest.main()
