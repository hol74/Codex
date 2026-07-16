from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicPublicationMetadataRequestCatalogIndependentReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads((DATA / "e14-fdic-publication-metadata-request-catalog-independent-review-v1.json").read_text(encoding="utf-8"))
        self.schema = json.loads((MODELS / "e14-fdic-publication-metadata-request-catalog-independent-review-schema-v1.json").read_text(encoding="utf-8"))

    def test_receipt_validates_against_closed_schema(self) -> None:
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_reviewed_hashes_are_exact(self) -> None:
        expected = {
            "contractSha256": MODELS / "e14-fdic-publication-metadata-request-catalog-contract-v1.json",
            "planSha256": MODELS / "e14-fdic-publication-metadata-request-catalog-plan-v1.json",
            "requestCatalogSha256": DATA / "e14-fdic-publication-metadata-requests-v1.json",
            "auditSha256": DATA / "e14-fdic-publication-metadata-request-catalog-audit-v1.json",
            "catalogSchemaSha256": MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json",
            "implementationSha256": Path("regime_eval/e14_fdic_publication_metadata_request_catalog.py"),
            "reviewSchemaSha256": MODELS / "e14-fdic-publication-metadata-request-catalog-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt[key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_needs_changes_keeps_execution_gate_closed(self) -> None:
        self.assertEqual("needs_changes", self.receipt["decision"])
        self.assertFalse(self.receipt["assessments"]["archiveExpansionValuesFrozen"])
        self.assertFalse(self.receipt["assessments"]["archiveDiscoveryDeterministic"])
        self.assertFalse(self.receipt["assessments"]["replacementExecutionGateAuthorized"])
        self.assertEqual(2, len(self.receipt["blockingFindings"]))


if __name__ == "__main__":
    unittest.main()
