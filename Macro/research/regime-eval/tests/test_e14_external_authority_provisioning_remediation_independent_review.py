from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14ExternalAuthorityProvisioningRemediationIndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((DATA / "e14-external-authority-provisioning-remediation-independent-review-v1.json").read_text())
        self.schema = json.loads((MODELS / "e14-external-authority-provisioning-remediation-independent-review-schema-v1.json").read_text())

    def test_closed_schema(self):
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_hashes_are_exact(self):
        expected = {
            "blockedDesignReview": DATA / "e14-external-authority-provisioning-independent-review-v1.json",
            "operationalProtocol": MODELS / "e14-external-authority-operational-protocol-v1.json",
            "operationalProtocolSchema": MODELS / "e14-external-authority-operational-protocol-schema-v1.json",
            "remediationSchema": MODELS / "e14-external-authority-provisioning-remediation-schema-v2.json",
            "remediationPlan": MODELS / "e14-external-authority-provisioning-plan-v2.json",
            "remediationAuditSchema": MODELS / "e14-external-authority-provisioning-remediation-audit-schema-v2.json",
            "remediationAudit": DATA / "e14-external-authority-provisioning-remediation-audit-v2.json",
            "tests": Path("tests/test_e14_external_authority_provisioning_remediation.py"),
            "acceptedBoundaryReview": DATA / "e14-fdic-archive-atomic-producer-v7-independent-review-v1.json",
            "authorityVerifier": Path("regime_eval/e14_external_monotonic_authority.py"),
            "producerV7": Path("regime_eval/e14_fdic_archive_atomic_producer_v7.py"),
            "projectConfiguration": Path("pyproject.toml"),
            "reviewSchema": MODELS / "e14-external-authority-provisioning-remediation-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_accept_closes_design_without_opening_capability(self):
        self.assertEqual("accept", self.receipt["decision"])
        self.assertEqual([], self.receipt["blockingFindings"])
        assessments = self.receipt["assessments"]
        self.assertTrue(assessments["designCompleteSafelyBlocked"])
        self.assertFalse(assessments["providerSelected"])
        self.assertFalse(assessments["adapterImplemented"])
        self.assertFalse(assessments["publicationAuthorized"])
        self.assertFalse(assessments["downstreamAuthorized"])


if __name__ == "__main__":
    unittest.main()
