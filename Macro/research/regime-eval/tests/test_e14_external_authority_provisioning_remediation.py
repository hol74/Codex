from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_external_monotonic_authority import PINNED_PRODUCTION_AUTHORITIES
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14ExternalAuthorityProvisioningRemediationTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((MODELS / "e14-external-authority-provisioning-plan-v2.json").read_text())
        self.plan_schema = json.loads((MODELS / "e14-external-authority-provisioning-remediation-schema-v2.json").read_text())
        self.protocol = json.loads((MODELS / "e14-external-authority-operational-protocol-v1.json").read_text())
        self.protocol_schema = json.loads((MODELS / "e14-external-authority-operational-protocol-schema-v1.json").read_text())
        self.audit = json.loads((DATA / "e14-external-authority-provisioning-remediation-audit-v2.json").read_text())
        self.audit_schema = json.loads((MODELS / "e14-external-authority-provisioning-remediation-audit-schema-v2.json").read_text())

    def test_closed_plan_protocol_and_audit(self):
        _validate_schema_value(self.plan, self.plan_schema, self.plan_schema, "$")
        _validate_schema_value(self.protocol, self.protocol_schema, self.protocol_schema, "$")
        _validate_schema_value(self.audit, self.audit_schema, self.audit_schema, "$")

    def test_every_evidence_class_is_individually_mandatory(self):
        self.assertEqual(10, len(self.plan["evidenceRequirements"]))
        for key in self.plan["evidenceRequirements"]:
            with self.subTest(key=key):
                mutated = copy.deepcopy(self.plan)
                del mutated["evidenceRequirements"][key]
                with self.assertRaises(DatasetValidationError):
                    _validate_schema_value(mutated, self.plan_schema, self.plan_schema, "$")

    def test_operational_protocol_is_exact_and_non_omissible(self):
        for key in self.protocol["protocol"]:
            with self.subTest(key=key):
                mutated = copy.deepcopy(self.protocol)
                del mutated["protocol"][key]
                with self.assertRaises(DatasetValidationError):
                    _validate_schema_value(mutated, self.protocol_schema, self.protocol_schema, "$")
        mutated = copy.deepcopy(self.protocol)
        del mutated["protocol"]["operations"]["compareAndSwapPending"]["precondition"]
        with self.assertRaises(DatasetValidationError):
            _validate_schema_value(mutated, self.protocol_schema, self.protocol_schema, "$")

    def test_hash_bindings_are_exact(self):
        expected = {
            "acceptedBoundaryReview": DATA / "e14-fdic-archive-atomic-producer-v7-independent-review-v1.json",
            "blockedDesignReview": DATA / "e14-external-authority-provisioning-independent-review-v1.json",
            "remediationSchema": MODELS / "e14-external-authority-provisioning-remediation-schema-v2.json",
            "remediationPlan": MODELS / "e14-external-authority-provisioning-plan-v2.json",
            "operationalProtocolSchema": MODELS / "e14-external-authority-operational-protocol-schema-v1.json",
            "operationalProtocol": MODELS / "e14-external-authority-operational-protocol-v1.json",
            "authorityVerifier": Path("regime_eval/e14_external_monotonic_authority.py"),
            "producerV7": Path("regime_eval/e14_fdic_archive_atomic_producer_v7.py"),
            "projectConfiguration": Path("pyproject.toml"),
        }
        for key, path in expected.items():
            self.assertEqual(self.audit["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_conformance_matrix_covers_reviewed_failure_modes(self):
        tests = self.protocol["protocol"]["mandatoryConformanceTests"]
        self.assertEqual(14, len(tests))
        self.assertTrue(all(tests.values()))
        for required in ("casRaceSingleWinner", "postRenameCrashRecovery", "crossVolumeFailsBeforeCas", "directoryDurabilityFailureBlocksCommit", "symlinkSwapRejected", "pidReuseDoesNotStealLock"):
            self.assertIn(required, tests)

    def test_remediation_creates_no_current_capability(self):
        self.assertEqual({}, PINNED_PRODUCTION_AUTHORITIES)
        self.assertEqual(0, self.audit["protocol"]["networkRequestsMade"])
        self.assertEqual(0, self.audit["protocol"]["authoritiesProvisioned"])
        for key, value in self.audit["decision"].items():
            if key.endswith("Authorized") and key != "independentRemediationReviewAuthorized":
                self.assertFalse(value, key)


if __name__ == "__main__":
    unittest.main()
