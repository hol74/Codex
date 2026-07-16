from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .dataset import DatasetValidationError


STATUS = "POST_2005_RAW_SOURCE_SNAPSHOT_ACQUIRED_TRANSFORMATION_GATE_REQUIRED"
Downloader = Callable[[str, Path, int], dict[str, Any]]


def write_e14_post2005_atomic_source_snapshot(
    contract_path: str | Path,
    manifest_path: str | Path,
    execution_gate_audit_path: str | Path,
    request_catalog_path: str | Path,
    snapshot_schema_path: str | Path,
    repository_root: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    downloader: Downloader | None = None,
    retrieved_at_utc: str | None = None,
) -> tuple[Path, Path, Path]:
    labels = ("execution contract", "source manifest", "execution gate audit", "request catalog", "snapshot schema")
    paths = (contract_path, manifest_path, execution_gate_audit_path, request_catalog_path, snapshot_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (_, _, contract), (_, manifest_raw, manifest), (_, gate_raw, gate), (_, catalog_raw, catalog), (_, schema_raw, schema) = artifacts
    actual_hashes = {
        "sourceAcquisitionManifestSha256": _sha(manifest_raw),
        "sourceExecutionGateAuditSha256": _sha(gate_raw),
        "requestCatalogSha256": _sha(catalog_raw),
        "snapshotSchemaSha256": _sha(schema_raw),
    }
    _validate_inputs(contract, manifest, gate, catalog, schema, actual_hashes)

    repo = Path(repository_root).resolve()
    snapshot = (repo / manifest["snapshotRoot"]).resolve()
    try:
        snapshot.relative_to(repo)
    except ValueError as error:
        raise DatasetValidationError("E14.7k snapshot root escapes the repository.") from error
    stage = snapshot.parent / f".{snapshot.name}.staging"
    if snapshot.exists() or stage.exists():
        raise DatasetValidationError("E14.7k immutable snapshot or staging directory already exists.")
    if stage.parent.resolve() != snapshot.parent.resolve():
        raise DatasetValidationError("E14.7k staging directory is not a sibling of the snapshot.")

    env = os.environ if environment is None else environment
    key = env.get("FRED_API_KEY", "")
    if not re.fullmatch(r"[a-z0-9]{32}", key):
        raise DatasetValidationError("E14.7k required FRED_API_KEY is missing or invalid.")
    download = _download if downloader is None else downloader
    retrieved_at = retrieved_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    downloaded: list[dict[str, Any]] = []
    try:
        stage.mkdir(parents=True, exist_ok=False)
        for logical_request in catalog["requests"]:
            for request in _expand_request(logical_request):
                _acquire_request(request, stage, key, download, retrieved_at, downloaded)

        if len(downloaded) != contract["expectedArtifactCount"]:
            raise DatasetValidationError("E14.7k concrete artifact count differs from the frozen contract.")

        index = {
            "schemaVersion": 1,
            "artifactType": "E14Post2005AtomicSourceSnapshotIndex",
            "snapshotId": "e14-post2005-source-snapshot-v1",
            "status": STATUS,
            "retrievedAtUtc": retrieved_at,
            "inputs": {"sourceAcquisitionManifestSha256": actual_hashes["sourceAcquisitionManifestSha256"], "sourceExecutionGateAuditSha256": actual_hashes["sourceExecutionGateAuditSha256"], "requestCatalogSha256": actual_hashes["requestCatalogSha256"]},
            "inventory": {"sourceCount": len({item["sourceId"] for item in downloaded}), "artifactCount": len(downloaded), "totalSizeBytes": sum(item["sizeBytes"] for item in downloaded), "rawOnlyArtifactCount": sum(item["usageBoundary"].startswith("raw-only") for item in downloaded), "eventTimeReadyArtifactCount": sum(item["usageBoundary"].startswith("event-time") for item in downloaded)},
            "artifacts": downloaded,
            "checks": {"allRequestsCompleted": True, "allPayloadsValidated": True, "allArtifactsHashed": True, "allRedirectsOnAllowlist": True, "secretsExcluded": True, "publishedAtomically": True},
            "authorizationPolicy": {"rawSourceSnapshotAcquired": True, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False},
        }
        index_path = stage / "snapshot-index.json"
        index_path.write_bytes(_json_bytes(index))
        index_raw = index_path.read_bytes()
        audit = {
            "schemaVersion": 1,
            "artifactType": "E14Post2005AtomicSourceAcquisitionAudit",
            "status": STATUS,
            "retrievedAtUtc": retrieved_at,
            "inputs": {name: _artifact(file, raw) for name, (file, raw, _) in zip(("executionContract", "sourceAcquisitionManifest", "sourceExecutionGateAudit", "requestCatalog", "snapshotSchema"), artifacts)},
            "outputs": {"snapshotIndex": _artifact(index_path, index_raw)},
            "inventory": index["inventory"],
            "checks": {**index["checks"], "stagingRemovedByAtomicPublish": True, "sourceBytesUnmodified": True, "fredInitialReleaseMetadataPresent": all(item.get("observationCount", 0) > 0 for item in downloaded if item["contentValidation"] == "fred-initial-release-json")},
            "protocol": {"networkRequestsMade": len(downloaded), "rawArtifactsWritten": len(downloaded), "observationsParsedForValidationOnly": sum(item.get("observationCount", 0) for item in downloaded), "featuresTransformed": 0, "candidatesGenerated": 0, "outerOosRead": False},
            "decision": {"rawSnapshotComplete": True, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": contract["nextAllowedAction"]},
            "implementation": {"module": "regime_eval.e14_post2005_source_acquisition_execution", "sourceSha256": _sha(Path(__file__).read_bytes())},
        }
        audit_path = stage / "acquisition-audit.json"
        audit_path.write_bytes(_json_bytes(audit))
        stage.rename(snapshot)
        return snapshot, snapshot / "snapshot-index.json", snapshot / "acquisition-audit.json"
    except Exception as error:
        if stage.exists():
            shutil.rmtree(stage)
        message = str(error).replace(key, "[REDACTED]")
        if isinstance(error, DatasetValidationError):
            raise DatasetValidationError(message) from error
        raise DatasetValidationError(f"E14.7k atomic acquisition failed: {message}") from error


def _validate_inputs(contract: dict[str, Any], manifest: dict[str, Any], gate: dict[str, Any], catalog: dict[str, Any], schema: dict[str, Any], actual_hashes: dict[str, str]) -> None:
    requests = catalog.get("requests", [])
    counts = dict(Counter(item.get("sourceId") for item in requests))
    manifest_sources = {item.get("sourceId") for item in manifest.get("sources", [])}
    request_ids = [item.get("requestId") for item in requests]
    output_paths = [item.get("outputRelativePath") for item in requests]
    if (
        contract.get("contractId") != "e14-post2005-source-acquisition-execution-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or not all(contract.get("decisionPolicy", {}).values())
        or contract.get("expectedStatus") != STATUS
        or manifest.get("manifestId") != "e14-post2005-source-acquisition-manifest-v1"
        or gate.get("status") != "POST_2005_SOURCE_ACQUISITION_EXECUTION_AUTHORIZED"
        or gate.get("decision", {}).get("sourceAcquisitionExecutionAuthorized") is not True
        or gate.get("inputs", {}).get("sourceAcquisitionManifest", {}).get("sha256") != actual_hashes["sourceAcquisitionManifestSha256"]
        or catalog.get("requestCatalogId") != "e14-post2005-source-acquisition-requests-v1"
        or catalog.get("manifestId") != manifest.get("manifestId")
        or len(requests) != contract.get("expectedRequestCount")
        or sum(len(item.get("realtimeChunks", [None])) for item in requests) != contract.get("expectedArtifactCount")
        or counts != contract.get("expectedRequestCountBySource")
        or set(counts) != manifest_sources
        or len(request_ids) != len(set(request_ids))
        or len(output_paths) != len(set(output_paths))
        or not all(catalog.get("atomicityPolicy", {}).values())
        or catalog.get("authorizationPolicy") != {"rawSourceAcquisitionAuthorized": True, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False}
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-snapshot-index-v1.json"
    ):
        raise DatasetValidationError("E14.7k atomic acquisition inputs are invalid.")


def _expand_request(request: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = request.get("realtimeChunks")
    if not chunks:
        return [request]
    expanded = []
    for start, end in chunks:
        expanded.append({
            **request,
            "requestId": f"{request['requestId']}-{start}-{end}",
            "urlTemplate": request["urlTemplate"].replace("{REALTIME_START}", start).replace("{REALTIME_END}", end),
            "outputRelativePath": request["outputRelativePath"].replace("{REALTIME_START}", start).replace("{REALTIME_END}", end),
            "realtimeChunk": [start, end],
        })
    return expanded


def _acquire_request(
    request: dict[str, Any], stage: Path, key: str, download: Downloader,
    retrieved_at: str, downloaded: list[dict[str, Any]],
) -> None:
    destination = (stage / request["outputRelativePath"]).resolve()
    try:
        destination.relative_to(stage.resolve())
    except ValueError as error:
        raise DatasetValidationError("E14.7k request output escapes staging.") from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = request["urlTemplate"].replace("{FRED_API_KEY}", key)
    result = download(url, destination, request["maximumBytes"])
    validation = _validate_payload(destination, request["contentValidation"])
    if request.get("realtimeChunk") and not (
        request["realtimeChunk"][0] <= validation.get("vintageStart", "")
        and validation.get("vintageEnd", "9999-12-31") <= request["realtimeChunk"][1]
    ):
        raise DatasetValidationError("E14.7k FRED realtime chunk boundaries are invalid.")
    final_host = urllib.parse.urlparse(result["finalUrl"]).hostname
    if final_host not in {"www.federalreserve.gov", "www.fdic.gov", "api.stlouisfed.org"}:
        raise DatasetValidationError("E14.7k download redirected outside the provider allowlist.")
    raw = destination.read_bytes()
    artifact = {
        "requestId": request["requestId"], "sourceId": request["sourceId"],
        "relativePath": request["outputRelativePath"], "urlTemplate": request["urlTemplate"],
        "finalHost": final_host, "statusCode": result["statusCode"],
        "contentType": result.get("contentType"), "retrievedAtUtc": retrieved_at,
        "sha256": _sha(raw), "sizeBytes": len(raw),
        "contentValidation": request["contentValidation"], "usageBoundary": request["usageBoundary"],
        **validation,
    }
    if request.get("realtimeChunk"):
        artifact["realtimeChunk"] = request["realtimeChunk"]
    downloaded.append(artifact)


def _download(url: str, destination: Path, maximum_bytes: int) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "MacroRegimeResearchAcquisition/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response, destination.open("xb") as stream:
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > maximum_bytes:
                        raise DatasetValidationError("provider payload exceeds preregistered maximumBytes")
                    stream.write(chunk)
                if response.status != 200 or total == 0:
                    raise DatasetValidationError("provider returned an empty or non-200 payload")
                return {"statusCode": response.status, "finalUrl": response.geturl(), "contentType": response.headers.get("Content-Type")}
        except Exception as error:
            last_error = error
            if destination.exists():
                destination.unlink()
            if attempt < 2:
                time.sleep(attempt + 1)
    assert last_error is not None
    raise last_error


def _validate_payload(path: Path, validation: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if validation in {"zip-magic", "xlsx-magic"}:
        if not raw.startswith(b"PK"):
            raise DatasetValidationError(f"E14.7k {validation} payload has invalid magic bytes.")
        return {}
    if validation.startswith("html-"):
        text = raw.decode("utf-8", errors="replace").casefold()
        marker = {"html-h8-marker": "assets and liabilities of commercial banks", "html-qbp-marker": "quarterly banking profile", "html-h10-marker": "foreign exchange rates"}[validation]
        if marker not in text:
            raise DatasetValidationError(f"E14.7k {validation} marker is missing.")
        return {}
    if validation == "fred-initial-release-json":
        try:
            payload = json.loads(raw)
            observations = payload["observations"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise DatasetValidationError("E14.7k FRED payload is invalid JSON.") from error
        if not observations or any(not ("2006-01-01" <= item.get("date", "") <= "2025-12-31") or not item.get("realtime_start") or not item.get("realtime_end") for item in observations):
            raise DatasetValidationError("E14.7k FRED initial-release metadata or window is invalid.")
        return {
            "observationCount": len(observations),
            "observationStart": min(item["date"] for item in observations),
            "observationEnd": max(item["date"] for item in observations),
            "vintageStart": min(item["realtime_start"] for item in observations),
            "vintageEnd": max(item["realtime_start"] for item in observations),
        }
    raise DatasetValidationError("E14.7k unknown content validation policy.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7k {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
