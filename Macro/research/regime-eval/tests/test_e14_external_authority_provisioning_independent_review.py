from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14ExternalAuthorityProvisioningIndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((DATA / "e14-external-authority-provisioning-independent-review-v1.json").read_text())
        self.schema = json.loads((MODELS / "e14-external-authority-provisioning-independent-review-schema-v1.json").read_text())

    def test_closed_schema(self):
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_hashes_are_exact(self):
        expected = {
            "acceptedBoundaryReview": DATA / "e14-fdic-archive-atomic-producer-v7-independent-review-v1.json",
            "preregistrationSchema": MODELS / "e14-external-authority-provisioning-preregistration-schema-v1.json",
            "provisioningPlan": MODELS / "e14-external-authority-provisioning-plan-v1.json",
            "preregistrationAuditSchema": MODELS / "e14-external-authority-provisioning-preregistration-audit-schema-v1.json",
            "preregistrationAudit": DATA / "e14-external-authority-provisioning-preregistration-audit-v1.json",
            "authorityContractSchema": MODELS / "e14-external-monotonic-authority-contract-schema-v1.json",
            "authorityVerifier": Path("regime_eval/e14_external_monotonic_authority.py"),
            "producerV7": Path("regime_eval/e14_fdic_archive_atomic_producer_v7.py"),
            "tests": Path("tests/test_e14_external_authority_provisioning_preregistration.py"),
            "projectConfiguration": Path("pyproject.toml"),
            "reviewSchema": MODELS / "e14-external-authority-provisioning-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_needs_changes_keeps_everything_closed(self):
        self.assertEqual("needs_changes", self.receipt["decision"])
        self.assertEqual(2, len(self.receipt["blockingFindings"]))
        self.assertFalse(self.receipt["assessments"]["currentCapabilityCreated"])
        self.assertFalse(self.receipt["assessments"]["networkAuthorized"])
        self.assertFalse(self.receipt["assessments"]["downstreamAuthorized"])


if __name__ == "__main__":
    unittest.main()
