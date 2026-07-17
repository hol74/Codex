from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_atomic_producer import build_test_bundle
from regime_eval.e14_fdic_archive_atomic_producer_v2 import (
    publish_archive_bundle_atomic_v2, validate_integrated_bundle_v2,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")
GATE_SCHEMA_RAW = json.dumps({"type": "object", "additionalProperties": False,
                              "required": ["status"], "properties": {"status": {"const": "reviewed-test-gate"}}}).encode()
GATE_RAW = b'{"status":"reviewed-test-gate"}'


class E14FdicArchiveAtomicProducerV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog_raw = (DATA / "e14-fdic-publication-metadata-requests-v1.json").read_bytes()
        self.catalog = json.loads(self.catalog_raw)
        self.catalog_schema_raw = (MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json").read_bytes()
        self.evidence_schema_raw = (MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json").read_bytes()
        self.map_schema_raw = (MODELS / "e14-fdic-archive-quarter-map-schema-v3.json").read_bytes()
        self.audit_schema_raw = (MODELS / "e14-fdic-archive-quarter-map-audit-schema-v3.json").read_bytes()

    def test_bundle_contains_raw_and_exact_reviewed_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); raw = root / "raw"; raw.mkdir(); mapping, manifest = build_test_bundle(self.catalog, raw)
            target = self._publish(mapping, manifest, raw, root / "published")
            self.assertEqual(79, len(list((target / "raw").iterdir())))
            audit = json.loads((target / "e14-fdic-archive-quarter-map-audit-v3.json").read_text())
            self.assertEqual(_sha(self.map_schema_raw), audit["inputs"]["mapSchema"]["sha256"])
            self.assertEqual(_sha(self.evidence_schema_raw), audit["inputs"]["evidenceSchema"]["sha256"])
            self.assertEqual(_sha(self.audit_schema_raw), audit["inputs"]["auditSchema"]["sha256"])
            self.assertEqual(_sha(GATE_RAW), audit["inputs"]["executionGate"]["sha256"])

    def test_catalog_object_raw_divergence_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw)
            mapping["entries"][0]["providerPrimaryUrl"] = "https://www.fdic.gov/forged.pdf"
            with self.assertRaisesRegex(DatasetValidationError, "source catalog URL mismatch"):
                self._validate(mapping, manifest, raw)

    def test_raw_and_archive_ids_must_be_unique_and_quarter_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw)
            manifest["records"][1]["fileName"] = manifest["records"][0]["fileName"]
            manifest["records"][1]["responseSha256"] = manifest["records"][0]["responseSha256"]
            manifest["records"][1]["requestedUrl"] = manifest["records"][0]["requestedUrl"]
            manifest["records"][1]["finalUrl"] = manifest["records"][0]["finalUrl"]
            mapping["entries"][1]["evidenceSha256"] = manifest["records"][0]["responseSha256"]
            mapping["entries"][1]["archiveRecordId"] = mapping["entries"][0]["archiveRecordId"]
            mapping["entries"][1]["archiveUrl"] = mapping["entries"][0]["archiveUrl"]
            _bind(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "unique per quarter"):
                self._validate(mapping, manifest, raw)

    def test_marker_only_absence_and_unsubstantiated_redirect_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw, absent_index=0)
            path = raw / manifest["records"][0]["fileName"]
            path.write_bytes(b"provider-no-record")
            digest = _sha(path.read_bytes()); manifest["records"][0]["responseSha256"] = digest
            manifest["records"][0]["sizeBytes"] = path.stat().st_size; mapping["entries"][0]["evidenceSha256"] = digest; _bind(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "quarter-bound|absence proof"):
                self._validate(mapping, manifest, raw)
            mapping, manifest = build_test_bundle(self.catalog, raw)
            manifest["records"][0]["redirectChain"] = [manifest["records"][0]["requestedUrl"], "https://www.fdic.gov/hop", manifest["records"][0]["finalUrl"]]
            _bind(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "intermediate redirect"):
                self._validate(mapping, manifest, raw)

    def test_valid_explicit_absence_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory); mapping, manifest = build_test_bundle(self.catalog, raw, absent_index=0)
            record = manifest["records"][0]; content = f"provider-no-record {record['quarterId']} no matching record was found by provider archive search".encode()
            path = raw / record["fileName"]; path.write_bytes(content); digest = _sha(content)
            record["responseSha256"] = digest; record["sizeBytes"] = len(content)
            mapping["entries"][0]["evidenceSha256"] = digest; _bind(mapping, manifest)
            self._validate(mapping, manifest, raw)

    def test_invalid_gate_and_prepublication_failure_leave_no_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); raw = root / "raw"; raw.mkdir(); mapping, manifest = build_test_bundle(self.catalog, raw)
            with self.assertRaises(DatasetValidationError):
                validate_integrated_bundle_v2(mapping, manifest, raw, **self._args(execution_gate_raw=b"{}"))
            target = root / "failed"
            with self.assertRaisesRegex(DatasetValidationError, "injected"):
                publish_archive_bundle_atomic_v2(mapping, manifest, raw, target, fail_before_publish=True, **self._args())
            self.assertFalse(target.exists()); self.assertEqual([], list(root.glob(".failed-staging-*")))

    def _args(self, **overrides: bytes) -> dict:
        values = {"source_catalog_raw": self.catalog_raw, "source_catalog_schema_raw": self.catalog_schema_raw,
                  "map_schema_raw": self.map_schema_raw, "evidence_schema_raw": self.evidence_schema_raw,
                  "map_audit_schema_raw": self.audit_schema_raw, "execution_gate_raw": GATE_RAW,
                  "execution_gate_schema_raw": GATE_SCHEMA_RAW}
        values.update(overrides); return values

    def _validate(self, mapping: dict, manifest: dict, raw: Path):
        return validate_integrated_bundle_v2(mapping, manifest, raw, **self._args())

    def _publish(self, mapping: dict, manifest: dict, raw: Path, target: Path):
        return publish_archive_bundle_atomic_v2(mapping, manifest, raw, target, **self._args())


def _sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def _bind(mapping: dict, manifest: dict) -> None:
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    mapping["evidenceManifest"]["sha256"] = _sha(raw); mapping["evidenceManifest"]["sizeBytes"] = len(raw)


if __name__ == "__main__": unittest.main()
