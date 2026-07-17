from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers"); MODELS = Path("models")


class E14FdicArchiveAtomicProducerV5IndependentReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads((DATA / "e14-fdic-archive-atomic-producer-v5-independent-review-v1.json").read_text())
        self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-v5-independent-review-schema-v1.json").read_text())

    def test_closed_schema(self) -> None:
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_hashes_are_exact(self) -> None:
        expected = {
            "implementationContract": MODELS / "e14-fdic-archive-atomic-producer-v5-implementation-contract-v1.json", "blockedReview": DATA / "e14-fdic-archive-atomic-producer-v4-independent-review-v1.json", "plan": MODELS / "e14-fdic-archive-atomic-producer-v5-plan-v1.json", "auditSchema": MODELS / "e14-fdic-archive-atomic-producer-v5-audit-schema-v1.json", "audit": DATA / "e14-fdic-archive-atomic-producer-v5-audit-v1.json", "contractVerifier": Path("regime_eval/e14_fdic_archive_contract_verifier_v5.py"), "producer": Path("regime_eval/e14_fdic_archive_atomic_producer_v5.py"), "testRunnerTrust": Path("regime_eval/e14_test_runner_trust.py"), "testRunner": Path("regime_eval/e14_hash_bound_test_runner_v3.py"), "platformQualification": Path("regime_eval/e14_nofollow_platform_qualification.py"), "producerTests": Path("tests/test_e14_fdic_archive_atomic_producer_v5.py"), "auditTests": Path("tests/test_e14_fdic_archive_atomic_producer_v5_audit.py"), "collectorReceiptSchema": MODELS / "e14-fdic-collector-receipt-schema-v2.json", "ledgerSchema": MODELS / "e14-fdic-archive-receipt-ledger-schema-v1.json", "bundleAuditSchema": MODELS / "e14-fdic-archive-producer-v5-bundle-audit-schema-v1.json", "runtimeTestContract": MODELS / "e14-fdic-archive-producer-v5-runtime-test-contract-v1.json", "testReceipt": DATA / "e14-fdic-archive-atomic-producer-v5-test-receipt-v1.json", "testTranscript": DATA / "e14-fdic-archive-atomic-producer-v5-test-transcript-v1.txt", "projectConfiguration": Path("pyproject.toml"), "reviewSchema": MODELS / "e14-fdic-archive-atomic-producer-v5-independent-review-schema-v1.json"
        }
        for key, path in expected.items(): self.assertEqual(self.receipt["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_needs_changes_keeps_downstream_closed(self) -> None:
        self.assertEqual("needs_changes", self.receipt["decision"]); self.assertEqual(4, len(self.receipt["blockingFindings"]))
        self.assertTrue(self.receipt["assessments"]["testReceiptSignerSecretUnexposed"])
        self.assertFalse(self.receipt["assessments"]["crossParentReplayPrevented"])
        self.assertFalse(self.receipt["assessments"]["ledgerTamperRollbackPrevented"])
        self.assertTrue(self.receipt["assessments"]["downstreamStillClosed"])


if __name__ == "__main__": unittest.main()
