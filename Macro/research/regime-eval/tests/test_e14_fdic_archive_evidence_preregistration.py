from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_evidence_preregistration import (
    STATUS,
    write_e14_fdic_archive_evidence_preregistration,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveEvidencePreregistrationTests(unittest.TestCase):
    def test_preregisters_two_outcome_protocol_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _call(Path(directory))
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(79, audit["inventory"]["requiredQuarterCount"])
            self.assertEqual(79, audit["inventory"]["pendingProviderEvidenceCount"])
            self.assertTrue(audit["checks"]["resolvedOutcomeRepresentable"])
            self.assertTrue(audit["checks"]["confirmedAbsentOutcomeRepresentable"])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertFalse(audit["protocol"]["mapV2Materialized"])
            self.assertFalse(audit["decision"]["networkCollectionAuthorized"])

    def test_map_schema_v2_represents_both_closed_outcomes(self) -> None:
        schema = json.loads((MODELS / "e14-fdic-archive-quarter-map-schema-v2.json").read_text(encoding="utf-8"))
        self.assertIn("resolvedEntries", schema["properties"])
        self.assertIn("confirmedAbsentEntries", schema["properties"])
        self.assertFalse(schema["$defs"]["resolvedEntry"]["additionalProperties"])
        self.assertFalse(schema["$defs"]["absentEntry"]["additionalProperties"])
        self.assertIn("archiveRecordId", schema["$defs"]["resolvedEntry"]["required"])
        self.assertIn("evidence", schema["$defs"]["absentEntry"]["required"])

    def test_outputs_are_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _call(root)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(root)

    def test_mutated_review_is_rejected_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = root / "review.json"
            review.write_bytes((DATA / "e14-fdic-archive-quarter-map-independent-review-v1.json").read_bytes() + b"\n")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(root / "outputs", blocked_review=review)

    def test_existing_discovery_catalog_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forbidden = root / "data/historical-real-v12-2008-2025/challengers/e14-fdic-archive-provider-discovery-requests-v1.json"
            forbidden.parent.mkdir(parents=True)
            forbidden.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "forbidden catalog"):
                _call(root / "outputs", repository_root=root)


def _call(
    output_root: Path,
    *,
    blocked_review: Path | None = None,
    repository_root: Path = Path("../.."),
) -> Path:
    return write_e14_fdic_archive_evidence_preregistration(
        MODELS / "e14-fdic-archive-evidence-preregistration-contract-v1.json",
        blocked_review or DATA / "e14-fdic-archive-quarter-map-independent-review-v1.json",
        DATA / "e14-fdic-archive-quarter-map-v1.json",
        DATA / "e14-fdic-archive-quarter-map-audit-v1.json",
        MODELS / "e14-fdic-archive-evidence-collection-plan-v1.json",
        MODELS / "e14-fdic-archive-quarter-map-schema-v2.json",
        MODELS / "e14-fdic-archive-quarter-map-audit-schema-v2.json",
        MODELS / "e14-fdic-archive-evidence-preregistration-audit-schema-v1.json",
        repository_root,
        output_root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
