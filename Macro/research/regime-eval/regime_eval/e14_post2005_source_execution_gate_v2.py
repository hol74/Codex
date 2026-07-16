from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .dataset import DatasetValidationError


READY = "POST_2005_SOURCE_V2_METADATA_GATE_PASSED_ACQUISITION_EXECUTION_SEPARATELY_AUTHORIZED"
BLOCKED = "POST_2005_SOURCE_V2_METADATA_GATE_BLOCKED"
SOURCE_IDS = ["federal-reserve-h8-release-archive", "fdic-qbp-archive", "fred-dgs2", "fred-dgs10", "federal-reserve-g5-release-archive", "fred-dcpf3m", "fred-dtb3"]
CANONICAL_HASHES = {
    "sourceAcquisitionManifestV2Sha256": "cbe3e50768381c6772a8a5b70efa04fe62fb27d4f33b5623f5f7fc8caeb128dc",
    "requestCatalogV2Sha256": "cf4d1c8643d4123ff7ac3ef3bd780766cd46f4b3fbddeda858b4682ffcc36935",
    "sourceAcquisitionPreregistrationAuditV2Sha256": "f2a2e8cfe02b89c2f10df4377623c4450466186e43ebee6ec0888da91d432827",
    "executionGatePlanV2Sha256": "dea42516f3c57061fd38d06653f54080fa65fb26f3d210cb9573eb856d63b525",
    "executionGateSchemaV2Sha256": "4bb4920ae5e8d7c665fd6ca776676506ef30e5c785163b9b461c1ed70e3d12f1",
}
GATE_CONFIGS = {
    "e14-post2005-source-execution-gate-contract-v2": {"contractSha256": "0d55deb34a52d28e240932fd0d9d5473cd6e1e7bc70bde073d781062528282f1", "planId": "e14-post2005-source-execution-gate-plan-v2", "hashes": CANONICAL_HASHES},
    "e14-post2005-source-execution-gate-contract-v3": {"contractSha256": "db9f75311d4f89dc65ec99aac259a560d439d62d43bdadf22a5671ba56daf707", "planId": "e14-post2005-source-execution-gate-plan-v3", "hashes": {**CANONICAL_HASHES, "executionGatePlanV2Sha256": "b8de2b978c529380dc3e1807df32fa0cc5ce713da2157d2b7117f48eebdbd2c6"}},
}
Probe = Callable[[str, str, int, int], dict[str, Any]]


def write_e14_post2005_source_execution_gate_v2(
    contract_path: str | Path,
    manifest_path: str | Path,
    request_catalog_path: str | Path,
    preregistration_audit_path: str | Path,
    gate_plan_path: str | Path,
    gate_schema_path: str | Path,
    output_path: str | Path,
    *,
    environment: Mapping[str, str] | None = None,
    probe: Probe | None = None,
    executed_at_utc: str | None = None,
) -> Path:
    labels = ("gate contract v2", "source manifest v2", "request catalog v2", "preregistration audit v2", "gate plan v2", "gate schema v2")
    paths = (contract_path, manifest_path, request_catalog_path, preregistration_audit_path, gate_plan_path, gate_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, manifest, catalog, prereg, plan, schema = (item[2] for item in artifacts)
    config = GATE_CONFIGS.get(contract.get("contractId"))
    if config is None or _sha(artifacts[0][1]) != config["contractSha256"]:
        raise DatasetValidationError("E14.7u execution-gate contract hash is not canonical.")
    hashes = {name: _sha(artifacts[index][1]) for index, name in enumerate(config["hashes"], start=1)}
    _validate_inputs(contract, manifest, catalog, prereg, plan, schema, hashes, config)

    env = os.environ if environment is None else environment
    credential_results: list[dict[str, Any]] = []
    secrets: dict[str, str] = {}
    for requirement in plan["credentialRequirements"]:
        name = requirement["environmentVariable"]
        value = env.get(name, "")
        valid = bool(re.fullmatch(r"[a-z0-9]{32}", value))
        credential_results.append({"environmentVariable": name, "appliesToSourceIds": requirement["appliesToSourceIds"], "present": bool(value), "formatValid": valid, "secretPersisted": False})
        if valid:
            secrets[name] = value

    probe_impl = _http_probe if probe is None else probe
    allowed_hosts = set(plan["networkPolicy"]["allowedHosts"])
    results: list[dict[str, Any]] = []
    network_requests = 0
    for item in plan["probes"]:
        credential_name = item["credentialEnvironmentVariable"]
        if credential_name and credential_name not in secrets:
            results.append(_probe_result(item, attempted=False, failure="required-credential-missing-or-invalid"))
            continue
        url = item["urlTemplate"]
        if credential_name:
            url = url.replace("{" + credential_name + "}", secrets[credential_name])
        network_requests += 1
        try:
            outcome = probe_impl(url, item["expectedMarker"], plan["timeoutSeconds"], plan["maximumProbeBytes"])
            final = urllib.parse.urlparse(str(outcome.get("finalUrl", "")))
            chain = outcome.get("redirectChain") or [url, str(outcome.get("finalUrl", ""))]
            parsed_chain = [urllib.parse.urlparse(str(value)) for value in chain]
            chain_allowed = bool(parsed_chain) and all(value.scheme == "https" and value.hostname in allowed_hosts for value in parsed_chain)
            content_type = str(outcome.get("contentType") or "").lower()
            content_valid = any(content_type.startswith(prefix) for prefix in item["acceptedContentTypePrefixes"])
            bytes_valid = 0 <= int(outcome.get("bytesInspected", -1)) <= plan["maximumProbeBytes"]
            passed = outcome.get("statusCode") == 200 and outcome.get("expectedMarkerFound") is True and chain_allowed and content_valid and bytes_valid
            results.append(_probe_result(item, attempted=True, passed=passed, outcome=outcome, final_host=final.hostname, redirect_chain_hosts=[value.hostname or "" for value in parsed_chain], failure=None if passed else "response-marker-content-size-or-redirect-policy-failed"))
        except Exception as error:  # network/provider errors are audited, not raised
            message = str(error)
            for secret in secrets.values():
                message = message.replace(secret, "[REDACTED]")
            redirect_hosts = error.hosts if isinstance(error, _RedirectPolicyError) else []
            results.append(_probe_result(item, attempted=True, redirect_chain_hosts=redirect_hosts, failure=(message[:240] or type(error).__name__)))

    credentials_ready = all(item["present"] and item["formatValid"] for item in credential_results)
    probes_ready = len(results) == 7 and all(item["passed"] for item in results)
    ready = credentials_ready and probes_ready
    output = Path(output_path).resolve()
    repository_root = Path(__file__).resolve().parents[3]
    snapshot_root = (repository_root / manifest["snapshotRoot"]).resolve()
    if output.exists() or output.is_relative_to(snapshot_root.resolve()):
        raise DatasetValidationError("E14.7u output is occupied or overlaps the protected v2 snapshot root.")

    payload = {
        "schemaVersion": 2,
        "artifactType": "E14Post2005SourceAcquisitionExecutionGateAudit",
        "status": READY if ready else BLOCKED,
        "executedAtUtc": executed_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "inputs": {name: _artifact(path, raw) for name, (path, raw, _) in zip(("executionGateContractV2", "sourceAcquisitionManifestV2", "requestCatalogV2", "preregistrationAuditV2", "executionGatePlanV2", "executionGateSchemaV2"), artifacts)},
        "inventory": {"requiredCredentialCount": len(credential_results), "sourceProbeCount": len(results), "requestTemplateCount": len(catalog["requests"]), "passedProbeCount": sum(item["passed"] for item in results), "failedProbeCount": sum(not item["passed"] for item in results), "retiredH10ReferenceCount": 0},
        "credentialResults": credential_results,
        "probeResults": results,
        "checks": {"allInputHashesExact": True, "manifestAndCatalogExact": True, "preregistrationExecutionWasClosed": True, "requestCatalogSemanticsExact": True, "h10AbsentAndG5Present": True, "requiredCredentialsReady": credentials_ready, "allMetadataProbesPassed": probes_ready, "secretsExcludedFromAudit": True, "redirectsStayedOnAllowlist": all(all(host in allowed_hosts for host in item["redirectChainHosts"]) for item in results if item["attempted"]), "observationsAndRawArtifactsAbsent": True},
        "protocol": {"networkRequestsMade": network_requests, "metadataOnlyRequests": network_requests, "requestTemplatesExecuted": 0, "observationsAcquired": 0, "rawArtifactsWritten": 0, "featuresTransformed": 0, "candidatesGenerated": 0, "evaluationPerformed": False, "outerOosRead": False},
        "decision": {"separateSourceAcquisitionExecutionAuthorized": ready, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": contract["nextActionIfReady"] if ready else contract["nextActionIfBlocked"]},
        "implementation": {"module": "regime_eval.e14_post2005_source_execution_gate_v2", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    _validate_output_shape(payload, schema)
    return _write(output, _json_bytes(payload))


def _validate_inputs(contract: dict[str, Any], manifest: dict[str, Any], catalog: dict[str, Any], prereg: dict[str, Any], plan: dict[str, Any], schema: dict[str, Any], hashes: dict[str, str], config: dict[str, Any]) -> None:
    manifest_ids = [item.get("sourceId") for item in manifest.get("sources", [])]
    probe_ids = [item.get("sourceId") for item in plan.get("probes", [])]
    request_ids = [item.get("sourceId") for item in catalog.get("requests", [])]
    g5 = next((item for item in catalog.get("requests", []) if item.get("requestId") == "g5-dated-release-expansion-v2"), {})
    fdic = next((item for item in catalog.get("requests", []) if item.get("requestId") == "fdic-qbp-publication-expansion-v2"), {})
    serialized = json.dumps((manifest, catalog, plan), sort_keys=True).lower()
    expected_authorization = {
        "allCredentialsRequired": True, "allSevenProbesMustPass": True,
        "manifestAndCatalogHashesMustMatch": True, "catalogSemanticsMustMatch": True,
        "gateWritesSourceObservations": False, "gateWritesRawArtifacts": False,
        "successfulGateAuthorizesSeparateAcquisitionExecution": True,
        "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False,
        "evaluationAuthorized": False, "outerOosAuthorized": False,
    }
    if (
        contract.get("inputHashes") != hashes or hashes != config["hashes"]
        or contract.get("expectedSourceIds") != SOURCE_IDS or contract.get("forbiddenSourceIds") != ["federal-reserve-h10-release-archive"]
        or contract.get("decisionPolicy") != {"allInputHashesMustMatchExactly": True, "preregistrationMustForbidExecution": True, "requiredCredentialsMustBePresent": True, "allMetadataProbesMustPass": True, "requestCatalogSemanticsMustMatch": True, "secretsMustNotBePersisted": True, "gateCannotWriteObservationsOrRawArtifacts": True, "failureBlocksAllAcquisition": True}
        or contract.get("nextActionIfReady") != "Execute source acquisition separately and atomically against the exact manifest v2 and request catalog v2; preserve raw bytes and release/vintage metadata; do not transform features"
        or contract.get("nextActionIfBlocked") != "Remediate only failed credential, catalog, or provider metadata checks and rerun a newly versioned gate; do not acquire any source"
        or manifest.get("manifestId") != "e14-post2005-source-acquisition-manifest-v2" or manifest_ids != SOURCE_IDS
        or catalog.get("requestCatalogId") != "e14-post2005-source-acquisition-requests-v2" or catalog.get("manifestId") != manifest.get("manifestId")
        or len(catalog.get("requests", [])) != 11 or set(request_ids) != set(SOURCE_IDS)
        or prereg.get("outputs", {}).get("sourceAcquisitionManifestV2", {}).get("sha256") != hashes["sourceAcquisitionManifestV2Sha256"]
        or prereg.get("outputs", {}).get("requestCatalogV2", {}).get("sha256") != hashes["requestCatalogV2Sha256"]
        or prereg.get("decision", {}).get("separateExecutionGateAuthorized") is not True or prereg.get("decision", {}).get("sourceAcquisitionExecutionAuthorized") is not False
        or plan.get("planId") != config["planId"] or plan.get("manifestId") != manifest.get("manifestId") or plan.get("requestCatalogId") != catalog.get("requestCatalogId")
        or probe_ids != SOURCE_IDS or set(plan.get("networkPolicy", {}).get("allowedHosts", [])) != {"www.federalreserve.gov", "www.fdic.gov", "api.stlouisfed.org"}
        or plan.get("networkPolicy", {}).get("metadataOnly") is not True or plan.get("authorizationPolicy") != expected_authorization
        or "federal-reserve-h10-release-archive" in serialized or "/h10" in serialized
        or g5.get("expansionPolicy", {}).get("expectedUniqueMonthCount") != 240 or g5.get("expansionPolicy", {}).get("duplicateOrCorrectionReleaseRequiresAdjudication") is not True
        or fdic.get("expansionPolicy", {}).get("expectedEligibleQuarterCount") != 79 or fdic.get("expansionPolicy", {}).get("lastEligibleQuarter") != "2025Q3" or fdic.get("expansionPolicy", {}).get("excludedQuarter") != "2025Q4" or fdic.get("expansionPolicy", {}).get("quarterEndCannotSubstituteForPublicationDate") is not True
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-execution-gate-audit-v2.json"
    ):
        raise DatasetValidationError("E14.7u metadata execution-gate inputs are invalid.")


def _validate_output_shape(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    expected = {"schemaVersion", "artifactType", "status", "executedAtUtc", "inputs", "inventory", "credentialResults", "probeResults", "checks", "protocol", "decision", "implementation"}
    if set(payload) != expected or len(payload["probeResults"]) != 7 or payload["protocol"]["observationsAcquired"] != 0 or payload["protocol"]["rawArtifactsWritten"] != 0:
        raise DatasetValidationError("E14.7u output shape or zero-acquisition invariant is invalid.")
    _validate_schema_value(payload, schema, schema, "$")


def _validate_schema_value(value: Any, node: dict[str, Any], root: dict[str, Any], path: str) -> None:
    if "$ref" in node:
        target: Any = root
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        _validate_schema_value(value, target, root, path)
        return
    if "const" in node and value != node["const"]:
        raise DatasetValidationError(f"E14.7u schema const failed at {path}.")
    if "enum" in node and value not in node["enum"]:
        raise DatasetValidationError(f"E14.7u schema enum failed at {path}.")
    allowed_types = node.get("type")
    if allowed_types:
        allowed_types = [allowed_types] if isinstance(allowed_types, str) else allowed_types
        matches = any((kind == "object" and isinstance(value, dict)) or (kind == "array" and isinstance(value, list)) or (kind == "string" and isinstance(value, str)) or (kind == "integer" and isinstance(value, int) and not isinstance(value, bool)) or (kind == "boolean" and isinstance(value, bool)) or (kind == "null" and value is None) for kind in allowed_types)
        if not matches:
            raise DatasetValidationError(f"E14.7u schema type failed at {path}.")
    if isinstance(value, dict) and node.get("type") == "object":
        required = set(node.get("required", []))
        properties = node.get("properties", {})
        if not required.issubset(value) or (node.get("additionalProperties") is False and not set(value).issubset(properties)):
            raise DatasetValidationError(f"E14.7u closed schema failed at {path}.")
        for key, child in value.items():
            if key in properties:
                _validate_schema_value(child, properties[key], root, f"{path}.{key}")
            elif isinstance(node.get("additionalProperties"), dict):
                _validate_schema_value(child, node["additionalProperties"], root, f"{path}.{key}")
    if isinstance(value, list) and node.get("type") == "array":
        if len(value) < node.get("minItems", 0) or len(value) > node.get("maxItems", len(value)):
            raise DatasetValidationError(f"E14.7u schema array bounds failed at {path}.")
        for index, child in enumerate(value):
            _validate_schema_value(child, node.get("items", {}), root, f"{path}[{index}]")
    if isinstance(value, int) and not isinstance(value, bool):
        if value < node.get("minimum", value) or value > node.get("maximum", value):
            raise DatasetValidationError(f"E14.7u schema numeric bounds failed at {path}.")
    if isinstance(value, str):
        if len(value) < node.get("minLength", 0) or (node.get("pattern") and not re.fullmatch(node["pattern"], value)):
            raise DatasetValidationError(f"E14.7u schema string failed at {path}.")


def _probe_result(item: dict[str, Any], *, attempted: bool, passed: bool = False, outcome: dict[str, Any] | None = None, final_host: str | None = None, redirect_chain_hosts: list[str] | None = None, failure: str | None = None) -> dict[str, Any]:
    outcome = outcome or {}
    return {"sourceId": item["sourceId"], "urlTemplate": item["urlTemplate"], "attempted": attempted, "passed": passed, "statusCode": outcome.get("statusCode"), "finalHost": final_host, "redirectChainHosts": redirect_chain_hosts or [], "contentType": outcome.get("contentType"), "bytesInspected": outcome.get("bytesInspected", 0), "expectedMarkerFound": outcome.get("expectedMarkerFound", False), "failureReason": failure}


def _http_probe(url: str, expected_marker: str, timeout: int, maximum_bytes: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "MacroRegimeResearchGate/2.0"})
    redirect_handler = _TrackingRedirectHandler(url, {"www.federalreserve.gov", "www.fdic.gov", "api.stlouisfed.org"})
    with urllib.request.build_opener(redirect_handler).open(request, timeout=timeout) as response:
        raw = response.read(maximum_bytes)
        text = raw.decode("utf-8", errors="replace")
        final_url = response.geturl()
        chain = redirect_handler.chain + ([] if redirect_handler.chain[-1] == final_url else [final_url])
        return {"statusCode": response.status, "finalUrl": final_url, "redirectChain": chain, "contentType": response.headers.get("Content-Type"), "bytesInspected": len(raw), "expectedMarkerFound": expected_marker.casefold() in text.casefold()}


class _TrackingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, initial_url: str, allowed_hosts: set[str]) -> None:
        super().__init__()
        self.chain = [initial_url]
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        self.chain.append(newurl)
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise _RedirectPolicyError([urllib.parse.urlparse(value).hostname or "" for value in self.chain])
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _RedirectPolicyError(Exception):
    def __init__(self, hosts: list[str]) -> None:
        self.hosts = hosts
        super().__init__("redirect-off-allowlist:" + hosts[-1])


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7u {label} is not valid JSON: {source}") from error


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
        raise DatasetValidationError(f"Immutable E14.7u output exists: {path}") from error
    return path
