from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .dataset import DatasetValidationError
from .e14_fdic_archive_atomic_producer import _json_bytes
from .e14_fdic_archive_atomic_producer_v3 import _validate_redirects
from .e14_fdic_archive_atomic_producer_v4 import _body, _decode, _read_nofollow, _verify_signed
from .e14_fdic_archive_contract_verifier_v5 import verify_pinned_contract_v5
from .e14_fdic_archive_evidence_remediation import RESOLVED, validate_archive_map_semantics
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_ARCHIVE_ATOMIC_PRODUCER_V5_IMPLEMENTED_INDEPENDENT_REVIEW_REQUIRED"
LEDGER_FILE_NAME = "e14-fdic-archive-receipt-ledger-v1.json"
INPUT_KEYS = ("sourceCatalog", "sourceCatalogSchema", "evidenceManifestSchema", "mapSchema", "bundleAuditSchema", "executionGate", "executionGateSchema", "envelopeSchema", "collectorReceiptSchema", "collectorPublicKey", "ledgerSchema")


def validate_bundle_v5(contract_raw: bytes, map_payload: dict[str, Any], evidence_manifest: dict[str, Any], envelope_root: str | Path, collector_receipt_raw: bytes, *, inputs: dict[str, bytes], ledger: dict[str, Any]) -> dict[str, Any]:
    contract, contract_hash = verify_pinned_contract_v5(contract_raw)
    if set(inputs) != set(INPUT_KEYS) or contract.get("inputHashes") != {key: _sha(inputs[key]) for key in INPUT_KEYS}:
        raise DatasetValidationError("E14.7as runtime inputs differ from the deployment-pinned contract.")
    catalog = _decode(inputs["sourceCatalog"], "catalog"); catalog_schema = _decode(inputs["sourceCatalogSchema"], "catalog schema")
    evidence_schema = _decode(inputs["evidenceManifestSchema"], "evidence schema"); map_schema = _decode(inputs["mapSchema"], "map schema")
    gate = _decode(inputs["executionGate"], "gate"); gate_schema = _decode(inputs["executionGateSchema"], "gate schema")
    envelope_schema = _decode(inputs["envelopeSchema"], "envelope schema"); receipt_schema = _decode(inputs["collectorReceiptSchema"], "collector receipt schema")
    for value, schema in ((catalog, catalog_schema), (evidence_manifest, evidence_schema), (map_payload, map_schema), (gate, gate_schema)):
        _validate_schema_value(value, schema, schema, "$")
    report = validate_archive_map_semantics(map_payload, evidence_manifest)
    catalog_hash = _sha(inputs["sourceCatalog"]); manifest_raw = _json_bytes(evidence_manifest)
    if map_payload["sourceCatalog"]["sha256"] != catalog_hash or map_payload["evidenceManifest"]["sha256"] != _sha(manifest_raw):
        raise DatasetValidationError("E14.7as map catalog or manifest binding failed.")
    urls = {row["quarterId"]: row["providerPrimaryUrl"] for row in catalog["quarterRequests"]}
    if any(urls.get(row["quarterId"]) != row["providerPrimaryUrl"] for row in map_payload["entries"]):
        raise DatasetValidationError("E14.7as catalog URL binding failed.")
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(inputs["collectorPublicKey"].decode().strip()))
    except (ValueError, UnicodeDecodeError) as error:
        raise DatasetValidationError("E14.7as collector public key is invalid.") from error

    receipt = _decode(collector_receipt_raw, "collector receipt"); _validate_schema_value(receipt, receipt_schema, receipt_schema, "$"); _verify_signed(receipt, public_key, "collector receipt")
    context = {"contractSha256": contract_hash, "catalogSha256": catalog_hash, "acquisitionRunId": contract["acquisitionRunId"], "runNonce": contract["runNonce"]}
    if any(receipt.get(key) != value for key, value in context.items()) or receipt.get("receiptId") != contract["collectorReceiptId"]:
        raise DatasetValidationError("E14.7as collector receipt context does not match the pinned contract.")
    if receipt["attestationType"] != "synthetic-test" or receipt["networkRequestsMade"] != 0:
        raise DatasetValidationError("E14.7as network capture is unsupported and synthetic receipts must report zero requests.")
    if receipt["previousReceiptSha256"] != ledger["headReceiptSha256"]:
        raise DatasetValidationError("E14.7as receipt does not extend the trusted ledger head.")
    if any(row["acquisitionRunId"] == contract["acquisitionRunId"] or row["runNonce"] == contract["runNonce"] for row in ledger["entries"]):
        raise DatasetValidationError("E14.7as acquisition run or nonce was already consumed.")

    root = Path(envelope_root).resolve(); entries = {row["quarterId"]: row for row in map_payload["entries"]}
    seen_requests: set[str] = set(); seen_bodies: set[str] = set(); seen_records: set[str] = set(); envelope_hashes: dict[str, str] = {}
    for record in evidence_manifest["records"]:
        if record["requestId"] in seen_requests or record["responseSha256"] in seen_bodies:
            raise DatasetValidationError("E14.7as request and body identities must be unique.")
        seen_requests.add(record["requestId"]); seen_bodies.add(record["responseSha256"])
        raw = _read_nofollow(root, record["fileName"]); envelope_hashes[record["fileName"]] = _sha(raw)
        if receipt["envelopeHashes"].get(record["fileName"]) != _sha(raw):
            raise DatasetValidationError("E14.7as collector receipt does not bind the envelope bytes.")
        envelope = _decode(raw, "envelope"); _validate_schema_value(envelope, envelope_schema, envelope_schema, "$"); _verify_signed(envelope, public_key, "envelope")
        expected_context = {**context, "collectorReceiptId": receipt["receiptId"]}
        if any(envelope.get(key) != value for key, value in expected_context.items()):
            raise DatasetValidationError("E14.7as signed envelope context mismatch or replay.")
        for key in ("requestId", "quarterId", "requestedUrl", "finalUrl", "retrievedAtUtc", "statusCode", "contentType", "outcome", "responseSha256"):
            if envelope.get(key) != record.get(key):
                raise DatasetValidationError(f"E14.7as envelope binding failed for {key}.")
        body = _body(envelope)
        if _sha(body) != record["responseSha256"] or len(body) != record["sizeBytes"] or len(body) != envelope["responseSizeBytes"]:
            raise DatasetValidationError("E14.7as signed body size/hash mismatch.")
        _validate_redirects(envelope, record); entry = entries[record["quarterId"]]
        if record["quarterId"].encode() not in body or record["evidenceMarker"].encode() not in body:
            raise DatasetValidationError("E14.7as signed body lacks quarter or marker.")
        if record["outcome"] == RESOLVED:
            record_id = entry["archiveRecordId"]
            if record_id in seen_records or record_id.encode() not in body:
                raise DatasetValidationError("E14.7as resolved record is invalid or reused.")
            seen_records.add(record_id)
        elif b"no matching record" not in body.lower():
            raise DatasetValidationError("E14.7as signed body lacks absence proof.")
    if set(receipt["envelopeHashes"]) != set(envelope_hashes):
        raise DatasetValidationError("E14.7as collector receipt envelope roster mismatch.")
    return {"report": report, "contract": contract, "contractHash": contract_hash, "catalogHash": catalog_hash, "envelopeHashes": envelope_hashes, "collectorReceiptHash": _sha(collector_receipt_raw), "receipt": receipt}


def publish_bundle_v5(contract_raw: bytes, map_payload: dict[str, Any], evidence_manifest: dict[str, Any], envelope_root: str | Path, collector_receipt_raw: bytes, target_dir: str | Path, *, inputs: dict[str, bytes], corrupt_staged_name: str | None = None, fail_after_ledger_commit: bool = False) -> Path:
    target = Path(target_dir).resolve()
    if target.exists():
        raise DatasetValidationError("E14.7as target already exists.")
    target.parent.mkdir(parents=True, exist_ok=True); ledger_path = target.parent / LEDGER_FILE_NAME; lock_path = target.parent / (LEDGER_FILE_NAME + ".lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError as error:
        raise DatasetValidationError("E14.7as trusted ledger is locked by another publisher.") from error
    os.close(lock_fd); staging: Path | None = None; ledger_temp: Path | None = None
    try:
        ledger_schema = _decode(inputs["ledgerSchema"], "ledger schema"); ledger = _load_ledger(ledger_path, ledger_schema)
        result = validate_bundle_v5(contract_raw, map_payload, evidence_manifest, envelope_root, collector_receipt_raw, inputs=inputs, ledger=ledger)
        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-staging-", dir=target.parent)); envelope_dir = staging / "envelopes"; envelope_dir.mkdir(); root = Path(envelope_root).resolve(); expected: dict[Path, bytes] = {}
        for record in evidence_manifest["records"]:
            raw = _read_nofollow(root, record["fileName"]); path = envelope_dir / record["fileName"]; path.write_bytes(raw); expected[path] = raw
        manifest_raw, map_raw = _json_bytes(evidence_manifest), _json_bytes(map_payload)
        receipt_path = staging / "e14-fdic-collector-receipt-v2.json"; receipt_path.write_bytes(collector_receipt_raw); expected[receipt_path] = collector_receipt_raw
        manifest_path = staging / "e14-fdic-archive-evidence-manifest-v1.json"; manifest_path.write_bytes(manifest_raw); expected[manifest_path] = manifest_raw
        map_path = staging / "e14-fdic-archive-quarter-map-v3.json"; map_path.write_bytes(map_raw); expected[map_path] = map_raw
        contract = result["contract"]; receipt = result["receipt"]
        audit = {"schemaVersion": 1, "artifactType": "E14FdicArchiveProducerV5BundleAudit", "status": "FDIC_ARCHIVE_LEDGER_BOUND_SYNTHETIC_BUNDLE_COMPLETE", "contractSha256": result["contractHash"], "catalogSha256": result["catalogHash"], "acquisitionRunId": contract["acquisitionRunId"], "runNonce": contract["runNonce"], "collectorReceiptSha256": result["collectorReceiptHash"], "previousReceiptSha256": receipt["previousReceiptSha256"], "ledgerHeadAfterCommit": result["collectorReceiptHash"], "inputHashes": {key: _sha(inputs[key]) for key in INPUT_KEYS}, "manifestSha256": _sha(manifest_raw), "mapSha256": _sha(map_raw), "envelopeHashes": result["envelopeHashes"], "envelopeCount": 79, "allStagedArtifactsRevalidated": True, "networkCaptureAccepted": False, "nextAllowedAction": "Independent review before any downstream use."}
        audit_schema = _decode(inputs["bundleAuditSchema"], "bundle audit schema"); _validate_schema_value(audit, audit_schema, audit_schema, "$")
        audit_path = staging / "e14-fdic-archive-producer-v5-bundle-audit-v1.json"; audit_raw = _json_bytes(audit); audit_path.write_bytes(audit_raw); expected[audit_path] = audit_raw
        if corrupt_staged_name:
            match = next((path for path in expected if path.name == corrupt_staged_name), None)
            if match:
                match.write_bytes(b"corrupt")
        for path, raw in expected.items():
            reread = _read_nofollow(path.parent.resolve(), path.name)
            if reread != raw or _sha(reread) != _sha(raw):
                raise DatasetValidationError("E14.7as staged artifact failed complete post-write verification.")
        new_ledger = {"schemaVersion": 1, "artifactType": "E14FdicArchiveReceiptLedger", "headReceiptSha256": result["collectorReceiptHash"], "entries": [*ledger["entries"], {"acquisitionRunId": contract["acquisitionRunId"], "runNonce": contract["runNonce"], "receiptSha256": result["collectorReceiptHash"], "previousReceiptSha256": receipt["previousReceiptSha256"], "targetPathSha256": _sha(str(target).encode())}]}
        _validate_schema_value(new_ledger, ledger_schema, ledger_schema, "$"); _validate_ledger_semantics(new_ledger)
        fd, temp_name = tempfile.mkstemp(prefix=".e14-ledger-", suffix=".json", dir=target.parent); ledger_temp = Path(temp_name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(_json_bytes(new_ledger)); stream.flush(); os.fsync(stream.fileno())
        if _read_nofollow(target.parent, ledger_temp.name) != _json_bytes(new_ledger):
            raise DatasetValidationError("E14.7as ledger post-write verification failed.")
        os.replace(ledger_temp, ledger_path); ledger_temp = None
        if fail_after_ledger_commit:
            raise DatasetValidationError("E14.7as injected failure after durable nonce consumption.")
        os.replace(staging, target); staging = None
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        if ledger_temp is not None and ledger_temp.exists():
            ledger_temp.unlink()
        if lock_path.exists():
            lock_path.unlink()
    return target


def _load_ledger(path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        ledger = {"schemaVersion": 1, "artifactType": "E14FdicArchiveReceiptLedger", "headReceiptSha256": None, "entries": []}
    else:
        ledger = _decode(_read_nofollow(path.parent.resolve(), path.name), "receipt ledger")
    _validate_schema_value(ledger, schema, schema, "$"); _validate_ledger_semantics(ledger)
    return ledger


def _validate_ledger_semantics(ledger: dict[str, Any]) -> None:
    previous = None; runs: set[str] = set(); nonces: set[str] = set(); receipts: set[str] = set()
    for entry in ledger["entries"]:
        if entry["previousReceiptSha256"] != previous:
            raise DatasetValidationError("E14.7as ledger chain is discontinuous.")
        if entry["acquisitionRunId"] in runs or entry["runNonce"] in nonces or entry["receiptSha256"] in receipts:
            raise DatasetValidationError("E14.7as ledger contains a duplicate run, nonce or receipt.")
        runs.add(entry["acquisitionRunId"]); nonces.add(entry["runNonce"]); receipts.add(entry["receiptSha256"]); previous = entry["receiptSha256"]
    if ledger["headReceiptSha256"] != previous:
        raise DatasetValidationError("E14.7as ledger head does not match its append-only chain.")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
