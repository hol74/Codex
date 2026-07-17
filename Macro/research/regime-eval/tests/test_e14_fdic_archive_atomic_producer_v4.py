from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_atomic_producer import build_test_bundle
from regime_eval.e14_fdic_archive_atomic_producer_v4 import INPUT_KEYS, publish_bundle_v4, validate_bundle_v4


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
        self.contract_raw = (MODELS / "e14-fdic-archive-producer-v4-runtime-test-contract-v1.json").read_bytes()
        self.contract = json.loads(self.contract_raw); self.contract_hash = _sha(self.contract_raw)
        self.inputs = {
            "sourceCatalog": (DATA / "e14-fdic-publication-metadata-requests-v1.json").read_bytes(),
            "sourceCatalogSchema": (MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json").read_bytes(),
            "evidenceManifestSchema": (MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json").read_bytes(),
            "mapSchema": (MODELS / "e14-fdic-archive-quarter-map-schema-v3.json").read_bytes(),
            "bundleAuditSchema": (MODELS / "e14-fdic-archive-producer-v4-bundle-audit-schema-v1.json").read_bytes(),
            "executionGate": (MODELS / "e14-fdic-producer-v4-test-gate-v1.json").read_bytes(),
            "executionGateSchema": (MODELS / "e14-fdic-producer-v4-test-gate-schema-v1.json").read_bytes(),
            "envelopeSchema": (MODELS / "e14-fdic-response-envelope-schema-v2.json").read_bytes(),
            "collectorReceiptSchema": (MODELS / "e14-fdic-collector-receipt-schema-v1.json").read_bytes(),
            "collectorPublicKey": (MODELS / "e14-fdic-producer-v4-test-collector-public-key-v1.hex").read_bytes(),
        }
        self.catalog = json.loads(self.inputs["sourceCatalog"])

    def test_pinned_context_bound_bundle_publishes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); env = root / "env"; env.mkdir(); mapping, manifest, receipt = self._bundle(env, absent_index=0)
            target = publish_bundle_v4(self.contract_raw, mapping, manifest, env, receipt, root / "published", inputs=self.inputs)
            self.assertEqual(79, len(list((target / "envelopes").iterdir())))
            audit = json.loads((target / "e14-fdic-archive-producer-v4-bundle-audit-v1.json").read_text())
            self.assertTrue(audit["allStagedArtifactsRevalidated"]); self.assertFalse(audit["networkAttestationAccepted"])

    def test_contract_cannot_be_self_pinned_by_caller(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest, receipt = self._bundle(root)
            modified = json.loads(self.contract_raw); modified["runNonce"] = "caller-controlled-nonce-999"; raw = _json_bytes(modified)
            with self.assertRaisesRegex(DatasetValidationError, "deployment-pinned"):
                validate_bundle_v4(raw, mapping, manifest, root, receipt, inputs=self.inputs)

    def test_cross_run_replay_and_request_swap_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest, receipt = self._bundle(root)
            path = root / manifest["records"][0]["fileName"]; envelope = json.loads(path.read_text()); envelope["runNonce"] = "another-run-nonce-0001"; _sign(envelope, self.private_key); path.write_bytes(_json_bytes(envelope))
            receipt = self._receipt(root, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "context mismatch|replay"):
                self._validate(mapping, manifest, root, receipt)
            mapping, manifest, receipt = self._bundle(root)
            manifest["records"][0]["requestId"], manifest["records"][1]["requestId"] = manifest["records"][1]["requestId"], manifest["records"][0]["requestId"]; _bind(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "requestId"):
                self._validate(mapping, manifest, root, receipt)

    def test_collector_receipt_distinguishes_synthetic_from_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest, receipt_raw = self._bundle(root)
            receipt = json.loads(receipt_raw); receipt["attestationType"] = "provider-network-capture"; receipt["networkRequestsMade"] = 79; _sign(receipt, self.private_key)
            with self.assertRaisesRegex(DatasetValidationError, "misstates network"):
                self._validate(mapping, manifest, root, _json_bytes(receipt))

    def test_every_staged_json_is_revalidated(self) -> None:
        names = ["e14-fdic-archive-evidence-manifest-v1.json", "e14-fdic-archive-quarter-map-v3.json", "e14-fdic-archive-producer-v4-bundle-audit-v1.json"]
        for name in names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); env = root / "env"; env.mkdir(); mapping, manifest, receipt = self._bundle(env); target = root / "failed"
                with self.assertRaisesRegex(DatasetValidationError, "complete post-write"):
                    publish_bundle_v4(self.contract_raw, mapping, manifest, env, receipt, target, inputs=self.inputs, corrupt_staged_name=name)
                self.assertFalse(target.exists()); self.assertEqual([], list(root.glob(".failed-staging-*")))

    def test_path_escape_is_rejected_by_descriptor_reader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); mapping, manifest, receipt = self._bundle(root); manifest["records"][0]["fileName"] = "../outside.json"; _bind(mapping, manifest)
            with self.assertRaisesRegex(DatasetValidationError, "escaped root"):
                self._validate(mapping, manifest, root, receipt)

    def _bundle(self, root: Path, absent_index: int | None = None):
        mapping, manifest = build_test_bundle(self.catalog, root, absent_index=absent_index)
        for record in manifest["records"]:
            body = (root / record["fileName"]).read_bytes()
            if record["outcome"] == "confirmed-absent-provider-primary":
                body = f"provider-no-record {record['quarterId']} no matching record in signed synthetic response".encode(); digest = _sha(body); record["responseSha256"] = digest; record["sizeBytes"] = len(body); next(item for item in mapping["entries"] if item["quarterId"] == record["quarterId"])["evidenceSha256"] = digest
            envelope = {"schemaVersion": 2, "envelopeId": "envelope-" + record["quarterId"].lower(), "collectorId": "e14-v4-test-collector", "collectorReceiptId": self.contract["collectorReceiptId"], "contractSha256": self.contract_hash, "catalogSha256": _sha(self.inputs["sourceCatalog"]), "acquisitionRunId": self.contract["acquisitionRunId"], "runNonce": self.contract["runNonce"], "requestId": record["requestId"], "quarterId": record["quarterId"], "requestedUrl": record["requestedUrl"], "finalUrl": record["finalUrl"], "redirects": [], "retrievedAtUtc": record["retrievedAtUtc"], "statusCode": record["statusCode"], "contentType": record["contentType"], "outcome": record["outcome"], "responseBodyBase64": base64.b64encode(body).decode(), "responseSha256": record["responseSha256"], "responseSizeBytes": len(body), "signatureBase64": ""}
            _sign(envelope, self.private_key); (root / record["fileName"]).write_bytes(_json_bytes(envelope))
        _bind(mapping, manifest); return mapping, manifest, self._receipt(root, manifest)

    def _receipt(self, root: Path, manifest: dict) -> bytes:
        receipt = {"schemaVersion": 1, "receiptId": self.contract["collectorReceiptId"], "collectorId": "e14-v4-test-collector", "contractSha256": self.contract_hash, "catalogSha256": _sha(self.inputs["sourceCatalog"]), "acquisitionRunId": self.contract["acquisitionRunId"], "runNonce": self.contract["runNonce"], "attestationType": "synthetic-test", "networkRequestsMade": 0, "envelopeHashes": {record["fileName"]: _sha((root / record["fileName"]).read_bytes()) for record in manifest["records"]}, "previousReceiptSha256": None, "signatureBase64": ""}
        _sign(receipt, self.private_key); return _json_bytes(receipt)
    def _validate(self, mapping, manifest, root, receipt): return validate_bundle_v4(self.contract_raw, mapping, manifest, root, receipt, inputs=self.inputs)


def _canonical(value): return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
def _sign(value, key): value.pop("signatureBase64", None); value["signatureBase64"] = base64.b64encode(key.sign(_canonical(value))).decode()
def _json_bytes(value): return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
def _sha(raw): return hashlib.sha256(raw).hexdigest()
def _bind(mapping, manifest): raw = _json_bytes(manifest); mapping["evidenceManifest"]["sha256"] = _sha(raw); mapping["evidenceManifest"]["sizeBytes"] = len(raw)
if __name__ == "__main__": unittest.main()
