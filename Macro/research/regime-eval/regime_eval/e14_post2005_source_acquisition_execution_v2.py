from __future__ import annotations

import hashlib
import json
import re
import shutil
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


READY = "POST_2005_SOURCE_V2_ACQUISITION_DISCOVERY_READY"
BLOCKED = "POST_2005_SOURCE_V2_ACQUISITION_BLOCKED_DISCOVERY_CATALOG_REMEDIATION_REQUIRED"
CONTRACT_SHA256 = "787517cee09475d9b1c41c54180c135d8cd81265a931d149bf941bee5d262388"
CANONICAL_HASHES = {
    "sourceAcquisitionManifestV2Sha256": "cbe3e50768381c6772a8a5b70efa04fe62fb27d4f33b5623f5f7fc8caeb128dc",
    "requestCatalogV2Sha256": "cf4d1c8643d4123ff7ac3ef3bd780766cd46f4b3fbddeda858b4682ffcc36935",
    "sourceExecutionGateAuditV3Sha256": "54f444fea108c355763044fbe060a765dd6099bc66345c33748fa21332b5b2f2",
    "executionPlanV2Sha256": "87339999e0545c818ce0bc5e5c1eb5bc83900830474ca1a3670cf377572baf84",
    "preflightSchemaV2Sha256": "bfa02a5da2b64889117d0a1f0616b41f6c8eb5d893676b556fa3ee07a6934909",
}
DISCOVERY_IDS = ["h8-release-index-v2", "fdic-qbp-publication-index-v2", "g5-release-calendar-v2"]
Fetch = Callable[[str, int], dict[str, Any]]


def write_e14_post2005_source_acquisition_execution_preflight_v2(
    contract_path: str | Path,
    manifest_path: str | Path,
    request_catalog_path: str | Path,
    gate_audit_path: str | Path,
    execution_plan_path: str | Path,
    audit_schema_path: str | Path,
    repository_root: str | Path,
    output_path: str | Path,
    *,
    fetch: Fetch | None = None,
    executed_at_utc: str | None = None,
) -> Path:
    labels = ("execution contract v2", "manifest v2", "request catalog v2", "gate audit v3", "execution plan v2", "preflight schema v2")
    paths = (contract_path, manifest_path, request_catalog_path, gate_audit_path, execution_plan_path, audit_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, manifest, catalog, gate, plan, schema = (item[2] for item in artifacts)
    if _sha(artifacts[0][1]) != CONTRACT_SHA256:
        raise DatasetValidationError("E14.7v execution contract hash is not canonical.")
    hashes = {name: _sha(artifacts[index][1]) for index, name in enumerate(CANONICAL_HASHES, start=1)}
    _validate_inputs(contract, manifest, catalog, gate, plan, schema, hashes)

    repo = Path(repository_root).resolve()
    snapshot = (repo / manifest["snapshotRoot"]).resolve()
    try:
        snapshot.relative_to(repo)
    except ValueError as error:
        raise DatasetValidationError("E14.7v snapshot root escapes the repository.") from error
    stage = snapshot.parent / f".{snapshot.name}.discovery-staging"
    output = Path(output_path).resolve()
    if snapshot.exists() or stage.exists() or output.exists() or output.is_relative_to(snapshot) or output.is_relative_to(stage):
        raise DatasetValidationError("E14.7v immutable snapshot/staging/output topology is invalid or occupied.")

    requests = {item["requestId"]: item for item in catalog["requests"]}
    fetch_impl = _fetch if fetch is None else fetch
    results: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    try:
        stage.mkdir(parents=True, exist_ok=False)
        for request_id in DISCOVERY_IDS:
            request = requests[request_id]
            outcome = fetch_impl(request["urlTemplate"], request["maximumBytes"])
            raw = outcome["raw"]
            if not isinstance(raw, bytes) or not raw or len(raw) > request["maximumBytes"]:
                raise DatasetValidationError(f"E14.7v {request_id} payload is empty, non-bytes, or oversized.")
            _validate_network_outcome(outcome, request["urlTemplate"])
            _validate_discovery_payload(raw, request["contentValidation"], outcome.get("contentType"))
            temporary = stage / request["outputRelativePath"]
            temporary.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_bytes(raw)
            payloads[request_id] = raw
            chain_hosts = [urllib.parse.urlparse(url).hostname or "" for url in outcome["redirectChain"]]
            results.append({
                "requestId": request_id, "sourceId": request["sourceId"], "urlTemplate": request["urlTemplate"],
                "statusCode": outcome["statusCode"], "finalHost": urllib.parse.urlparse(outcome["finalUrl"]).hostname,
                "redirectChainHosts": chain_hosts, "contentType": outcome.get("contentType"),
                "sizeBytes": len(raw), "sha256": _sha(raw), "payloadPersisted": False,
            })

        h8_dates = _h8_dates(payloads["h8-release-index-v2"])
        fdic_documents, fdic_publication_proofs = _fdic_discovery(payloads["fdic-qbp-publication-index-v2"])
        g5_dates, g5_months, g5_duplicates = _g5_discovery(payloads["g5-release-calendar-v2"])
        blockers: list[dict[str, Any]] = []
        if not _h8_coverage_valid(h8_dates):
            blockers.append(_blocker("H8_DIRECT_DATED_RELEASE_VALUES_INCOMPLETE", "federal-reserve-h8-release-archive", "h8-release-index-v2", len(h8_dates), 1043, "Preregister the provider H8 releaseDates.json calendar; do not infer or synthesize weekly dates"))
        if len(fdic_documents) != 79:
            blockers.append(_blocker("FDIC_ELIGIBLE_DOCUMENT_ROSTER_INCOMPLETE", "fdic-qbp-archive", "fdic-qbp-publication-index-v2", len(fdic_documents), 79, "Preregister the provider past-QBP archive as a discovery request"))
        if len(fdic_publication_proofs) != 79:
            blockers.append(_blocker("FDIC_ACTUAL_PUBLICATION_PROOFS_INCOMPLETE", "fdic-qbp-archive", "fdic-qbp-publication-index-v2", len(fdic_publication_proofs), 79, "Preregister provider-primary actual publication-date evidence for every eligible quarter; quarter end is not proof"))
        if len(g5_months) != 240:
            blockers.append(_blocker("G5_UNIQUE_MONTH_COVERAGE_INVALID", "federal-reserve-g5-release-archive", "g5-release-calendar-v2", len(g5_months), 240, "Remediate calendar coverage without backcasting or synthetic dates"))
        if g5_duplicates:
            blockers.append(_blocker("G5_DUPLICATE_MONTHS_REQUIRE_ADJUDICATION", "federal-reserve-g5-release-archive", "g5-release-calendar-v2", g5_duplicates, [], "Create an independently reviewed adjudication artifact for every duplicate/correction month before acquisition"))
    finally:
        if stage.exists():
            shutil.rmtree(stage)

    ready = not blockers
    payload = {
        "schemaVersion": 2,
        "artifactType": "E14Post2005SourceAcquisitionExecutionPreflightAudit",
        "status": READY if ready else BLOCKED,
        "executedAtUtc": executed_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "inputs": {name: _artifact(path, raw) for name, (path, raw, _) in zip(("executionContractV2", "sourceAcquisitionManifestV2", "requestCatalogV2", "sourceExecutionGateAuditV3", "executionPlanV2", "preflightSchemaV2"), artifacts)},
        "inventory": {"discoveryRequestCount": 3, "successfulDiscoveryRequestCount": len(results), "blockerCount": len(blockers), "h8DirectReleaseDateCount": len(h8_dates), "fdicEligibleDocumentCount": len(fdic_documents), "fdicActualPublicationProofCount": len(fdic_publication_proofs), "g5ReleaseCount": len(g5_dates), "g5UniqueMonthCount": len(g5_months), "g5DuplicateMonthCount": len(g5_duplicates)},
        "discoveryResults": results,
        "blockers": blockers,
        "checks": {"allInputHashesExact": True, "gateAuthorizedExactManifestAndCatalog": True, "onlyPreregisteredDiscoveryUrlsRequested": True, "allRedirectsOnAllowlist": True, "rawPayloadsDiscarded": True, "snapshotAbsent": not snapshot.exists(), "stagingAbsent": not stage.exists(), "secretValuesAbsent": True, "eventTimeAndFredRequestsNotStarted": True},
        "protocol": {"networkRequestsMade": len(results), "discoveryRequestsMade": len(results), "eventTimeRequestsMade": 0, "fredRequestsMade": 0, "rawArtifactsPublished": 0, "observationsAcquired": 0, "featuresTransformed": 0, "candidatesGenerated": 0, "evaluationPerformed": False, "outerOosRead": False},
        "decision": {"fullAtomicAcquisitionAuthorized": ready, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": contract["nextActionIfReady"] if ready else contract["nextActionIfBlocked"]},
        "implementation": {"module": "regime_eval.e14_post2005_source_acquisition_execution_v2", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    _validate_schema_value(payload, schema, schema, "$")
    return _write(output, _json_bytes(payload))


def _validate_inputs(contract: dict[str, Any], manifest: dict[str, Any], catalog: dict[str, Any], gate: dict[str, Any], plan: dict[str, Any], schema: dict[str, Any], hashes: dict[str, str]) -> None:
    requests = catalog.get("requests", [])
    by_id = {item.get("requestId"): item for item in requests}
    expected_policy = {"authorizedGateMustBindExactManifestAndCatalog": True, "discoveryMustPrecedeAllBulkAcquisition": True, "onlyFrozenDiscoveryUrlsMayBeRequested": True, "incompleteProviderDiscoveryMustFailClosed": True, "g5DuplicateMonthsRequireSeparateAdjudication": True, "failedPreflightCannotPublishRawPayloadsOrSnapshot": True, "secretsMustNotBePersisted": True, "featureTransformationRemainsForbidden": True}
    if (
        contract.get("contractId") != "e14-post2005-source-acquisition-execution-contract-v2"
        or contract.get("inputHashes") != hashes or hashes != CANONICAL_HASHES
        or contract.get("expectedDiscoveryRequestIds") != DISCOVERY_IDS or contract.get("decisionPolicy") != expected_policy
        or manifest.get("manifestId") != "e14-post2005-source-acquisition-manifest-v2"
        or catalog.get("requestCatalogId") != "e14-post2005-source-acquisition-requests-v2" or catalog.get("manifestId") != manifest.get("manifestId")
        or len(requests) != 11 or any(request_id not in by_id for request_id in DISCOVERY_IDS)
        or any(by_id[request_id].get("expansionPolicy") is not None or "{" in by_id[request_id]["urlTemplate"] for request_id in DISCOVERY_IDS)
        or gate.get("status") != "POST_2005_SOURCE_V2_METADATA_GATE_PASSED_ACQUISITION_EXECUTION_SEPARATELY_AUTHORIZED"
        or gate.get("decision", {}).get("separateSourceAcquisitionExecutionAuthorized") is not True
        or gate.get("inputs", {}).get("sourceAcquisitionManifestV2", {}).get("sha256") != hashes["sourceAcquisitionManifestV2Sha256"]
        or gate.get("inputs", {}).get("requestCatalogV2", {}).get("sha256") != hashes["requestCatalogV2Sha256"]
        or plan.get("planId") != "e14-post2005-source-acquisition-execution-plan-v2" or plan.get("discoveryFirstRequestIds") != DISCOVERY_IDS
        or not all(plan.get("discoveryPolicy", {}).values()) or plan.get("networkPolicy", {}).get("maximumLogicalRequests") != 3
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-acquisition-execution-preflight-audit-v2.json"
    ):
        raise DatasetValidationError("E14.7v acquisition preflight inputs are invalid.")


def _h8_dates(raw: bytes) -> list[str]:
    text = raw.decode("utf-8", errors="replace")
    dates = set(re.findall(r"href=[\"'][^\"']*/releases/h8/(20\d{6})/?[^\"']*[\"']", text, re.IGNORECASE))
    return sorted(date for date in dates if "20060101" <= date <= "20251231")


def _h8_coverage_valid(values: list[str]) -> bool:
    try:
        dates = [datetime.strptime(value, "%Y%m%d").date() for value in values]
    except ValueError:
        return False
    iso_weeks = {(value.isocalendar().year, value.isocalendar().week) for value in dates}
    return len(dates) == 1043 and len(iso_weeks) == 1043 and all(value.weekday() in (3, 4) for value in dates) and dates[0] <= date(2006, 1, 13) and dates[-1] >= date(2025, 12, 18)


def _fdic_discovery(raw: bytes) -> tuple[list[str], list[str]]:
    text = raw.decode("utf-8", errors="replace")
    documents: set[str] = set()
    proofs: set[str] = set()
    for match in re.finditer(r"<a\b[^>]*>", text, re.IGNORECASE):
        tag = match.group(0)
        href = re.search(r"href=[\"']([^\"']+)[\"']", tag, re.IGNORECASE)
        if not href or not re.search(r"quarterly-banking-profile|/qbp/", href.group(1), re.IGNORECASE):
            continue
        url = href.group(1)
        quarter = _quarter_from_url(url)
        if quarter and "2006Q1" <= quarter <= "2025Q3":
            documents.add(quarter)
            published = re.search(r"(?:data-publication-date|datetime)=[\"'](20\d{2}-\d{2}-\d{2})[\"']", tag, re.IGNORECASE)
            if published:
                try:
                    publication_date = date.fromisoformat(published.group(1))
                    quarter_end = date.fromisoformat(_quarter_end(quarter))
                except ValueError:
                    continue
                if quarter_end < publication_date <= quarter_end + timedelta(days=180):
                    proofs.add(quarter)
    return sorted(documents), sorted(proofs)


def _quarter_from_url(url: str) -> str | None:
    modern = re.search(r"q([1-4])[-_](20\d{2})", url, re.IGNORECASE)
    if modern:
        return f"{modern.group(2)}Q{modern.group(1)}"
    legacy = re.search(r"/(20\d{2})(mar|jun|sep|dec)/", url, re.IGNORECASE)
    if legacy:
        number = {"mar": 1, "jun": 2, "sep": 3, "dec": 4}[legacy.group(2).lower()]
        return f"{legacy.group(1)}Q{number}"
    return None


def _quarter_end(quarter: str) -> str:
    year, number = quarter.split("Q")
    return {"1": f"{year}-03-31", "2": f"{year}-06-30", "3": f"{year}-09-30", "4": f"{year}-12-31"}[number]


def _g5_discovery(raw: bytes) -> tuple[list[str], list[str], list[str]]:
    try:
        payload = json.loads(raw)
        dates = []
        for year in payload:
            for month in year["Months"]:
                if not str(month["MonthValue"]).startswith(str(year["yearValue"])):
                    raise DatasetValidationError("E14.7v G5 year/month metadata is inconsistent.")
                for release_date in month["Dates"]:
                    if not str(release_date).startswith(str(month["MonthValue"])):
                        raise DatasetValidationError("E14.7v G5 release date disagrees with MonthValue.")
                    if "20060101" <= release_date <= "20251231":
                        dates.append(release_date)
    except (json.JSONDecodeError, TypeError, KeyError) as error:
        raise DatasetValidationError("E14.7v G5 release calendar is invalid JSON.") from error
    if any(not re.fullmatch(r"20\d{6}", date) for date in dates):
        raise DatasetValidationError("E14.7v G5 release date is invalid.")
    month_counts = Counter(date[:6] for date in dates)
    return sorted(dates), sorted(month_counts), sorted(month for month, count in month_counts.items() if count > 1)


def _blocker(code: str, source_id: str, request_id: str, observed: Any, required: Any, remediation: str) -> dict[str, Any]:
    return {"code": code, "sourceId": source_id, "requestId": request_id, "observed": observed, "required": required, "remediation": remediation}


def _validate_network_outcome(outcome: dict[str, Any], initial_url: str) -> None:
    chain = outcome.get("redirectChain") or [initial_url, outcome.get("finalUrl", "")]
    initial = urllib.parse.urlparse(initial_url)
    parsed_chain = [urllib.parse.urlparse(str(url)) for url in chain]
    if outcome.get("statusCode") != 200 or not chain or initial.username or initial.password or initial.fragment or initial.port not in (None, 443) or any(value.scheme != "https" or value.hostname != initial.hostname or value.username or value.password or value.fragment or value.port not in (None, 443) for value in parsed_chain):
        raise DatasetValidationError("E14.7v discovery response or redirect chain violates policy.")


def _validate_discovery_payload(raw: bytes, validation: str, content_type: Any) -> None:
    actual_type = str(content_type or "").lower()
    if validation == "html-h8-marker":
        if not actual_type.startswith("text/html") or b"assets and liabilities of commercial banks" not in raw.lower():
            raise DatasetValidationError("E14.7v H8 discovery marker or content type is invalid.")
    elif validation == "html-qbp-marker":
        if not actual_type.startswith("text/html") or b"quarterly banking profile" not in raw.lower():
            raise DatasetValidationError("E14.7v FDIC discovery marker or content type is invalid.")
    elif validation == "json-g5-release-calendar":
        if not any(actual_type.startswith(prefix) for prefix in ("application/json", "text/json", "text/plain")):
            raise DatasetValidationError("E14.7v G5 discovery content type is invalid.")
    else:
        raise DatasetValidationError("E14.7v unrecognized discovery validation policy.")


def _fetch(url: str, maximum_bytes: int) -> dict[str, Any]:
    handler = _AllowlistRedirectHandler(url)
    request = urllib.request.Request(url, headers={"User-Agent": "MacroRegimeResearchAcquisitionPreflight/2.0"})
    with urllib.request.build_opener(handler).open(request, timeout=120) as response:
        raw = response.read(maximum_bytes + 1)
        if len(raw) > maximum_bytes:
            raise DatasetValidationError("E14.7v discovery payload exceeds preregistered maximumBytes.")
        final_url = response.geturl()
        chain = handler.chain + ([] if handler.chain[-1] == final_url else [final_url])
        return {"raw": raw, "statusCode": response.status, "finalUrl": final_url, "redirectChain": chain, "contentType": response.headers.get("Content-Type")}


class _AllowlistRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, initial_url: str) -> None:
        super().__init__()
        self.chain = [initial_url]
        self.initial_host = urllib.parse.urlparse(initial_url).hostname

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        self.chain.append(newurl)
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname != self.initial_host or parsed.username or parsed.password or parsed.fragment or parsed.port not in (None, 443):
            raise DatasetValidationError("E14.7v redirect off allowlist was refused before follow.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7v {label} is not valid JSON: {source}") from error


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
        raise DatasetValidationError(f"Immutable E14.7v output exists: {path}") from error
    return path
