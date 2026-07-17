from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .dataset import DatasetValidationError
from .e14_fdic_archive_atomic_producer import _json_bytes
from .e14_fdic_archive_contract_verifier import verify_pinned_contract
from .e14_fdic_archive_evidence_remediation import ABSENT, RESOLVED, validate_archive_map_semantics
from .e14_fdic_archive_atomic_producer_v3 import _validate_redirects
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_ARCHIVE_ATOMIC_PRODUCER_V4_IMPLEMENTED_INDEPENDENT_REVIEW_REQUIRED"
INPUT_KEYS = ("sourceCatalog", "sourceCatalogSchema", "evidenceManifestSchema", "mapSchema", "bundleAuditSchema", "executionGate", "executionGateSchema", "envelopeSchema", "collectorReceiptSchema", "collectorPublicKey")


def validate_bundle_v4(contract_raw: bytes, map_payload: dict[str, Any], evidence_manifest: dict[str, Any], envelope_root: str | Path, collector_receipt_raw: bytes, *, inputs: dict[str, bytes]) -> dict[str, Any]:
    contract, contract_hash = verify_pinned_contract(contract_raw)
    if set(inputs) != set(INPUT_KEYS) or contract.get("inputHashes") != {key: _sha(inputs[key]) for key in INPUT_KEYS}:
        raise DatasetValidationError("E14.7aq runtime inputs differ from the deployment-pinned contract.")
    catalog = _decode(inputs["sourceCatalog"], "catalog"); catalog_schema = _decode(inputs["sourceCatalogSchema"], "catalog schema")
    evidence_schema = _decode(inputs["evidenceManifestSchema"], "evidence schema"); map_schema = _decode(inputs["mapSchema"], "map schema")
    gate = _decode(inputs["executionGate"], "gate"); gate_schema = _decode(inputs["executionGateSchema"], "gate schema")
    envelope_schema = _decode(inputs["envelopeSchema"], "envelope schema"); receipt_schema = _decode(inputs["collectorReceiptSchema"], "collector receipt schema")
    for value, schema in ((catalog, catalog_schema), (evidence_manifest, evidence_schema), (map_payload, map_schema), (gate, gate_schema)):
        _validate_schema_value(value, schema, schema, "$")
    report = validate_archive_map_semantics(map_payload, evidence_manifest)
    catalog_hash = _sha(inputs["sourceCatalog"]); manifest_raw = _json_bytes(evidence_manifest)
    if map_payload["sourceCatalog"]["sha256"] != catalog_hash or map_payload["evidenceManifest"]["sha256"] != _sha(manifest_raw):
        raise DatasetValidationError("E14.7aq map catalog or manifest binding failed.")
    urls = {row["quarterId"]: row["providerPrimaryUrl"] for row in catalog["quarterRequests"]}
    if any(urls.get(row["quarterId"]) != row["providerPrimaryUrl"] for row in map_payload["entries"]):
        raise DatasetValidationError("E14.7aq catalog URL binding failed.")
    try: public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(inputs["collectorPublicKey"].decode().strip()))
    except (ValueError, UnicodeDecodeError) as error: raise DatasetValidationError("E14.7aq collector public key is invalid.") from error

    receipt = _decode(collector_receipt_raw, "collector receipt")
    _validate_schema_value(receipt, receipt_schema, receipt_schema, "$")
    _verify_signed(receipt, public_key, "collector receipt")
    context = {"contractSha256": contract_hash, "catalogSha256": catalog_hash, "acquisitionRunId": contract["acquisitionRunId"], "runNonce": contract["runNonce"]}
    if any(receipt.get(key) != value for key, value in context.items()) or receipt.get("receiptId") != contract["collectorReceiptId"]:
        raise DatasetValidationError("E14.7aq collector receipt context does not match the pinned contract.")
    if contract["executionMode"] == "synthetic-test":
        if receipt["attestationType"] != "synthetic-test" or receipt["networkRequestsMade"] != 0: raise DatasetValidationError("E14.7aq synthetic receipt misstates network activity.")
    elif receipt["attestationType"] != "provider-network-capture" or receipt["networkRequestsMade"] != 79:
        raise DatasetValidationError("E14.7aq production collector receipt lacks the required network attestation.")

    root = Path(envelope_root).resolve(); entries = {row["quarterId"]: row for row in map_payload["entries"]}
    seen_requests: set[str] = set(); seen_bodies: set[str] = set(); seen_records: set[str] = set(); envelope_hashes: dict[str, str] = {}
    for record in evidence_manifest["records"]:
        if record["requestId"] in seen_requests or record["responseSha256"] in seen_bodies: raise DatasetValidationError("E14.7aq request and body identities must be unique.")
        seen_requests.add(record["requestId"]); seen_bodies.add(record["responseSha256"])
        raw = _read_nofollow(root, record["fileName"]); envelope_hashes[record["fileName"]] = _sha(raw)
        if receipt["envelopeHashes"].get(record["fileName"]) != _sha(raw): raise DatasetValidationError("E14.7aq collector receipt does not bind the envelope bytes.")
        envelope = _decode(raw, "envelope"); _validate_schema_value(envelope, envelope_schema, envelope_schema, "$"); _verify_signed(envelope, public_key, "envelope")
        expected_context = {**context, "collectorReceiptId": receipt["receiptId"]}
        if any(envelope.get(key) != value for key, value in expected_context.items()): raise DatasetValidationError("E14.7aq signed envelope context mismatch or replay.")
        for key in ("requestId", "quarterId", "requestedUrl", "finalUrl", "retrievedAtUtc", "statusCode", "contentType", "outcome", "responseSha256"):
            if envelope.get(key) != record.get(key): raise DatasetValidationError(f"E14.7aq envelope binding failed for {key}.")
        body = _body(envelope)
        if _sha(body) != record["responseSha256"] or len(body) != record["sizeBytes"] or len(body) != envelope["responseSizeBytes"]: raise DatasetValidationError("E14.7aq signed body size/hash mismatch.")
        _validate_redirects(envelope, record); entry = entries[record["quarterId"]]
        if record["quarterId"].encode() not in body or record["evidenceMarker"].encode() not in body: raise DatasetValidationError("E14.7aq signed body lacks quarter or marker.")
        if record["outcome"] == RESOLVED:
            rid = entry["archiveRecordId"]
            if rid in seen_records or rid.encode() not in body: raise DatasetValidationError("E14.7aq resolved record is invalid or reused.")
            seen_records.add(rid)
        elif b"no matching record" not in body.lower(): raise DatasetValidationError("E14.7aq signed body lacks absence proof.")
    if set(receipt["envelopeHashes"]) != set(envelope_hashes): raise DatasetValidationError("E14.7aq collector receipt envelope roster mismatch.")
    return {"report": report, "contract": contract, "contractHash": contract_hash, "catalogHash": catalog_hash, "envelopeHashes": envelope_hashes, "collectorReceiptHash": _sha(collector_receipt_raw)}


def publish_bundle_v4(contract_raw: bytes, map_payload: dict[str, Any], evidence_manifest: dict[str, Any], envelope_root: str | Path, collector_receipt_raw: bytes, target_dir: str | Path, *, inputs: dict[str, bytes], corrupt_staged_name: str | None = None) -> Path:
    result = validate_bundle_v4(contract_raw, map_payload, evidence_manifest, envelope_root, collector_receipt_raw, inputs=inputs)
    target = Path(target_dir).resolve()
    if target.exists(): raise DatasetValidationError("E14.7aq target already exists.")
    target.parent.mkdir(parents=True, exist_ok=True); staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-staging-", dir=target.parent)); root = Path(envelope_root).resolve()
    try:
        envelope_dir = staging / "envelopes"; envelope_dir.mkdir(); expected: dict[Path, bytes] = {}
        for record in evidence_manifest["records"]:
            raw = _read_nofollow(root, record["fileName"]); path = envelope_dir / record["fileName"]; path.write_bytes(raw); expected[path] = raw
        manifest_raw, map_raw = _json_bytes(evidence_manifest), _json_bytes(map_payload)
        receipt_path = staging / "e14-fdic-collector-receipt-v1.json"; receipt_path.write_bytes(collector_receipt_raw); expected[receipt_path] = collector_receipt_raw
        manifest_path = staging / "e14-fdic-archive-evidence-manifest-v1.json"; manifest_path.write_bytes(manifest_raw); expected[manifest_path] = manifest_raw
        map_path = staging / "e14-fdic-archive-quarter-map-v3.json"; map_path.write_bytes(map_raw); expected[map_path] = map_raw
        contract = result["contract"]
        audit = {"schemaVersion": 1, "artifactType": "E14FdicArchiveProducerV4BundleAudit", "status": "FDIC_ARCHIVE_CONTEXT_BOUND_EVIDENCE_BUNDLE_COMPLETE", "contractSha256": result["contractHash"], "catalogSha256": result["catalogHash"], "acquisitionRunId": contract["acquisitionRunId"], "runNonce": contract["runNonce"], "collectorReceiptSha256": result["collectorReceiptHash"], "inputHashes": {key: _sha(inputs[key]) for key in INPUT_KEYS}, "manifestSha256": _sha(manifest_raw), "mapSha256": _sha(map_raw), "envelopeHashes": result["envelopeHashes"], "envelopeCount": 79, "allStagedArtifactsRevalidated": True, "networkAttestationAccepted": contract["executionMode"] == "provider-network-capture", "nextAllowedAction": "Independent review before any downstream use."}
        audit_schema = _decode(inputs["bundleAuditSchema"], "bundle audit schema"); _validate_schema_value(audit, audit_schema, audit_schema, "$")
        audit_path = staging / "e14-fdic-archive-producer-v4-bundle-audit-v1.json"; audit_raw = _json_bytes(audit); audit_path.write_bytes(audit_raw); expected[audit_path] = audit_raw
        if corrupt_staged_name:
            match = next((path for path in expected if path.name == corrupt_staged_name), None)
            if match: match.write_bytes(b"corrupt")
        for path, raw in expected.items():
            reread = _read_nofollow(path.parent.resolve(), path.name)
            if reread != raw or _sha(reread) != _sha(raw): raise DatasetValidationError("E14.7aq staged artifact failed complete post-write verification.")
        os.replace(staging, target)
    except Exception:
        if staging.exists(): shutil.rmtree(staging)
        raise
    return target


def _read_nofollow(root: Path, name: str) -> bytes:
    path = root / name; resolved = path.resolve()
    if not resolved.is_relative_to(root) or path.is_symlink(): raise DatasetValidationError("E14.7aq path escaped root or is a symlink.")
    before = os.lstat(path); flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try: fd = os.open(path, flags)
    except OSError as error: raise DatasetValidationError("E14.7aq descriptor-based no-follow open failed.") from error
    try:
        after = os.fstat(fd)
        if not stat.S_ISREG(after.st_mode) or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino): raise DatasetValidationError("E14.7aq file changed between confinement check and open.")
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk: break
            chunks.append(chunk)
        return b"".join(chunks)
    finally: os.close(fd)


def _verify_signed(payload: dict[str, Any], key: Ed25519PublicKey, label: str) -> None:
    unsigned = dict(payload); signature = unsigned.pop("signatureBase64", None)
    try: key.verify(base64.b64decode(signature, validate=True), _canonical(unsigned))
    except (InvalidSignature, ValueError, TypeError) as error: raise DatasetValidationError(f"E14.7aq {label} signature is invalid.") from error
def _decode(raw: bytes, label: str) -> dict[str, Any]:
    try: value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error: raise DatasetValidationError(f"E14.7aq invalid {label} JSON.") from error
    if not isinstance(value, dict): raise DatasetValidationError(f"E14.7aq {label} must be an object.")
    return value
def _body(envelope: dict[str, Any]) -> bytes:
    try: return base64.b64decode(envelope["responseBodyBase64"], validate=True)
    except ValueError as error: raise DatasetValidationError("E14.7aq invalid response body base64.") from error
def _canonical(value: dict[str, Any]) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
def _sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
