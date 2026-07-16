from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .dataset import DatasetValidationError


READY = "POST_2005_SOURCE_ACQUISITION_EXECUTION_AUTHORIZED"
BLOCKED = "POST_2005_SOURCE_ACQUISITION_EXECUTION_BLOCKED"
Probe = Callable[[str, str, int, int], dict[str, Any]]


def write_e14_post2005_source_execution_gate(
    contract_path: str | Path,
    manifest_path: str | Path,
    preregistration_audit_path: str | Path,
    gate_plan_path: str | Path,
    gate_schema_path: str | Path,
    output_path: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    probe: Probe | None = None,
    executed_at_utc: str | None = None,
) -> Path:
    labels = ("gate contract", "source manifest", "preregistration audit", "gate plan", "gate schema")
    paths = (contract_path, manifest_path, preregistration_audit_path, gate_plan_path, gate_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (_, _, contract), (_, manifest_raw, manifest), (_, audit_raw, prereg), (_, plan_raw, plan), (_, schema_raw, schema) = artifacts
    actual_hashes = {
        "sourceAcquisitionManifestSha256": _sha(manifest_raw),
        "sourceAcquisitionPreregistrationAuditSha256": _sha(audit_raw),
        "executionGatePlanSha256": _sha(plan_raw),
        "executionGateSchemaSha256": _sha(schema_raw),
    }
    _validate_inputs(contract, manifest, prereg, plan, schema, actual_hashes)

    env = os.environ if environment is None else environment
    credential_results = []
    secrets: dict[str, str] = {}
    for requirement in plan["credentialRequirements"]:
        name = requirement["environmentVariable"]
        value = env.get(name, "")
        valid = bool(re.fullmatch(r"[a-z0-9]{32}", value))
        credential_results.append({
            "environmentVariable": name,
            "appliesToSourceIds": requirement["appliesToSourceIds"],
            "present": bool(value),
            "formatValid": valid,
            "secretPersisted": False,
        })
        if valid:
            secrets[name] = value

    probe_impl = _http_probe if probe is None else probe
    allowed_hosts = set(plan["networkPolicy"]["allowedHosts"])
    results = []
    network_requests = 0
    for item in plan["probes"]:
        credential_name = item["credentialEnvironmentVariable"]
        if credential_name and credential_name not in secrets:
            results.append({
                "sourceId": item["sourceId"], "urlTemplate": item["urlTemplate"],
                "attempted": False, "passed": False, "statusCode": None,
                "finalHost": None, "contentType": None, "bytesInspected": 0,
                "expectedMarkerFound": False, "failureReason": "required-credential-missing-or-invalid",
            })
            continue
        url = item["urlTemplate"]
        if credential_name:
            url = url.replace("{" + credential_name + "}", secrets[credential_name])
        network_requests += 1
        try:
            outcome = probe_impl(url, item["expectedMarker"], plan["timeoutSeconds"], plan["maximumProbeBytes"])
            final_host = urllib.parse.urlparse(outcome["finalUrl"]).hostname
            passed = (
                outcome.get("statusCode") == 200
                and outcome.get("expectedMarkerFound") is True
                and final_host in allowed_hosts
                and urllib.parse.urlparse(outcome["finalUrl"]).scheme == "https"
            )
            results.append({
                "sourceId": item["sourceId"], "urlTemplate": item["urlTemplate"],
                "attempted": True, "passed": passed, "statusCode": outcome.get("statusCode"),
                "finalHost": final_host, "contentType": outcome.get("contentType"),
                "bytesInspected": outcome.get("bytesInspected", 0),
                "expectedMarkerFound": outcome.get("expectedMarkerFound", False),
                "failureReason": None if passed else "response-or-redirect-policy-failed",
            })
        except Exception as error:  # provider/network failures are audit outcomes
            message = str(error)
            for secret in secrets.values():
                message = message.replace(secret, "[REDACTED]")
            results.append({
                "sourceId": item["sourceId"], "urlTemplate": item["urlTemplate"],
                "attempted": True, "passed": False, "statusCode": None,
                "finalHost": None, "contentType": None, "bytesInspected": 0,
                "expectedMarkerFound": False, "failureReason": message[:240] or type(error).__name__,
            })

    credentials_ready = all(item["present"] and item["formatValid"] for item in credential_results)
    probes_ready = len(results) == 7 and all(item["passed"] for item in results)
    ready = credentials_ready and probes_ready
    status = READY if ready else BLOCKED
    output = Path(output_path).resolve()
    if output.exists():
        raise DatasetValidationError("Immutable E14.7j execution-gate audit already exists.")
    executed_at = executed_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005SourceAcquisitionExecutionGateAudit",
        "status": status,
        "executedAtUtc": executed_at,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("executionGateContract", "sourceAcquisitionManifest", "preregistrationAudit", "executionGatePlan", "executionGateSchema"),
                artifacts,
            )
        },
        "inventory": {"requiredCredentialCount": len(credential_results), "sourceProbeCount": len(results), "passedProbeCount": sum(item["passed"] for item in results), "failedProbeCount": sum(not item["passed"] for item in results)},
        "credentialResults": credential_results,
        "probeResults": results,
        "checks": {"manifestHashExact": True, "preregistrationExecutionWasClosed": True, "requiredCredentialsReady": credentials_ready, "allMetadataProbesPassed": probes_ready, "secretsExcludedFromAudit": True, "redirectsStayedOnAllowlist": all(item["finalHost"] in allowed_hosts for item in results if item["passed"]), "observationsAbsent": True},
        "protocol": {"networkRequestsMade": network_requests, "metadataOnlyRequests": network_requests, "observationsAcquired": 0, "rawArtifactsWritten": 0, "featuresTransformed": 0, "candidatesGenerated": 0, "outerOosRead": False},
        "decision": {"sourceAcquisitionExecutionAuthorized": ready, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": contract["nextActionIfReady"] if ready else contract["nextActionIfBlocked"]},
        "implementation": {"module": "regime_eval.e14_post2005_source_execution_gate", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    return _write(output, _json_bytes(payload))


def _validate_inputs(contract: dict[str, Any], manifest: dict[str, Any], prereg: dict[str, Any], plan: dict[str, Any], schema: dict[str, Any], actual_hashes: dict[str, str]) -> None:
    manifest_ids = [item.get("sourceId") for item in manifest.get("sources", [])]
    probe_ids = [item.get("sourceId") for item in plan.get("probes", [])]
    expected_authorization = {"allCredentialsRequired": True, "allSevenProbesMustPass": True, "gateWritesSourceObservations": False, "gateWritesRawArtifacts": False, "successfulGateAuthorizesAcquisitionExecution": True, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False}
    if (
        contract.get("contractId") != "e14-post2005-source-execution-gate-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or not all(contract.get("decisionPolicy", {}).values())
        or manifest.get("manifestId") != "e14-post2005-source-acquisition-manifest-v1"
        or manifest.get("status") != "POST_2005_SOURCE_ACQUISITION_MANIFEST_FROZEN_EXECUTION_REQUIRES_SEPARATE_GATE"
        or manifest.get("authorizationPolicy", {}).get("sourceAcquisitionExecutionAuthorized") is not False
        or prereg.get("decision", {}).get("sourceAcquisitionExecutionAuthorized") is not False
        or prereg.get("outputs", {}).get("sourceAcquisitionManifest", {}).get("sha256") != actual_hashes["sourceAcquisitionManifestSha256"]
        or manifest_ids != contract.get("expectedSourceIds")
        or probe_ids != manifest_ids
        or plan.get("planId") != "e14-post2005-source-execution-gate-plan-v1"
        or plan.get("manifestId") != manifest.get("manifestId")
        or plan.get("authorizationPolicy") != expected_authorization
        or set(plan.get("networkPolicy", {}).get("allowedHosts", [])) != {"www.federalreserve.gov", "www.fdic.gov", "api.stlouisfed.org"}
        or plan.get("networkPolicy", {}).get("metadataOnly") is not True
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-execution-gate-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7j execution-gate inputs are invalid.")


def _http_probe(url: str, expected_marker: str, timeout: int, maximum_bytes: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "MacroRegimeResearchGate/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(maximum_bytes)
        text = raw.decode("utf-8", errors="replace")
        return {"statusCode": response.status, "finalUrl": response.geturl(), "contentType": response.headers.get("Content-Type"), "bytesInspected": len(raw), "expectedMarkerFound": expected_marker.casefold() in text.casefold()}


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7j {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write(path: Path, raw: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14.7j output exists: {path}") from error
    return path
