from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveEvidenceRemediationIndependentReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads((DATA / "e14-fdic-archive-evidence-remediation-independent-review-v1.json").read_text(encoding="utf-8"))
        self.schema = json.loads((MODELS / "e14-fdic-archive-evidence-remediation-independent-review-schema-v1.json").read_text(encoding="utf-8"))

    def test_receipt_validates_against_closed_schema(self) -> None:
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_reviewed_hashes_are_exact(self) -> None:
        expected = {
            "contractSha256": MODELS / "e14-fdic-archive-evidence-remediation-contract-v1.json",
            "blockedReviewSha256": DATA / "e14-fdic-archive-evidence-independent-review-v1.json",
            "remediationPlanSha256": MODELS / "e14-fdic-archive-evidence-remediation-plan-v2.json",
            "evidenceManifestSchemaSha256": MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json",
            "mapSchemaV3Sha256": MODELS / "e14-fdic-archive-quarter-map-schema-v3.json",
            "mapAuditSchemaV3Sha256": MODELS / "e14-fdic-archive-quarter-map-audit-schema-v3.json",
            "remediationAuditSchemaSha256": MODELS / "e14-fdic-archive-evidence-remediation-audit-schema-v1.json",
            "remediationAuditSha256": DATA / "e14-fdic-archive-evidence-remediation-audit-v1.json",
            "implementationSha256": Path("regime_eval/e14_fdic_archive_evidence_remediation.py"),
            "testsSha256": Path("tests/test_e14_fdic_archive_evidence_remediation.py"),
            "reviewSchemaSha256": MODELS / "e14-fdic-archive-evidence-remediation-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt[key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_needs_changes_keeps_discovery_closed(self) -> None:
        self.assertEqual("needs_changes", self.receipt["decision"])
        self.assertTrue(self.receipt["assessments"]["exact79RosterEnforced"])
        self.assertFalse(self.receipt["assessments"]["rawBytesExistenceVerified"])
        self.assertFalse(self.receipt["assessments"]["sourceCatalogUrlsBound"])
        self.assertFalse(self.receipt["assessments"]["schemaAndSemanticValidationIntegrated"])
        self.assertFalse(self.receipt["assessments"]["partialPublicationFailClosed"])
        self.assertFalse(self.receipt["assessments"]["discoveryCatalogDesignAuthorized"])
        self.assertEqual(5, len(self.receipt["blockingFindings"]))


if __name__ == "__main__":
    unittest.main()
