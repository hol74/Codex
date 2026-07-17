from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_evidence_remediation import (
    STATUS,
    _valid_fixture,
    validate_archive_audit_consistency,
    validate_archive_map_semantics,
    write_e14_fdic_archive_evidence_remediation,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveEvidenceRemediationTests(unittest.TestCase):
    def test_preregisters_url_bound_model_and_validator_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _call(Path(directory))
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertTrue(audit["checks"]["providerUrlAndRequestProvenanceRequired"])
            self.assertTrue(audit["checks"]["partialPublicationBlockedByValidator"])
            self.assertEqual(5, audit["validatorSelfTest"]["scenariosPassed"])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertFalse(audit["protocol"]["mapV3Materialized"])
            self.assertFalse(audit["decision"]["discoveryCatalogAuthorized"])

    def test_valid_79_quarter_fixture_passes_semantic_validation(self) -> None:
        mapping, manifest = _valid_fixture()
        report = validate_archive_map_semantics(mapping, manifest)
        self.assertEqual(79, report["validatedQuarterCount"])
        self.assertEqual(79, report["resolvedCount"])
        self.assertEqual(0, report["confirmedAbsentCount"])

    def test_partial_or_duplicate_roster_is_rejected(self) -> None:
        mapping, manifest = _valid_fixture()
        mapping["entries"].pop()
        with self.assertRaisesRegex(DatasetValidationError, "exact ordered unique"):
            validate_archive_map_semantics(mapping, manifest)
        mapping, manifest = _valid_fixture()
        mapping["entries"][1] = copy.deepcopy(mapping["entries"][0])
        with self.assertRaisesRegex(DatasetValidationError, "exact ordered unique"):
            validate_archive_map_semantics(mapping, manifest)

    def test_off_provider_or_reused_evidence_is_rejected(self) -> None:
        mapping, manifest = _valid_fixture()
        manifest["records"][0]["requestedUrl"] = "https://example.com/not-provider"
        with self.assertRaisesRegex(DatasetValidationError, "off-provider"):
            validate_archive_map_semantics(mapping, manifest)
        mapping, manifest = _valid_fixture()
        mapping["entries"][1]["evidenceId"] = mapping["entries"][0]["evidenceId"]
        with self.assertRaisesRegex(DatasetValidationError, "missing or reused"):
            validate_archive_map_semantics(mapping, manifest)

    def test_outcome_and_hash_mismatches_are_rejected(self) -> None:
        mapping, manifest = _valid_fixture()
        manifest["records"][0]["outcome"] = "confirmed-absent-provider-primary"
        with self.assertRaisesRegex(DatasetValidationError, "outcome mismatch"):
            validate_archive_map_semantics(mapping, manifest)
        mapping, manifest = _valid_fixture()
        mapping["entries"][0]["evidenceSha256"] = "f" * 64
        with self.assertRaisesRegex(DatasetValidationError, "hash mismatch"):
            validate_archive_map_semantics(mapping, manifest)

    def test_audit_counts_must_match_validated_map(self) -> None:
        mapping, manifest = _valid_fixture()
        audit = {
            "inventory": {"quarterCount": 79, "resolvedCount": 78, "confirmedAbsentCount": 1, "unresolvedCount": 0, "firstQuarter": "2006Q1", "lastQuarter": "2025Q3"},
            "validatorReport": {"semanticValidationPassed": True, "exactRosterPassed": True, "uniqueQuarterIdsPassed": True, "evidenceProvenancePassed": True, "outcomeConsistencyPassed": True, "validatedQuarterCount": 79},
        }
        with self.assertRaisesRegex(DatasetValidationError, "inventory"):
            validate_archive_audit_consistency(mapping, manifest, audit)

    def test_output_is_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _call(root)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(root)

    def test_existing_discovery_catalog_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forbidden = root / "data/historical-real-v12-2008-2025/challengers/e14-fdic-archive-provider-discovery-requests-v1.json"
            forbidden.parent.mkdir(parents=True)
            forbidden.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "forbidden discovery"):
                _call(root / "outputs", repository_root=root)


def _call(output_root: Path, *, repository_root: Path = Path("../..")) -> Path:
    return write_e14_fdic_archive_evidence_remediation(
        MODELS / "e14-fdic-archive-evidence-remediation-contract-v1.json",
        DATA / "e14-fdic-archive-evidence-independent-review-v1.json",
        MODELS / "e14-fdic-archive-evidence-remediation-plan-v2.json",
        MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json",
        MODELS / "e14-fdic-archive-quarter-map-schema-v3.json",
        MODELS / "e14-fdic-archive-quarter-map-audit-schema-v3.json",
        MODELS / "e14-fdic-archive-evidence-remediation-audit-schema-v1.json",
        repository_root,
        output_root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
