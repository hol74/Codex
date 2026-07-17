from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_fdic_archive_atomic_producer import _artifact, _json_bytes
from .e14_fdic_archive_evidence_remediation import ABSENT, RESOLVED, validate_archive_audit_consistency
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_ARCHIVE_ATOMIC_PRODUCER_V2_IMPLEMENTED_INDEPENDENT_REVIEW_REQUIRED"


def validate_integrated_bundle_v2(
    map_payload: dict[str, Any], evidence_manifest: dict[str, Any], raw_root: str | Path,
    *, source_catalog_raw: bytes, source_catalog_schema_raw: bytes,
    map_schema_raw: bytes, evidence_schema_raw: bytes, map_audit_schema_raw: bytes,
    execution_gate_raw: bytes, execution_gate_schema_raw: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = _decode(source_catalog_raw, "source catalog")
    catalog_schema = _decode(source_catalog_schema_raw, "source catalog schema")
    map_schema = _decode(map_schema_raw, "map schema")
    evidence_schema = _decode(evidence_schema_raw, "evidence schema")
    audit_schema = _decode(map_audit_schema_raw, "map audit schema")
    gate = _decode(execution_gate_raw, "execution gate")
    gate_schema = _decode(execution_gate_schema_raw, "execution gate schema")
    _validate_schema_value(catalog, catalog_schema, catalog_schema, "$")
    _validate_schema_value(evidence_manifest, evidence_schema, evidence_schema, "$")
    _validate_schema_value(map_payload, map_schema, map_schema, "$")
    _validate_schema_value(gate, gate_schema, gate_schema, "$")

    from .e14_fdic_archive_atomic_producer import validate_integrated_bundle
    report = validate_integrated_bundle(
        map_payload, evidence_manifest, catalog, raw_root, map_schema,
        evidence_schema, catalog_schema, source_catalog_raw=source_catalog_raw,
    )
    if map_payload["sourceCatalog"]["sha256"] != _sha(source_catalog_raw):
        raise DatasetValidationError("E14.7am source catalog bytes are not authenticated.")

    root = Path(raw_root).resolve()
    names: set[str] = set(); hashes: set[str] = set(); archive_ids: set[str] = set()
    entries = {item["quarterId"]: item for item in map_payload["entries"]}
    for record in evidence_manifest["records"]:
        name, digest, quarter = record["fileName"], record["responseSha256"], record["quarterId"]
        if name in names or digest in hashes:
            raise DatasetValidationError("E14.7am raw file names and hashes must be unique per quarter.")
        names.add(name); hashes.add(digest)
        raw = (root / name).read_bytes()
        if quarter.encode() not in raw:
            raise DatasetValidationError("E14.7am raw evidence is not quarter-bound.")
        chain = record["redirectChain"]
        if len(chain) > 2:
            raise DatasetValidationError("E14.7am intermediate redirect hops require response-level evidence.")
        entry = entries[quarter]
        if record["outcome"] == RESOLVED:
            record_id = entry["archiveRecordId"]
            if record_id in archive_ids:
                raise DatasetValidationError("E14.7am archive record IDs must be unique.")
            archive_ids.add(record_id)
        else:
            lowered = raw.lower()
            if (record["evidenceMarker"] != "provider-no-record" or
                    b"no matching record" not in lowered or len(raw) < 32 or
                    quarter.lower() not in record["requestedUrl"].lower()):
                raise DatasetValidationError("E14.7am provider absence proof is not quarter-bound and explicit.")
    return report, {"catalog": catalog, "auditSchema": audit_schema, "gate": gate}


def publish_archive_bundle_atomic_v2(
    map_payload: dict[str, Any], evidence_manifest: dict[str, Any], raw_root: str | Path,
    target_dir: str | Path, *, source_catalog_raw: bytes, source_catalog_schema_raw: bytes,
    map_schema_raw: bytes, evidence_schema_raw: bytes, map_audit_schema_raw: bytes,
    execution_gate_raw: bytes, execution_gate_schema_raw: bytes,
    fail_before_publish: bool = False,
) -> Path:
    report, decoded = validate_integrated_bundle_v2(
        map_payload, evidence_manifest, raw_root, source_catalog_raw=source_catalog_raw,
        source_catalog_schema_raw=source_catalog_schema_raw, map_schema_raw=map_schema_raw,
        evidence_schema_raw=evidence_schema_raw, map_audit_schema_raw=map_audit_schema_raw,
        execution_gate_raw=execution_gate_raw, execution_gate_schema_raw=execution_gate_schema_raw,
    )
    target = Path(target_dir).resolve()
    if target.exists():
        raise DatasetValidationError("E14.7am atomic bundle target already exists.")
    target.parent.mkdir(parents=True, exist_ok=True)
    map_raw, manifest_raw = _json_bytes(map_payload), _json_bytes(evidence_manifest)
    audit = _build_audit(map_payload, report, map_raw, manifest_raw, source_catalog_raw,
                         map_schema_raw, evidence_schema_raw, map_audit_schema_raw,
                         execution_gate_raw)
    _validate_schema_value(audit, decoded["auditSchema"], decoded["auditSchema"], "$")
    validate_archive_audit_consistency(map_payload, evidence_manifest, audit)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-staging-", dir=target.parent))
    try:
        (staging / "raw").mkdir()
        source_root = Path(raw_root).resolve()
        for record in evidence_manifest["records"]:
            raw = (source_root / record["fileName"]).read_bytes()
            if _sha(raw) != record["responseSha256"]:
                raise DatasetValidationError("E14.7am raw evidence changed after validation.")
            (staging / "raw" / record["fileName"]).write_bytes(raw)
        (staging / "e14-fdic-archive-evidence-manifest-v1.json").write_bytes(manifest_raw)
        (staging / "e14-fdic-archive-quarter-map-v3.json").write_bytes(map_raw)
        (staging / "e14-fdic-archive-quarter-map-audit-v3.json").write_bytes(_json_bytes(audit))
        if fail_before_publish:
            raise DatasetValidationError("E14.7am injected pre-publication failure.")
        os.replace(staging, target)
    except Exception:
        if staging.exists(): shutil.rmtree(staging)
        raise
    return target


def _build_audit(map_payload: dict[str, Any], report: dict[str, Any], map_raw: bytes,
                 manifest_raw: bytes, catalog_raw: bytes, map_schema_raw: bytes,
                 evidence_schema_raw: bytes, audit_schema_raw: bytes, gate_raw: bytes) -> dict[str, Any]:
    return {
        "schemaVersion": 3, "artifactType": "E14FdicArchiveQuarterMapAudit",
        "status": "FDIC_ARCHIVE_QUARTER_MAP_PROVIDER_EVIDENCE_COMPLETE",
        "inputs": {"executionGate": _artifact(Path("execution-gate.json"), gate_raw),
                   "requestCatalog": _artifact(Path("source-catalog.json"), catalog_raw),
                   "evidenceManifest": _artifact(Path("evidence-manifest.json"), manifest_raw),
                   "mapSchema": _artifact(Path("map-schema.json"), map_schema_raw),
                   "evidenceSchema": _artifact(Path("evidence-schema.json"), evidence_schema_raw),
                   "auditSchema": _artifact(Path("audit-schema.json"), audit_schema_raw)},
        "output": _artifact(Path("map.json"), map_raw),
        "validatorReport": {"semanticValidationPassed": True, "exactRosterPassed": True,
            "uniqueQuarterIdsPassed": True, "evidenceProvenancePassed": True,
            "outcomeConsistencyPassed": True, "validatedQuarterCount": 79,
            "validatorSourceSha256": _sha(Path(__file__).read_bytes())},
        "inventory": {"quarterCount": 79, "resolvedCount": report["resolvedCount"],
            "confirmedAbsentCount": report["confirmedAbsentCount"], "unresolvedCount": 0,
            "firstQuarter": "2006Q1", "lastQuarter": "2025Q3"},
        "protocol": {"networkRequestsMade": 0, "rawEvidenceArtifactsWritten": 79, "partialOutputsPublished": 0},
        "decision": {"mapV3Materialized": True, "independentReviewAuthorized": True,
            "executionGateAuthorized": False, "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "nextAllowedAction": "Independently review producer v2 before designing discovery collection."},
        "implementation": {"module": "regime_eval.e14_fdic_archive_atomic_producer_v2",
            "sourceSha256": _sha(Path(__file__).read_bytes())},
    }


def _decode(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7am {label} bytes are not valid JSON.") from error
    if not isinstance(value, dict):
        raise DatasetValidationError(f"E14.7am {label} must decode to an object.")
    return value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
