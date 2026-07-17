from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV7IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads(
            (DATA / "e14-fdic-archive-atomic-producer-v7-independent-review-v1.json").read_text()
        )
        self.schema = json.loads(
            (MODELS / "e14-fdic-archive-atomic-producer-v7-independent-review-schema-v1.json").read_text()
        )

    def test_closed_schema(self):
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_hashes_are_exact(self):
        expected = {
            "blockedReview": DATA / "e14-fdic-archive-atomic-producer-v6-independent-review-v1.json",
            "authoritySchema": MODELS / "e14-external-monotonic-authority-contract-schema-v1.json",
            "plan": MODELS / "e14-fdic-archive-atomic-producer-v7-plan-v1.json",
            "auditSchema": MODELS / "e14-fdic-archive-atomic-producer-v7-audit-schema-v1.json",
            "audit": DATA / "e14-fdic-archive-atomic-producer-v7-audit-v1.json",
            "authorityVerifier": Path("regime_eval/e14_external_monotonic_authority.py"),
            "producer": Path("regime_eval/e14_fdic_archive_atomic_producer_v7.py"),
            "producerTests": Path("tests/test_e14_fdic_archive_atomic_producer_v7.py"),
            "auditTests": Path("tests/test_e14_fdic_archive_atomic_producer_v7_audit.py"),
            "projectConfiguration": Path("pyproject.toml"),
            "reviewSchema": MODELS / "e14-fdic-archive-atomic-producer-v7-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_accept_closes_e14_7_safely_blocked(self):
        assessments = self.receipt["assessments"]
        self.assertEqual("accept", self.receipt["decision"])
        self.assertEqual([], self.receipt["blockingFindings"])
        self.assertTrue(assessments["safeBlockedClosureSupported"])
        self.assertTrue(assessments["publishRemainsBlockedAfterAuthorityVerification"])
        self.assertFalse(assessments["externalProvisioningAuthorized"])
        self.assertFalse(assessments["providerNetworkCaptureAuthorized"])
        self.assertFalse(assessments["downstreamAuthorized"])


if __name__ == "__main__":
    unittest.main()
