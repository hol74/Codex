from __future__ import annotations

import base64
import hashlib
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value

DATA = Path("../../data/historical-real-v12-2008-2025/challengers"); MODELS = Path("models")

class E14FdicArchiveAtomicProducerV4AuditTests(unittest.TestCase):
    def setUp(self):
        self.audit = json.loads((DATA / "e14-fdic-archive-atomic-producer-v4-audit-v1.json").read_text()); self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-v4-audit-schema-v1.json").read_text())
    def test_closed_schema(self): _validate_schema_value(self.audit, self.schema, self.schema, "$")
    def test_hashes_and_signed_test_receipt(self):
        expected = {"implementationContract": MODELS / "e14-fdic-archive-atomic-producer-v4-implementation-contract-v1.json", "blockedReview": DATA / "e14-fdic-archive-atomic-producer-v3-independent-review-v1.json", "plan": MODELS / "e14-fdic-archive-atomic-producer-v4-plan-v1.json", "contractVerifier": Path("regime_eval/e14_fdic_archive_contract_verifier.py"), "producer": Path("regime_eval/e14_fdic_archive_atomic_producer_v4.py"), "testRunner": Path("regime_eval/e14_hash_bound_test_runner_v2.py"), "tests": Path("tests/test_e14_fdic_archive_atomic_producer_v4.py"), "envelopeSchema": MODELS / "e14-fdic-response-envelope-schema-v2.json", "collectorReceiptSchema": MODELS / "e14-fdic-collector-receipt-schema-v1.json", "bundleAuditSchema": MODELS / "e14-fdic-archive-producer-v4-bundle-audit-schema-v1.json", "runtimeTestContract": MODELS / "e14-fdic-archive-producer-v4-runtime-test-contract-v1.json", "projectConfiguration": Path("pyproject.toml")}
        for key, path in expected.items(): self.assertEqual(self.audit["hashes"][key], _sha(path.read_bytes()), key)
        receipt_path = DATA / "e14-fdic-archive-atomic-producer-v4-test-receipt-v1.json"; transcript_path = DATA / "e14-fdic-archive-atomic-producer-v4-test-transcript-v1.txt"; receipt = json.loads(receipt_path.read_text()); unsigned = dict(receipt); signature = unsigned.pop("signatureBase64")
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(receipt["publicKeyHex"])).verify(base64.b64decode(signature), json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode())
        self.assertEqual(self.audit["testExecution"]["receiptSha256"], _sha(receipt_path.read_bytes())); self.assertEqual(receipt["transcript"]["sha256"], _sha(transcript_path.read_bytes())); self.assertIn(b"Ran 6 tests", transcript_path.read_bytes())
    def test_downstream_closed(self):
        self.assertEqual(0, self.audit["protocol"]["networkRequestsMade"]); self.assertFalse(self.audit["decision"]["discoveryCatalogAuthorized"])
def _sha(raw): return hashlib.sha256(raw).hexdigest()
if __name__ == "__main__": unittest.main()
