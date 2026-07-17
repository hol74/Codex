from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV2IndependentReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads((DATA / "e14-fdic-archive-atomic-producer-v2-independent-review-v1.json").read_text())
        self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-v2-independent-review-schema-v1.json").read_text())

    def test_receipt_validates_against_closed_schema(self) -> None:
        _validate_schema_value(self.receipt, self.schema, self.schema, "$")

    def test_hashes_are_exact(self) -> None:
        expected = {
            "contract": MODELS / "e14-fdic-archive-atomic-producer-v2-contract-v1.json",
            "plan": MODELS / "e14-fdic-archive-atomic-producer-v2-plan-v1.json",
            "auditSchema": MODELS / "e14-fdic-archive-atomic-producer-v2-audit-schema-v1.json",
            "audit": DATA / "e14-fdic-archive-atomic-producer-v2-audit-v1.json",
            "implementation": Path("regime_eval/e14_fdic_archive_atomic_producer_v2.py"),
            "producerTests": Path("tests/test_e14_fdic_archive_atomic_producer_v2.py"),
            "auditTests": Path("tests/test_e14_fdic_archive_atomic_producer_v2_audit.py"),
            "reviewSchema": MODELS / "e14-fdic-archive-atomic-producer-v2-independent-review-schema-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.receipt["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)

    def test_needs_changes_keeps_downstream_closed(self) -> None:
        self.assertEqual("needs_changes", self.receipt["decision"])
        self.assertTrue(self.receipt["assessments"]["atomicPublicationFailClosed"])
        self.assertFalse(self.receipt["assessments"]["contractTrustAnchorEnforced"])
        self.assertFalse(self.receipt["assessments"]["providerProvenanceNonFabricable"])
        self.assertFalse(self.receipt["assessments"]["discoveryCatalogAuthorized"])
        self.assertEqual(7, len(self.receipt["blockingFindings"]))


if __name__ == "__main__": unittest.main()
