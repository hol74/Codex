from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_PUBLICATION_METADATA_REQUEST_CATALOG_PREREGISTERED_REVIEW_REQUIRED"
CONTRACT_SHA256 = "ca5e888cb65e7bbf93b257b2e758fd8a1b2b831ac98182cbb490ec923e19c5d6"
HASH_KEYS = (
    "collectionPreflightAuditV1Sha256",
    "metadataPreregistrationAuditV1Sha256",
    "pastQbpIndexHtmlSha256",
    "requestCatalogPlanV1Sha256",
    "requestCatalogSchemaV1Sha256",
    "auditSchemaV1Sha256",
)


def write_e14_fdic_publication_metadata_request_catalog(
    contract_path: str | Path,
    collection_preflight_audit_path: str | Path,
    metadata_preregistration_audit_path: str | Path,
    past_qbp_index_html_path: str | Path,
    request_catalog_plan_path: str | Path,
    request_catalog_schema_path: str | Path,
    audit_schema_path: str | Path,
    repository_root: str | Path,
    request_catalog_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    json_inputs = (
        (contract_path, "contract"),
        (collection_preflight_audit_path, "collection preflight audit"),
        (metadata_preregistration_audit_path, "metadata preregistration audit"),
        (request_catalog_plan_path, "request catalog plan"),
        (request_catalog_schema_path, "request catalog schema"),
        (audit_schema_path, "audit schema"),
    )
    loaded = [_read_json(path, label) for path, label in json_inputs]
    contract, preflight, preregistration, plan, catalog_schema, audit_schema = (item[2] for item in loaded)
    html_path = Path(past_qbp_index_html_path).resolve()
    try:
        html_raw = html_path.read_bytes()
        html = html_raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise DatasetValidationError(f"E14.7ac past QBP index is not readable UTF-8: {html_path}") from error

    if _sha(loaded[0][1]) != CONTRACT_SHA256:
        raise DatasetValidationError("E14.7ac request catalog contract hash is not canonical.")
    input_raw = (loaded[1][1], loaded[2][1], html_raw, loaded[3][1], loaded[4][1], loaded[5][1])
    hashes = {key: _sha(raw) for key, raw in zip(HASH_KEYS, input_raw)}
    _validate_inputs(contract, preflight, preregistration, plan, catalog_schema, audit_schema, hashes)

    root = Path(repository_root).resolve()
    catalog_output = Path(request_catalog_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    forbidden_catalog = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
    snapshot_v2 = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
    if forbidden_catalog.exists() or snapshot_v2.exists():
        raise DatasetValidationError("E14.7ac catalog v3 or snapshot v2 already exists; fail closed.")
    if catalog_output == audit_output or catalog_output.exists() or audit_output.exists():
        raise DatasetValidationError("Immutable E14.7ac output already exists or output paths collide.")

    quarter_requests = _extract_quarter_requests(html)
    templates = []
    for item in plan["requestTemplates"]:
        frozen = dict(item)
        frozen["templateSha256"] = _canonical_sha(item)
        templates.append(frozen)
    catalog = {
        "schemaVersion": 1,
        "artifactType": "E14FdicPublicationMetadataRequestCatalog",
        "requestCatalogId": "e14-fdic-publication-metadata-requests-v1",
        "status": STATUS,
        "exactSeedUrls": plan["exactSeedUrls"],
        "allowedHostsProposed": plan["allowedHostsProposed"],
        "requestTemplates": templates,
        "quarterRequests": quarter_requests,
        "authorizationPolicy": {
            "networkRequestsAuthorized": False,
            "requestCatalogPreregistered": True,
            "independentReviewRequired": True,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
        },
    }
    _validate_schema_value(catalog, catalog_schema, catalog_schema, "$")
    catalog_raw = json.dumps(catalog, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    audit = {
        "schemaVersion": 1,
        "artifactType": "E14FdicPublicationMetadataRequestCatalogAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(*loaded[0][:2]),
            "collectionPreflightAudit": _artifact(*loaded[1][:2]),
            "metadataPreregistrationAudit": _artifact(*loaded[2][:2]),
            "pastQbpIndexHtml": _artifact(html_path, html_raw),
            "requestCatalogPlan": _artifact(*loaded[3][:2]),
            "requestCatalogSchema": _artifact(*loaded[4][:2]),
            "auditSchema": _artifact(*loaded[5][:2]),
        },
        "outputs": {"requestCatalog": _artifact(catalog_output, catalog_raw)},
        "checks": {
            "allInputHashesExact": True,
            "preflightRemediationAuthorized": True,
            "quarterRosterExact": True,
            "exactSeedUrlsFrozen": True,
            "requestTemplatesHashBound": True,
            "archiveHostExtensionOnlyProposed": True,
            "catalogV3Absent": True,
            "snapshotV2Absent": True,
        },
        "inventory": {
            "quarterRequestCount": len(quarter_requests),
            "firstQuarter": quarter_requests[0]["quarterId"],
            "lastQuarter": quarter_requests[-1]["quarterId"],
            "exactSeedUrlCount": len(plan["exactSeedUrls"]),
            "requestTemplateCount": len(templates),
            "unresolvedPublicationDateCount": len(quarter_requests),
        },
        "protocol": {
            "networkRequestsMade": 0,
            "metadataRowsCollected": 0,
            "rawArtifactsWritten": 0,
            "eventTimePayloadsDownloaded": 0,
        },
        "decision": {
            "metadataRequestCatalogPreregistered": True,
            "independentReviewAuthorized": True,
            "metadataNetworkCollectionAuthorized": False,
            "archiveHostExtensionAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_fdic_publication_metadata_request_catalog",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_schema_value(audit, audit_schema, audit_schema, "$")
    audit_raw = json.dumps(audit, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    catalog_output.parent.mkdir(parents=True, exist_ok=True)
    audit_output.parent.mkdir(parents=True, exist_ok=True)
    catalog_output.write_bytes(catalog_raw)
    audit_output.write_bytes(audit_raw)
    return catalog_output, audit_output


def _extract_quarter_requests(html: str) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for block in re.finditer(r"<h2>(20\d{2})</h2>\s*<p>(.*?)</p>", html, flags=re.IGNORECASE | re.DOTALL):
        year = int(block.group(1))
        if year < 2006 or year > 2025:
            continue
        for anchor in re.finditer(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>\s*Q([1-4])\s*</a>", block.group(2), flags=re.IGNORECASE | re.DOTALL):
            quarter = int(anchor.group(2))
            quarter_id = f"{year}Q{quarter}"
            if quarter_id == "2025Q4":
                continue
            url = urljoin("https://www.fdic.gov/", anchor.group(1))
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname != "www.fdic.gov":
                raise DatasetValidationError(f"E14.7ac off-provider quarter URL: {quarter_id}")
            if quarter_id in rows:
                raise DatasetValidationError(f"E14.7ac duplicate quarter URL: {quarter_id}")
            rows[quarter_id] = {
                "quarterId": quarter_id,
                "requestId": f"fdic-qbp-{quarter_id.lower()}-metadata-v1",
                "providerPrimaryUrl": url,
                "providerHost": "www.fdic.gov",
                "evidenceState": "publication-date-unresolved",
                "usageBoundary": "metadata-publication-proof-discovery-only",
            }
    expected = [f"{year}Q{quarter}" for year in range(2006, 2026) for quarter in range(1, 5) if not (year == 2025 and quarter == 4)]
    if list(sorted(rows)) != expected:
        missing = sorted(set(expected) - set(rows))
        extra = sorted(set(rows) - set(expected))
        raise DatasetValidationError(f"E14.7ac quarter roster is not exact; missing={missing}, extra={extra}.")
    return [rows[key] for key in expected]


def _validate_inputs(contract: dict[str, Any], preflight: dict[str, Any], preregistration: dict[str, Any], plan: dict[str, Any], catalog_schema: dict[str, Any], audit_schema: dict[str, Any], hashes: dict[str, str]) -> None:
    invalid = (
        contract.get("contractId") != "e14-fdic-publication-metadata-request-catalog-contract-v1"
        or contract.get("inputHashes") != hashes
        or preflight.get("status") != "FDIC_PUBLICATION_METADATA_COLLECTION_PREFLIGHT_BLOCKED_REQUEST_CATALOG_REQUIRED"
        or preflight.get("decision", {}).get("requestCatalogRemediationAuthorized") is not True
        or preregistration.get("inventory", {}).get("requiredQuarterCount") != 79
        or plan.get("planId") != "e14-fdic-publication-metadata-request-catalog-plan-v1"
        or plan.get("allowedHostsProposed") != ["www.fdic.gov", "archive.fdic.gov"]
        or len(plan.get("exactSeedUrls", [])) != 2
        or len(plan.get("requestTemplates", [])) != 3
        or catalog_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-publication-metadata-request-catalog-v1.json"
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-publication-metadata-request-catalog-audit-v1.json"
    )
    if invalid:
        raise DatasetValidationError("E14.7ac request catalog inputs are invalid.")


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7ac {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _canonical_sha(value: Any) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
