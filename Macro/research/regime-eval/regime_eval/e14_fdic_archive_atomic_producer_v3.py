from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .dataset import DatasetValidationError
from .e14_fdic_archive_atomic_producer import _json_bytes
from .e14_fdic_archive_evidence_remediation import ABSENT, RESOLVED, validate_archive_map_semantics
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_ARCHIVE_ATOMIC_PRODUCER_V3_IMPLEMENTED_INDEPENDENT_REVIEW_REQUIRED"
INPUT_KEYS = (
    "sourceCatalog", "sourceCatalogSchema", "evidenceManifestSchema", "mapSchema",
    "bundleAuditSchema", "executionGate", "executionGateSchema", "envelopeSchema",
    "collectorPublicKey",
)


def validate_bundle_v3(
    contract_raw: bytes, trusted_contract_sha256: str, map_payload: dict[str, Any],
    evidence_manifest: dict[str, Any], envelope_root: str | Path, *, inputs: dict[str, bytes],
) -> dict[str, Any]:
    contract = _decode(contract_raw, "contract")
    if _sha(contract_raw) != trusted_contract_sha256:
        raise DatasetValidationError("E14.7ao contract does not match the trusted review hash.")
    if contract.get("contractId") != "e14-fdic-archive-atomic-producer-v3-runtime-contract-v1":
        raise DatasetValidationError("E14.7ao contract identity is invalid.")
    if set(inputs) != set(INPUT_KEYS) or contract.get("inputHashes") != {key: _sha(inputs[key]) for key in INPUT_KEYS}:
        raise DatasetValidationError("E14.7ao input bytes do not match the trusted contract.")

    catalog = _decode(inputs["sourceCatalog"], "source catalog")
    catalog_schema = _decode(inputs["sourceCatalogSchema"], "source catalog schema")
    evidence_schema = _decode(inputs["evidenceManifestSchema"], "evidence manifest schema")
    map_schema = _decode(inputs["mapSchema"], "map schema")
    gate = _decode(inputs["executionGate"], "execution gate")
    gate_schema = _decode(inputs["executionGateSchema"], "execution gate schema")
    envelope_schema = _decode(inputs["envelopeSchema"], "envelope schema")
    for value, schema in ((catalog, catalog_schema), (evidence_manifest, evidence_schema),
                          (map_payload, map_schema), (gate, gate_schema)):
        _validate_schema_value(value, schema, schema, "$")
    report = validate_archive_map_semantics(map_payload, evidence_manifest)
    if map_payload["sourceCatalog"]["sha256"] != _sha(inputs["sourceCatalog"]):
        raise DatasetValidationError("E14.7ao map is not bound to the contracted catalog bytes.")
    manifest_raw = _json_bytes(evidence_manifest)
    if map_payload["evidenceManifest"]["sha256"] != _sha(manifest_raw):
        raise DatasetValidationError("E14.7ao map is not bound to the manifest bytes.")
    urls = {row["quarterId"]: row["providerPrimaryUrl"] for row in catalog["quarterRequests"]}
    for entry in map_payload["entries"]:
        if urls.get(entry["quarterId"]) != entry["providerPrimaryUrl"]:
            raise DatasetValidationError("E14.7ao catalog URL binding failed.")

    try:
        public_key = Ed25519PublicKey.from_public_bytes(inputs["collectorPublicKey"])
    except ValueError as error:
        raise DatasetValidationError("E14.7ao collector public key is invalid.") from error
    root = Path(envelope_root).resolve()
    entries = {row["quarterId"]: row for row in map_payload["entries"]}
    seen_names: set[str] = set(); seen_requests: set[str] = set(); seen_bodies: set[str] = set(); seen_records: set[str] = set()
    envelope_hashes: dict[str, str] = {}
    for record in evidence_manifest["records"]:
        name = record["fileName"]
        if name in seen_names or record["requestId"] in seen_requests or record["responseSha256"] in seen_bodies:
            raise DatasetValidationError("E14.7ao envelope, request and response identities must be unique.")
        seen_names.add(name); seen_requests.add(record["requestId"]); seen_bodies.add(record["responseSha256"])
        raw = _read_confined(root, name)
        envelope = _decode(raw, "response envelope")
        _validate_schema_value(envelope, envelope_schema, envelope_schema, "$")
        signature = envelope.pop("signatureBase64")
        try:
            public_key.verify(base64.b64decode(signature, validate=True), _canonical(envelope))
        except (InvalidSignature, ValueError) as error:
            raise DatasetValidationError("E14.7ao response envelope signature is invalid.") from error
        envelope["signatureBase64"] = signature
        for key in ("requestId", "quarterId", "requestedUrl", "finalUrl", "retrievedAtUtc", "statusCode", "contentType", "outcome", "responseSha256"):
            if envelope[key] != record[key]:
                raise DatasetValidationError(f"E14.7ao envelope-to-manifest binding failed for {key}.")
        body = _body(envelope)
        if len(body) != record["sizeBytes"] or len(body) != envelope["responseSizeBytes"] or _sha(body) != record["responseSha256"]:
            raise DatasetValidationError("E14.7ao signed response body size/hash mismatch.")
        _validate_redirects(envelope, record)
        entry = entries[record["quarterId"]]
        if record["quarterId"].encode() not in body or record["evidenceMarker"].encode() not in body:
            raise DatasetValidationError("E14.7ao signed response body lacks quarter or evidence marker.")
        if record["outcome"] == RESOLVED:
            record_id = entry["archiveRecordId"]
            if record_id in seen_records or record_id.encode() not in body:
                raise DatasetValidationError("E14.7ao resolved record identity is invalid or reused.")
            seen_records.add(record_id)
        elif b"no matching record" not in body.lower():
            raise DatasetValidationError("E14.7ao signed provider response lacks explicit absence evidence.")
        envelope_hashes[name] = _sha(raw)
    return {"semanticReport": report, "envelopeHashes": envelope_hashes, "contractSha256": trusted_contract_sha256}


def publish_bundle_v3(
    contract_raw: bytes, trusted_contract_sha256: str, map_payload: dict[str, Any],
    evidence_manifest: dict[str, Any], envelope_root: str | Path, target_dir: str | Path,
    *, inputs: dict[str, bytes], fail_before_publish: bool = False,
    corrupt_staged_index: int | None = None,
) -> Path:
    result = validate_bundle_v3(contract_raw, trusted_contract_sha256, map_payload, evidence_manifest, envelope_root, inputs=inputs)
    target = Path(target_dir).resolve()
    if target.exists(): raise DatasetValidationError("E14.7ao target already exists.")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-staging-", dir=target.parent))
    source_root = Path(envelope_root).resolve()
    try:
        (staging / "envelopes").mkdir()
        for index, record in enumerate(evidence_manifest["records"]):
            raw = _read_confined(source_root, record["fileName"])
            destination = staging / "envelopes" / record["fileName"]
            destination.write_bytes(raw)
            if corrupt_staged_index == index: destination.write_bytes(b"corrupt")
            copied = _read_confined((staging / "envelopes").resolve(), record["fileName"])
            if _sha(copied) != result["envelopeHashes"][record["fileName"]] or copied != raw:
                raise DatasetValidationError("E14.7ao staged envelope failed post-write verification.")
        manifest_raw, map_raw = _json_bytes(evidence_manifest), _json_bytes(map_payload)
        (staging / "e14-fdic-archive-evidence-manifest-v1.json").write_bytes(manifest_raw)
        (staging / "e14-fdic-archive-quarter-map-v3.json").write_bytes(map_raw)
        audit = {"schemaVersion": 1, "artifactType": "E14FdicArchiveProducerV3BundleAudit",
                 "status": "FDIC_ARCHIVE_SIGNED_EVIDENCE_BUNDLE_COMPLETE",
                 "contractSha256": trusted_contract_sha256,
                 "inputHashes": {key: _sha(inputs[key]) for key in INPUT_KEYS},
                 "manifestSha256": _sha(manifest_raw), "mapSha256": _sha(map_raw),
                 "envelopeHashes": result["envelopeHashes"], "envelopeCount": 79,
                 "postWriteVerificationPassed": True, "networkRequestsMade": 0,
                 "nextAllowedAction": "Independent review before downstream use."}
        audit_schema = _decode(inputs["bundleAuditSchema"], "bundle audit schema")
        _validate_schema_value(audit, audit_schema, audit_schema, "$")
        (staging / "e14-fdic-archive-producer-v3-bundle-audit-v1.json").write_bytes(_json_bytes(audit))
        if fail_before_publish: raise DatasetValidationError("E14.7ao injected pre-publication failure.")
        os.replace(staging, target)
    except Exception:
        if staging.exists(): shutil.rmtree(staging)
        raise
    return target


def _validate_redirects(envelope: dict[str, Any], record: dict[str, Any]) -> None:
    redirects = envelope["redirects"]
    if not redirects:
        if record["requestedUrl"] != record["finalUrl"] or record["redirectChain"]:
            raise DatasetValidationError("E14.7ao redirect receipt is missing.")
        return
    nodes = [redirects[0]["fromUrl"]]
    for hop in redirects:
        if nodes[-1] != hop["fromUrl"] or hop["location"] != hop["toUrl"]:
            raise DatasetValidationError("E14.7ao redirect receipt continuity failed.")
        nodes.append(hop["toUrl"])
    if nodes[0] != record["requestedUrl"] or nodes[-1] != record["finalUrl"] or nodes != record["redirectChain"]:
        raise DatasetValidationError("E14.7ao redirect receipt does not bind the manifest chain.")


def _read_confined(root: Path, name: str) -> bytes:
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise DatasetValidationError("E14.7ao envelope path escaped its root or is not a regular file.")
    return path.read_bytes()


def _decode(raw: bytes, label: str) -> dict[str, Any]:
    try: value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error: raise DatasetValidationError(f"E14.7ao invalid {label} JSON.") from error
    if not isinstance(value, dict): raise DatasetValidationError(f"E14.7ao {label} must be an object.")
    return value


def _body(envelope: dict[str, Any]) -> bytes:
    try: return base64.b64decode(envelope["responseBodyBase64"], validate=True)
    except ValueError as error: raise DatasetValidationError("E14.7ao response body is not valid base64.") from error


def _canonical(value: dict[str, Any]) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
def _sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
