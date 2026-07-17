from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV2AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads((DATA / "e14-fdic-archive-atomic-producer-v2-audit-v1.json").read_text())
        self.schema = json.loads((MODELS / "e14-fdic-archive-atomic-producer-v2-audit-schema-v1.json").read_text())

    def test_audit_validates_against_closed_schema(self) -> None:
        _validate_schema_value(self.audit, self.schema, self.schema, "$")

    def test_hashes_are_exact(self) -> None:
        expected = {
            "contractSha256": MODELS / "e14-fdic-archive-atomic-producer-v2-contract-v1.json",
            "blockedReviewSha256": DATA / "e14-fdic-archive-atomic-producer-independent-review-v1.json",
            "planSha256": MODELS / "e14-fdic-archive-atomic-producer-v2-plan-v1.json",
        }
        for key, path in expected.items():
            self.assertEqual(self.audit["inputs"][key], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(self.audit["implementation"]["sourceSha256"], hashlib.sha256(Path("regime_eval/e14_fdic_archive_atomic_producer_v2.py").read_bytes()).hexdigest())
        self.assertEqual(self.audit["implementation"]["testsSha256"], hashlib.sha256(Path("tests/test_e14_fdic_archive_atomic_producer_v2.py").read_bytes()).hexdigest())

    def test_downstream_remains_closed(self) -> None:
        self.assertFalse(self.audit["decision"]["discoveryCatalogAuthorized"])
        self.assertFalse(self.audit["decision"]["executionGateAuthorized"])
        self.assertEqual(0, self.audit["protocol"]["networkRequestsMade"])


if __name__ == "__main__": unittest.main()
