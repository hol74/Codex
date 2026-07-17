from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value
from regime_eval.e14_test_runner_trust import PINNED_TEST_RUNNER_PUBLIC_KEYS, verify_pinned_test_receipt


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV5AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads((DATA / "e14-fdic-archive-atomic-producer-v5-audit-v1.json").read_text())
        self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-v5-audit-schema-v1.json").read_text())

    def test_closed_schema(self) -> None:
        _validate_schema_value(self.audit, self.schema, self.schema, "$")

    def test_hashes_are_exact(self) -> None:
        expected = {
            "implementationContract": MODELS / "e14-fdic-archive-atomic-producer-v5-implementation-contract-v1.json",
            "blockedReview": DATA / "e14-fdic-archive-atomic-producer-v4-independent-review-v1.json",
            "plan": MODELS / "e14-fdic-archive-atomic-producer-v5-plan-v1.json",
            "contractVerifier": Path("regime_eval/e14_fdic_archive_contract_verifier_v5.py"),
            "producer": Path("regime_eval/e14_fdic_archive_atomic_producer_v5.py"),
            "testRunnerTrust": Path("regime_eval/e14_test_runner_trust.py"),
            "testRunner": Path("regime_eval/e14_hash_bound_test_runner_v3.py"),
            "platformQualification": Path("regime_eval/e14_nofollow_platform_qualification.py"),
            "tests": Path("tests/test_e14_fdic_archive_atomic_producer_v5.py"),
            "collectorReceiptSchema": MODELS / "e14-fdic-collector-receipt-schema-v2.json",
            "ledgerSchema": MODELS / "e14-fdic-archive-receipt-ledger-schema-v1.json",
            "bundleAuditSchema": MODELS / "e14-fdic-archive-producer-v5-bundle-audit-schema-v1.json",
            "runtimeTestContract": MODELS / "e14-fdic-archive-producer-v5-runtime-test-contract-v1.json",
            "projectConfiguration": Path("pyproject.toml"),
        }
        for key, path in expected.items():
            self.assertEqual(self.audit["hashes"][key], _sha(path.read_bytes()), key)

    def test_receipt_uses_only_externally_pinned_key(self) -> None:
        receipt_path = DATA / "e14-fdic-archive-atomic-producer-v5-test-receipt-v1.json"; transcript_path = DATA / "e14-fdic-archive-atomic-producer-v5-test-transcript-v1.txt"
        raw = receipt_path.read_bytes(); receipt = json.loads(raw)
        self.assertNotIn("publicKeyHex", receipt); self.assertIn(receipt["signerId"], PINNED_TEST_RUNNER_PUBLIC_KEYS)
        verified = verify_pinned_test_receipt(raw, transcript_path.read_bytes(), "tests.test_e14_fdic_archive_atomic_producer_v5", "tests/test_e14_fdic_archive_atomic_producer_v5.py")
        self.assertTrue(verified["passed"]); self.assertIn(b"Ran 8 tests", transcript_path.read_bytes())
        self.assertEqual(self.audit["testExecution"]["receiptSha256"], _sha(raw)); self.assertEqual(self.audit["testExecution"]["transcriptSha256"], _sha(transcript_path.read_bytes()))

    def test_downstream_and_network_stay_closed(self) -> None:
        self.assertEqual(0, self.audit["protocol"]["networkRequestsMade"])
        self.assertEqual(0, self.audit["protocol"]["productionContractsPinned"])
        self.assertFalse(self.audit["decision"]["discoveryCatalogAuthorized"])
        self.assertFalse(self.audit["decision"]["executionGateAuthorized"])


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__": unittest.main()
