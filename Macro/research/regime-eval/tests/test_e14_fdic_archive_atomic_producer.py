from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_atomic_producer import (
    build_test_bundle,
    publish_archive_bundle_atomic,
    validate_integrated_bundle,
    write_e14_fdic_archive_atomic_producer_audit,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog_path = DATA / "e14-fdic-publication-metadata-requests-v1.json"
        self.catalog_raw = self.catalog_path.read_bytes()
        self.catalog = json.loads(self.catalog_raw)
        self.catalog_schema = _load(MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json")
        self.evidence_schema = _load(MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json")
        self.map_schema = _load(MODELS / "e14-fdic-archive-quarter-map-schema-v3.json")
        self.audit_schema = _load(MODELS / "e14-fdic-archive-quarter-map-audit-schema-v3.json")

    def test_valid_bundle_with_confirmed_absence_publishes_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); raw = root / "raw"; raw.mkdir()
            mapping, manifest = build_test_bundle(self.catalog, raw, absent_index=0)
            target = publish_archive_bundle_atomic(mapping, manifest, self.catalog, raw, root / "published", self.map_schema, self.evidence_schema, self.catalog_schema, self.audit_schema, source_catalog_raw=self.catalog_raw)
            self.assertEqual(3, len(list(target.iterdir())))
            self.assertEqual("confirmed-absent-provider-primary", mapping["entries"][0]["outcome"])

    def test_missing_raw_and_hash_mismatch_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw)
            (raw / manifest["records"][0]["fileName"]).unlink()
            with self.assertRaisesRegex(DatasetValidationError, "missing"):
                self._validate(mapping, manifest, raw)
            mapping, manifest = build_test_bundle(self.catalog, raw)
            (raw / manifest["records"][0]["fileName"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(DatasetValidationError, "size/hash mismatch"):
                self._validate(mapping, manifest, raw)

    def test_duplicate_request_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw)
            manifest["records"][1]["requestId"] = manifest["records"][0]["requestId"]
            _bind_manifest(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "request IDs"):
                self._validate(mapping, manifest, raw)

    def test_source_catalog_url_and_hash_binding_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw)
            mapping["entries"][0]["providerPrimaryUrl"] = "https://www.fdic.gov/wrong"
            with self.assertRaisesRegex(DatasetValidationError, "source catalog URL mismatch"):
                self._validate(mapping, manifest, raw)
            mapping, manifest = build_test_bundle(self.catalog, raw)
            mapping["sourceCatalog"]["sha256"] = "f" * 64
            with self.assertRaisesRegex(DatasetValidationError, "hash-bound"):
                self._validate(mapping, manifest, raw)

    def test_schema_invalid_payload_is_rejected_before_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw)
            mapping["schemaVersion"] = 999
            with self.assertRaisesRegex(DatasetValidationError, "schema const"):
                self._validate(mapping, manifest, raw)
            mapping, manifest = build_test_bundle(self.catalog, raw)
            manifest["records"][0]["contentType"] = ""
            with self.assertRaisesRegex(DatasetValidationError, "schema string"):
                self._validate(mapping, manifest, raw)

    def test_redirect_discontinuity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw)
            manifest["records"][0]["redirectChain"] = ["https://archive.fdic.gov/wrong", manifest["records"][0]["finalUrl"]]
            _bind_manifest(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "redirect chain"):
                self._validate(mapping, manifest, raw)

    def test_atomic_failure_leaves_no_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); raw = root / "raw"; raw.mkdir(); mapping, manifest = build_test_bundle(self.catalog, raw)
            target = root / "failed"
            with self.assertRaisesRegex(DatasetValidationError, "injected"):
                publish_archive_bundle_atomic(mapping, manifest, self.catalog, raw, target, self.map_schema, self.evidence_schema, self.catalog_schema, self.audit_schema, source_catalog_raw=self.catalog_raw, fail_before_publish=True)
            self.assertFalse(target.exists())
            self.assertEqual([], list(root.glob(".failed-staging-*")))

    def test_remediation_audit_is_write_once_and_offline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _call(Path(directory))
            audit = _load(output)
            self.assertEqual(9, audit["testMatrix"]["scenariosPassed"])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(Path(directory))

    def _validate(self, mapping: dict, manifest: dict, raw: Path) -> dict:
        return validate_integrated_bundle(mapping, manifest, self.catalog, raw, self.map_schema, self.evidence_schema, self.catalog_schema, source_catalog_raw=self.catalog_raw)


def _call(root: Path) -> Path:
    return write_e14_fdic_archive_atomic_producer_audit(
        MODELS / "e14-fdic-archive-atomic-producer-contract-v1.json",
        DATA / "e14-fdic-archive-evidence-remediation-independent-review-v1.json",
        MODELS / "e14-fdic-archive-atomic-producer-plan-v1.json",
        DATA / "e14-fdic-publication-metadata-requests-v1.json",
        MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json",
        MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json",
        MODELS / "e14-fdic-archive-quarter-map-schema-v3.json",
        MODELS / "e14-fdic-archive-quarter-map-audit-schema-v3.json",
        MODELS / "e14-fdic-archive-atomic-producer-audit-schema-v1.json",
        Path("../.."), root / "audit.json",
    )


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bind_manifest(mapping: dict, manifest: dict) -> None:
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    mapping["evidenceManifest"]["sha256"] = hashlib.sha256(raw).hexdigest()
    mapping["evidenceManifest"]["sizeBytes"] = len(raw)


if __name__ == "__main__":
    unittest.main()
