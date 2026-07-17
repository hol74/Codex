from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerIndependentReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads((DATA / "e14-fdic-archive-atomic-producer-independent-review-v1.json").read_text(encoding="utf-8"))
        self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-independent-review-schema-v1.json").read_text(encoding="utf-8"))

    def test_receipt_validates_against_closed_schema(self) -> None:
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_reviewed_hashes_are_exact(self) -> None:
        expected = {
            "contractSha256": MODELS / "e14-fdic-archive-atomic-producer-contract-v1.json",
            "blockedReviewSha256": DATA / "e14-fdic-archive-evidence-remediation-independent-review-v1.json",
            "producerPlanSha256": MODELS / "e14-fdic-archive-atomic-producer-plan-v1.json",
            "sourceCatalogSha256": DATA / "e14-fdic-publication-metadata-requests-v1.json",
            "sourceCatalogSchemaSha256": MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json",
            "evidenceManifestSchemaSha256": MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json",
            "mapSchemaV3Sha256": MODELS / "e14-fdic-archive-quarter-map-schema-v3.json",
            "mapAuditSchemaV3Sha256": MODELS / "e14-fdic-archive-quarter-map-audit-schema-v3.json",
            "producerAuditSchemaSha256": MODELS / "e14-fdic-archive-atomic-producer-audit-schema-v1.json",
            "producerAuditSha256": DATA / "e14-fdic-archive-atomic-producer-audit-v1.json",
            "implementationSha256": Path("regime_eval/e14_fdic_archive_atomic_producer.py"),
            "cliSha256": Path("regime_eval/cli.py"),
            "testsSha256": Path("tests/test_e14_fdic_archive_atomic_producer.py"),
            "reviewSchemaSha256": MODELS / "e14-fdic-archive-atomic-producer-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt[key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_needs_changes_keeps_downstream_closed(self) -> None:
        self.assertEqual("needs_changes", self.receipt["decision"])
        self.assertTrue(self.receipt["assessments"]["atomicPublicationFailClosed"])
        self.assertFalse(self.receipt["assessments"]["sourceCatalogObjectAndRawBytesBound"])
        self.assertFalse(self.receipt["assessments"]["confirmedAbsenceSemanticsAdequate"])
        self.assertFalse(self.receipt["assessments"]["testMatrixExecutedHonestly"])
        self.assertFalse(self.receipt["assessments"]["discoveryCatalogDesignAuthorized"])
        self.assertEqual(6, len(self.receipt["blockingFindings"]))
        self.assertEqual(6, sum(not item["passed"] for item in self.receipt["probeResults"]))


if __name__ == "__main__":
    unittest.main()
