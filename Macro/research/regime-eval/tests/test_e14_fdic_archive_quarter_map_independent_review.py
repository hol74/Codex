from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveQuarterMapIndependentReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads((DATA / "e14-fdic-archive-quarter-map-independent-review-v1.json").read_text(encoding="utf-8"))
        self.schema = json.loads((MODELS / "e14-fdic-archive-quarter-map-independent-review-schema-v1.json").read_text(encoding="utf-8"))

    def test_receipt_validates_against_closed_schema(self) -> None:
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_reviewed_hashes_are_exact(self) -> None:
        expected = {
            "contractSha256": MODELS / "e14-fdic-archive-quarter-map-contract-v1.json",
            "mapSha256": DATA / "e14-fdic-archive-quarter-map-v1.json",
            "auditSha256": DATA / "e14-fdic-archive-quarter-map-audit-v1.json",
            "planSha256": MODELS / "e14-fdic-archive-quarter-map-plan-v1.json",
            "mapSchemaSha256": MODELS / "e14-fdic-archive-quarter-map-schema-v1.json",
            "auditSchemaSha256": MODELS / "e14-fdic-archive-quarter-map-audit-schema-v1.json",
            "implementationSha256": Path("regime_eval/e14_fdic_archive_quarter_map.py"),
            "reviewSchemaSha256": MODELS / "e14-fdic-archive-quarter-map-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt[key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_needs_changes_keeps_replacement_gate_closed(self) -> None:
        self.assertEqual("needs_changes", self.receipt["decision"])
        self.assertTrue(self.receipt["assessments"]["runtimeArchiveDiscoveryEliminated"])
        self.assertFalse(self.receipt["assessments"]["unresolvedClaimsEvidenceBound"])
        self.assertFalse(self.receipt["assessments"]["archiveMappingOperationallyComplete"])
        self.assertFalse(self.receipt["assessments"]["replacementExecutionGateAuthorized"])
        self.assertEqual(4, len(self.receipt["blockingFindings"]))


if __name__ == "__main__":
    unittest.main()
