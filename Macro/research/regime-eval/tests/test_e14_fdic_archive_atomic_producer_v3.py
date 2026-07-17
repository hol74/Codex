from __future__ import annotations

import base64
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_atomic_producer import build_test_bundle
from regime_eval.e14_fdic_archive_atomic_producer_v3 import INPUT_KEYS, publish_bundle_v3, validate_bundle_v3


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog_raw = (DATA / "e14-fdic-publication-metadata-requests-v1.json").read_bytes()
        self.catalog = json.loads(self.catalog_raw)
        self.private_key = Ed25519PrivateKey.generate()
        public_raw = self.private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.inputs = {
            "sourceCatalog": self.catalog_raw,
            "sourceCatalogSchema": (MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json").read_bytes(),
            "evidenceManifestSchema": (MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json").read_bytes(),
            "mapSchema": (MODELS / "e14-fdic-archive-quarter-map-schema-v3.json").read_bytes(),
            "bundleAuditSchema": (MODELS / "e14-fdic-archive-producer-v3-bundle-audit-schema-v1.json").read_bytes(),
            "executionGate": b'{"status":"reviewed-test-gate"}',
            "executionGateSchema": b'{"type":"object","additionalProperties":false,"required":["status"],"properties":{"status":{"const":"reviewed-test-gate"}}}',
            "envelopeSchema": (MODELS / "e14-fdic-response-envelope-schema-v1.json").read_bytes(),
            "collectorPublicKey": public_raw,
        }
        contract = {"schemaVersion": 1, "contractId": "e14-fdic-archive-atomic-producer-v3-runtime-contract-v1",
                    "inputHashes": {key: _sha(self.inputs[key]) for key in INPUT_KEYS}}
        self.contract_raw = _json_bytes(contract); self.trusted_hash = _sha(self.contract_raw)

    def test_signed_bundle_publishes_and_revalidates_79_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "envelopes"; envelopes.mkdir()
            mapping, manifest = self._bundle(envelopes, absent_index=0)
            target = self._publish(mapping, manifest, envelopes, root / "published")
            self.assertEqual(79, len(list((target / "envelopes").iterdir())))
            audit = json.loads((target / "e14-fdic-archive-producer-v3-bundle-audit-v1.json").read_text())
            self.assertEqual(self.trusted_hash, audit["contractSha256"])
            self.assertTrue(audit["postWriteVerificationPassed"])

    def test_contract_and_every_input_hash_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest = self._bundle(root)
            with self.assertRaisesRegex(DatasetValidationError, "trusted review hash"):
                validate_bundle_v3(self.contract_raw, "0" * 64, mapping, manifest, root, inputs=self.inputs)
            changed = dict(self.inputs); changed["executionGateSchema"] = b"{}"
            with self.assertRaisesRegex(DatasetValidationError, "trusted contract"):
                validate_bundle_v3(self.contract_raw, self.trusted_hash, mapping, manifest, root, inputs=changed)

    def test_forged_or_swapped_envelope_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest = self._bundle(root)
            path = root / manifest["records"][0]["fileName"]; envelope = json.loads(path.read_text())
            envelope["quarterId"] = "2006Q2"; path.write_bytes(_json_bytes(envelope))
            with self.assertRaisesRegex(DatasetValidationError, "signature"):
                self._validate(mapping, manifest, root)
            mapping, manifest = self._bundle(root)
            manifest["records"][0]["requestId"], manifest["records"][1]["requestId"] = manifest["records"][1]["requestId"], manifest["records"][0]["requestId"]
            _bind(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "requestId"):
                self._validate(mapping, manifest, root)

    def test_redirect_receipt_is_signed_and_continuous(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest = self._bundle(root)
            record = manifest["records"][0]; path = root / record["fileName"]; envelope = json.loads(path.read_text())
            start, final = "https://archive.fdic.gov/start", envelope["finalUrl"]
            record["requestedUrl"] = start; record["redirectChain"] = [start, final]
            envelope["requestedUrl"] = start; envelope["redirects"] = [{"statusCode": 302, "fromUrl": start, "location": final, "toUrl": final}]
            _sign(envelope, self.private_key); path.write_bytes(_json_bytes(envelope)); _bind(mapping, manifest)
            self._validate(mapping, manifest, root)
            envelope["redirects"][0]["location"] = "https://archive.fdic.gov/wrong"; _sign(envelope, self.private_key); path.write_bytes(_json_bytes(envelope))
            with self.assertRaisesRegex(DatasetValidationError, "continuity"):
                self._validate(mapping, manifest, root)

    def test_post_write_corruption_and_failure_leave_no_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "envelopes"; envelopes.mkdir(); mapping, manifest = self._bundle(envelopes)
            target = root / "corrupt"
            with self.assertRaisesRegex(DatasetValidationError, "post-write"):
                publish_bundle_v3(self.contract_raw, self.trusted_hash, mapping, manifest, envelopes, target, inputs=self.inputs, corrupt_staged_index=0)
            self.assertFalse(target.exists()); self.assertEqual([], list(root.glob(".corrupt-staging-*")))

    def test_path_escape_is_rejected_at_each_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest = self._bundle(root)
            manifest["records"][0]["fileName"] = "../outside.json"; _bind(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "escaped"):
                self._validate(mapping, manifest, root)

    def _bundle(self, root: Path, absent_index: int | None = None):
        mapping, manifest = build_test_bundle(self.catalog, root, absent_index=absent_index)
        for record in manifest["records"]:
            body = (root / record["fileName"]).read_bytes()
            if record["outcome"] == "confirmed-absent-provider-primary":
                body = f"provider-no-record {record['quarterId']} no matching record in signed provider response".encode()
                digest = _sha(body); record["responseSha256"] = digest; record["sizeBytes"] = len(body)
                next(item for item in mapping["entries"] if item["quarterId"] == record["quarterId"])["evidenceSha256"] = digest
            envelope = {"schemaVersion": 1, "envelopeId": "envelope-" + record["quarterId"].lower(), "collectorId": "test-ed25519-collector",
                "requestId": record["requestId"], "quarterId": record["quarterId"], "requestedUrl": record["requestedUrl"], "finalUrl": record["finalUrl"],
                "redirects": [], "retrievedAtUtc": record["retrievedAtUtc"], "statusCode": record["statusCode"], "contentType": record["contentType"],
                "outcome": record["outcome"], "responseBodyBase64": base64.b64encode(body).decode(), "responseSha256": record["responseSha256"],
                "responseSizeBytes": len(body), "signatureBase64": ""}
            _sign(envelope, self.private_key); (root / record["fileName"]).write_bytes(_json_bytes(envelope))
        _bind(mapping, manifest); return mapping, manifest

    def _validate(self, mapping, manifest, root): return validate_bundle_v3(self.contract_raw, self.trusted_hash, mapping, manifest, root, inputs=self.inputs)
    def _publish(self, mapping, manifest, root, target): return publish_bundle_v3(self.contract_raw, self.trusted_hash, mapping, manifest, root, target, inputs=self.inputs)


def _canonical(value): return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
def _sign(envelope, key):
    envelope.pop("signatureBase64", None); envelope["signatureBase64"] = base64.b64encode(key.sign(_canonical(envelope))).decode()
def _json_bytes(value): return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
def _sha(raw): return hashlib.sha256(raw).hexdigest()
def _bind(mapping, manifest):
    raw = _json_bytes(manifest); mapping["evidenceManifest"]["sha256"] = _sha(raw); mapping["evidenceManifest"]["sizeBytes"] = len(raw)


if __name__ == "__main__": unittest.main()
