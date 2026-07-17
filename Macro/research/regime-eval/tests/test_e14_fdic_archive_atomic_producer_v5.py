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
from regime_eval.e14_fdic_archive_atomic_producer_v5 import LEDGER_FILE_NAME, publish_bundle_v5
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value
from regime_eval.e14_nofollow_platform_qualification import nofollow_platform_qualification


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveAtomicProducerV5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
        self.contract_raw = (MODELS / "e14-fdic-archive-producer-v5-runtime-test-contract-v1.json").read_bytes()
        self.contract = json.loads(self.contract_raw); self.contract_hash = _sha(self.contract_raw)
        self.inputs = {
            "sourceCatalog": (DATA / "e14-fdic-publication-metadata-requests-v1.json").read_bytes(),
            "sourceCatalogSchema": (MODELS / "e14-fdic-publication-metadata-request-catalog-schema-v1.json").read_bytes(),
            "evidenceManifestSchema": (MODELS / "e14-fdic-archive-evidence-manifest-schema-v1.json").read_bytes(),
            "mapSchema": (MODELS / "e14-fdic-archive-quarter-map-schema-v3.json").read_bytes(),
            "bundleAuditSchema": (MODELS / "e14-fdic-archive-producer-v5-bundle-audit-schema-v1.json").read_bytes(),
            "executionGate": (MODELS / "e14-fdic-producer-v4-test-gate-v1.json").read_bytes(),
            "executionGateSchema": (MODELS / "e14-fdic-producer-v4-test-gate-schema-v1.json").read_bytes(),
            "envelopeSchema": (MODELS / "e14-fdic-response-envelope-schema-v2.json").read_bytes(),
            "collectorReceiptSchema": (MODELS / "e14-fdic-collector-receipt-schema-v2.json").read_bytes(),
            "collectorPublicKey": (MODELS / "e14-fdic-producer-v4-test-collector-public-key-v1.hex").read_bytes(),
            "ledgerSchema": (MODELS / "e14-fdic-archive-receipt-ledger-schema-v1.json").read_bytes(),
        }
        self.catalog = json.loads(self.inputs["sourceCatalog"])

    def test_publishes_and_commits_trusted_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self._bundle(envelopes)
            target = publish_bundle_v5(self.contract_raw, mapping, manifest, envelopes, receipt, root / "published", inputs=self.inputs)
            ledger = json.loads((root / LEDGER_FILE_NAME).read_text()); audit = json.loads((target / "e14-fdic-archive-producer-v5-bundle-audit-v1.json").read_text())
            self.assertEqual(_sha(receipt), ledger["headReceiptSha256"]); self.assertEqual(1, len(ledger["entries"]))
            self.assertFalse(audit["networkCaptureAccepted"]); self.assertEqual(79, len(audit["envelopeHashes"]))

    def test_exact_replay_to_different_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self._bundle(envelopes)
            publish_bundle_v5(self.contract_raw, mapping, manifest, envelopes, receipt, root / "first", inputs=self.inputs)
            with self.assertRaisesRegex(DatasetValidationError, "trusted ledger head|already consumed"):
                publish_bundle_v5(self.contract_raw, mapping, manifest, envelopes, receipt, root / "second", inputs=self.inputs)
            self.assertFalse((root / "second").exists())

    def test_receipt_must_extend_current_head(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt_raw = self._bundle(envelopes)
            receipt = json.loads(receipt_raw); receipt["previousReceiptSha256"] = "0" * 64; _sign(receipt, self.private_key)
            with self.assertRaisesRegex(DatasetValidationError, "trusted ledger head"):
                publish_bundle_v5(self.contract_raw, mapping, manifest, envelopes, _json_bytes(receipt), root / "failed", inputs=self.inputs)

    def test_network_capture_is_unrepresentable_and_rejected(self) -> None:
        schema = json.loads(self.inputs["collectorReceiptSchema"]); receipt = {"schemaVersion": 2, "receiptId": "receipt-synthetic-001", "collectorId": "collector-synthetic-001", "contractSha256": "0" * 64, "catalogSha256": "1" * 64, "acquisitionRunId": "synthetic-run-0001", "runNonce": "synthetic-nonce-0000000001", "attestationType": "provider-network-capture", "networkRequestsMade": 79, "envelopeHashes": {f"{year}q{quarter}.html": "2" * 64 for year in range(2006, 2026) for quarter in range(1, 4 if year == 2025 else 5)}, "previousReceiptSha256": None, "signatureBase64": "x" * 88}
        with self.assertRaises(DatasetValidationError):
            _validate_schema_value(receipt, schema, schema, "$")

    def test_strict_hash_rosters_reject_arbitrary_names_and_values(self) -> None:
        receipt_schema = json.loads(self.inputs["collectorReceiptSchema"]); bundle_schema = json.loads(self.inputs["bundleAuditSchema"])
        self.assertFalse(receipt_schema["properties"]["envelopeHashes"]["additionalProperties"])
        self.assertEqual(79, len(receipt_schema["properties"]["envelopeHashes"]["required"]))
        self.assertFalse(bundle_schema["properties"]["inputHashes"]["additionalProperties"])
        self.assertEqual(11, len(bundle_schema["properties"]["inputHashes"]["required"]))

    def test_failure_after_ledger_commit_consumes_nonce(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self._bundle(envelopes)
            with self.assertRaisesRegex(DatasetValidationError, "durable nonce consumption"):
                publish_bundle_v5(self.contract_raw, mapping, manifest, envelopes, receipt, root / "failed", inputs=self.inputs, fail_after_ledger_commit=True)
            self.assertFalse((root / "failed").exists()); self.assertTrue((root / LEDGER_FILE_NAME).exists())
            with self.assertRaisesRegex(DatasetValidationError, "trusted ledger head|already consumed"):
                publish_bundle_v5(self.contract_raw, mapping, manifest, envelopes, receipt, root / "retry", inputs=self.inputs)

    def test_staging_corruption_does_not_publish_or_consume_nonce(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self._bundle(envelopes)
            with self.assertRaisesRegex(DatasetValidationError, "complete post-write"):
                publish_bundle_v5(self.contract_raw, mapping, manifest, envelopes, receipt, root / "failed", inputs=self.inputs, corrupt_staged_name="e14-fdic-archive-producer-v5-bundle-audit-v1.json")
            self.assertFalse((root / "failed").exists()); self.assertFalse((root / LEDGER_FILE_NAME).exists())

    def test_windows_nofollow_fallback_is_explicitly_qualified(self) -> None:
        qualification = nofollow_platform_qualification()
        self.assertTrue(qualification["symlinkPrecheckEnabled"])
        self.assertTrue(qualification["lstatFstatDeviceInodeCheckEnabled"])
        self.assertTrue(qualification["regularFileDescriptorCheckEnabled"])
        self.assertTrue(qualification["failClosedOnIdentityChange"])
        if qualification["platform"] == "Windows":
            self.assertEqual("descriptor-identity-fallback", qualification["qualificationMode"])

    def _bundle(self, root: Path):
        mapping, manifest = build_test_bundle(self.catalog, root, absent_index=0)
        for record in manifest["records"]:
            body = (root / record["fileName"]).read_bytes()
            if record["outcome"] == "confirmed-absent-provider-primary":
                body = f"provider-no-record {record['quarterId']} no matching record in signed synthetic response".encode(); digest = _sha(body); record["responseSha256"] = digest; record["sizeBytes"] = len(body); next(item for item in mapping["entries"] if item["quarterId"] == record["quarterId"])["evidenceSha256"] = digest
            envelope = {"schemaVersion": 2, "envelopeId": "envelope-" + record["quarterId"].lower(), "collectorId": "e14-v5-test-collector", "collectorReceiptId": self.contract["collectorReceiptId"], "contractSha256": self.contract_hash, "catalogSha256": _sha(self.inputs["sourceCatalog"]), "acquisitionRunId": self.contract["acquisitionRunId"], "runNonce": self.contract["runNonce"], "requestId": record["requestId"], "quarterId": record["quarterId"], "requestedUrl": record["requestedUrl"], "finalUrl": record["finalUrl"], "redirects": [], "retrievedAtUtc": record["retrievedAtUtc"], "statusCode": record["statusCode"], "contentType": record["contentType"], "outcome": record["outcome"], "responseBodyBase64": base64.b64encode(body).decode(), "responseSha256": record["responseSha256"], "responseSizeBytes": len(body), "signatureBase64": ""}
            _sign(envelope, self.private_key); (root / record["fileName"]).write_bytes(_json_bytes(envelope))
        _bind(mapping, manifest); return mapping, manifest, self._receipt(root, manifest)

    def _receipt(self, root: Path, manifest: dict) -> bytes:
        receipt = {"schemaVersion": 2, "receiptId": self.contract["collectorReceiptId"], "collectorId": "e14-v5-test-collector", "contractSha256": self.contract_hash, "catalogSha256": _sha(self.inputs["sourceCatalog"]), "acquisitionRunId": self.contract["acquisitionRunId"], "runNonce": self.contract["runNonce"], "attestationType": "synthetic-test", "networkRequestsMade": 0, "envelopeHashes": {record["fileName"]: _sha((root / record["fileName"]).read_bytes()) for record in manifest["records"]}, "previousReceiptSha256": None, "signatureBase64": ""}
        _sign(receipt, self.private_key); return _json_bytes(receipt)


def _canonical(value): return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
def _sign(value, key): value.pop("signatureBase64", None); value["signatureBase64"] = base64.b64encode(key.sign(_canonical(value))).decode()
def _json_bytes(value): return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
def _sha(raw): return hashlib.sha256(raw).hexdigest()
def _bind(mapping, manifest): raw = _json_bytes(manifest); mapping["evidenceManifest"]["sha256"] = _sha(raw); mapping["evidenceManifest"]["sizeBytes"] = len(raw)


if __name__ == "__main__": unittest.main()
