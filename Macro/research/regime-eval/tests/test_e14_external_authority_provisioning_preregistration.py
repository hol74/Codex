from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_external_monotonic_authority import PINNED_PRODUCTION_AUTHORITIES
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14ExternalAuthorityProvisioningPreregistrationTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((MODELS / "e14-external-authority-provisioning-plan-v1.json").read_text())
        self.plan_schema = json.loads(
            (MODELS / "e14-external-authority-provisioning-preregistration-schema-v1.json").read_text()
        )
        self.audit = json.loads(
            (DATA / "e14-external-authority-provisioning-preregistration-audit-v1.json").read_text()
        )
        self.audit_schema = json.loads(
            (MODELS / "e14-external-authority-provisioning-preregistration-audit-schema-v1.json").read_text()
        )

    def test_closed_plan_and_audit_schemas(self):
        _validate_schema_value(self.plan, self.plan_schema, self.plan_schema, "$")
        _validate_schema_value(self.audit, self.audit_schema, self.audit_schema, "$")

    def test_hash_bindings_are_exact(self):
        expected = {
            "acceptedBoundaryReview": DATA / "e14-fdic-archive-atomic-producer-v7-independent-review-v1.json",
            "authorityContractSchema": MODELS / "e14-external-monotonic-authority-contract-schema-v1.json",
            "preregistrationSchema": MODELS / "e14-external-authority-provisioning-preregistration-schema-v1.json",
            "provisioningPlan": MODELS / "e14-external-authority-provisioning-plan-v1.json",
            "authorityVerifier": Path("regime_eval/e14_external_monotonic_authority.py"),
            "producerV7": Path("regime_eval/e14_fdic_archive_atomic_producer_v7.py"),
            "projectConfiguration": Path("pyproject.toml"),
        }
        for key, path in expected.items():
            self.assertEqual(self.audit["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_preregistration_does_not_create_capability(self):
        self.assertEqual({}, PINNED_PRODUCTION_AUTHORITIES)
        self.assertEqual(0, self.audit["protocol"]["networkRequestsMade"])
        self.assertEqual(0, self.audit["protocol"]["authoritiesProvisioned"])
        self.assertFalse(self.audit["decision"]["externalProvisioningAuthorized"])
        self.assertFalse(self.audit["decision"]["adapterImplementationAuthorized"])
        self.assertFalse(self.audit["decision"]["productionPublicationAuthorized"])
        self.assertFalse(self.audit["decision"]["downstreamAuthorized"])

    def test_only_independent_design_review_is_open(self):
        self.assertTrue(self.audit["decision"]["independentReviewAuthorized"])
        self.assertEqual("E14.8a", self.audit["decision"]["nextAllowedAction"].split()[0])
        self.assertEqual(10, len(self.plan["requiredProvisioningEvidence"]))
        self.assertTrue(all(self.plan["requiredCapabilities"].values()))


if __name__ == "__main__":
    unittest.main()
