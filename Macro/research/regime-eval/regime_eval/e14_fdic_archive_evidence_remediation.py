from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_ARCHIVE_EVIDENCE_MODEL_REMEDIATED_INDEPENDENT_REVIEW_REQUIRED"
RESOLVED = "resolved-provider-archive-record"
ABSENT = "confirmed-absent-provider-primary"
HASH_KEYS = (
    "blockedReviewV1Sha256",
    "remediationPlanV2Sha256",
    "evidenceManifestSchemaV1Sha256",
    "mapSchemaV3Sha256",
    "mapAuditSchemaV3Sha256",
    "remediationAuditSchemaV1Sha256",
)


def validate_archive_map_semantics(map_payload: dict[str, Any], evidence_manifest: dict[str, Any]) -> dict[str, Any]:
    expected = _quarter_ids()
    entries = map_payload.get("entries")
    records = evidence_manifest.get("records")
    if not isinstance(entries, list) or not isinstance(records, list):
        raise DatasetValidationError("E14.7ai map entries and evidence records must be arrays.")
    entry_quarters = [item.get("quarterId") for item in entries if isinstance(item, dict)]
    record_quarters = [item.get("quarterId") for item in records if isinstance(item, dict)]
    if len(entries) != 79 or entry_quarters != expected or len(set(entry_quarters)) != 79:
        raise DatasetValidationError("E14.7ai map must contain the exact ordered unique 79-quarter roster.")
    if len(records) != 79 or record_quarters != expected or len(set(record_quarters)) != 79:
        raise DatasetValidationError("E14.7ai evidence manifest must contain the exact ordered unique 79-quarter roster.")

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        evidence_id = record.get("evidenceId")
        if not isinstance(evidence_id, str) or len(evidence_id) < 3 or evidence_id in evidence_by_id:
            raise DatasetValidationError("E14.7ai evidence IDs must be non-empty and unique.")
        _validate_evidence_provenance(record)
        evidence_by_id[evidence_id] = record

    resolved = 0
    absent = 0
    used_evidence: set[str] = set()
    for entry in entries:
        common = {"quarterId", "providerPrimaryUrl", "outcome", "evidenceId", "evidenceSha256"}
        outcome = entry.get("outcome")
        expected_keys = common | ({"archiveRecordId", "archiveUrl"} if outcome == RESOLVED else {"absenceBasis"})
        if outcome not in {RESOLVED, ABSENT} or set(entry) != expected_keys:
            raise DatasetValidationError(f"E14.7ai invalid or mixed outcome fields for {entry.get('quarterId')}.")
        _require_url(entry.get("providerPrimaryUrl"), "www.fdic.gov", "provider-primary quarter URL")
        evidence_id = entry.get("evidenceId")
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None or evidence_id in used_evidence:
            raise DatasetValidationError(f"E14.7ai missing or reused evidence for {entry.get('quarterId')}.")
        used_evidence.add(evidence_id)
        if evidence.get("quarterId") != entry.get("quarterId") or evidence.get("outcome") != outcome:
            raise DatasetValidationError(f"E14.7ai map/evidence quarter or outcome mismatch for {entry.get('quarterId')}.")
        if evidence.get("responseSha256") != entry.get("evidenceSha256"):
            raise DatasetValidationError(f"E14.7ai evidence hash mismatch for {entry.get('quarterId')}.")
        if outcome == RESOLVED:
            record_id = entry.get("archiveRecordId")
            archive_url = entry.get("archiveUrl")
            if not isinstance(record_id, str) or not record_id.isdigit():
                raise DatasetValidationError(f"E14.7ai invalid archive record ID for {entry.get('quarterId')}.")
            expected_url = f"https://archive.fdic.gov/view/fdic/{record_id}"
            if archive_url != expected_url or evidence.get("finalUrl") != archive_url or evidence.get("evidenceMarker") != "provider-archive-record":
                raise DatasetValidationError(f"E14.7ai resolved archive provenance mismatch for {entry.get('quarterId')}.")
            resolved += 1
        else:
            if not isinstance(entry.get("absenceBasis"), str) or len(entry["absenceBasis"]) < 20 or evidence.get("evidenceMarker") != "provider-no-record":
                raise DatasetValidationError(f"E14.7ai absence evidence is insufficient for {entry.get('quarterId')}.")
            absent += 1
    if used_evidence != set(evidence_by_id):
        raise DatasetValidationError("E14.7ai evidence manifest contains unused records.")
    return {
        "semanticValidationPassed": True,
        "exactRosterPassed": True,
        "uniqueQuarterIdsPassed": True,
        "evidenceProvenancePassed": True,
        "outcomeConsistencyPassed": True,
        "validatedQuarterCount": 79,
        "resolvedCount": resolved,
        "confirmedAbsentCount": absent,
    }


def validate_archive_audit_consistency(map_payload: dict[str, Any], evidence_manifest: dict[str, Any], audit_payload: dict[str, Any]) -> None:
    report = validate_archive_map_semantics(map_payload, evidence_manifest)
    inventory = audit_payload.get("inventory", {})
    validator = audit_payload.get("validatorReport", {})
    expected_inventory = {
        "quarterCount": 79,
        "resolvedCount": report["resolvedCount"],
        "confirmedAbsentCount": report["confirmedAbsentCount"],
        "unresolvedCount": 0,
        "firstQuarter": "2006Q1",
        "lastQuarter": "2025Q3",
    }
    if inventory != expected_inventory:
        raise DatasetValidationError("E14.7ai audit inventory does not match the validated map.")
    for key in ("semanticValidationPassed", "exactRosterPassed", "uniqueQuarterIdsPassed", "evidenceProvenancePassed", "outcomeConsistencyPassed", "validatedQuarterCount"):
        if validator.get(key) != report[key]:
            raise DatasetValidationError("E14.7ai audit validator report is inconsistent.")


def write_e14_fdic_archive_evidence_remediation(
    contract_path: str | Path,
    blocked_review_path: str | Path,
    remediation_plan_path: str | Path,
    evidence_manifest_schema_path: str | Path,
    map_schema_v3_path: str | Path,
    map_audit_schema_v3_path: str | Path,
    remediation_audit_schema_path: str | Path,
    repository_root: str | Path,
    output_path: str | Path,
) -> Path:
    labels = ("contract", "blocked review", "remediation plan", "evidence manifest schema", "map schema v3", "map audit schema v3", "remediation audit schema")
    paths = (contract_path, blocked_review_path, remediation_plan_path, evidence_manifest_schema_path, map_schema_v3_path, map_audit_schema_v3_path, remediation_audit_schema_path)
    artifacts = tuple(_read(path, label) for path, label in zip(paths, labels))
    contract, review, plan, evidence_schema, map_schema, map_audit_schema, audit_schema = (item[2] for item in artifacts)
    hashes = {key: _sha(artifacts[index][1]) for index, key in enumerate(HASH_KEYS, start=1)}
    _validate_inputs(contract, review, plan, evidence_schema, map_schema, map_audit_schema, audit_schema, hashes)

    root = Path(repository_root).resolve()
    output = Path(output_path).resolve()
    forbidden = (
        root / "data/historical-real-v12-2008-2025/challengers/e14-fdic-archive-provider-discovery-requests-v1.json",
        root / "data/historical-real-v12-2008-2025/challengers/e14-fdic-archive-quarter-map-v3.json",
        root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json",
        root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2",
    )
    if any(path.exists() for path in forbidden):
        raise DatasetValidationError("E14.7ai forbidden discovery, map, catalog, or snapshot artifact already exists; fail closed.")
    if output.exists():
        raise DatasetValidationError("Immutable E14.7ai remediation output already exists.")

    self_test = _run_validator_self_test()
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FdicArchiveEvidenceRemediationAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(*artifacts[0][:2]),
            "blockedReview": _artifact(*artifacts[1][:2]),
            "remediationPlan": _artifact(*artifacts[2][:2]),
            "evidenceManifestSchema": _artifact(*artifacts[3][:2]),
            "mapSchemaV3": _artifact(*artifacts[4][:2]),
            "mapAuditSchemaV3": _artifact(*artifacts[5][:2]),
            "remediationAuditSchema": _artifact(*artifacts[6][:2]),
        },
        "checks": {
            "allInputHashesExact": True,
            "blockedReviewRequiresRemediation": True,
            "providerUrlAndRequestProvenanceRequired": True,
            "singleRosterModelDefined": True,
            "auditValidatorReportRequired": True,
            "partialPublicationBlockedByValidator": True,
            "catalogV3Absent": True,
            "snapshotV2Absent": True,
        },
        "validatorSelfTest": self_test,
        "protocol": {
            "networkRequestsMade": 0,
            "discoveryCatalogsMaterialized": 0,
            "evidenceRowsCollected": 0,
            "rawArtifactsWritten": 0,
            "mapV3Materialized": False,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "evidenceModelRemediated": True,
            "semanticValidatorImplemented": True,
            "independentReviewAuthorized": True,
            "discoveryCatalogAuthorized": False,
            "executionGateAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {"module": "regime_eval.e14_fdic_archive_evidence_remediation", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    _validate_schema_value(payload, audit_schema, audit_schema, "$")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return output


def _validate_evidence_provenance(record: dict[str, Any]) -> None:
    required = {"evidenceId", "quarterId", "outcome", "requestId", "requestedUrl", "finalUrl", "redirectChain", "retrievedAtUtc", "statusCode", "contentType", "responseSha256", "sizeBytes", "fileName", "evidenceMarker"}
    if set(record) != required or record.get("outcome") not in {RESOLVED, ABSENT}:
        raise DatasetValidationError("E14.7ai evidence record shape or outcome is invalid.")
    _require_url(record.get("requestedUrl"), "archive.fdic.gov", "requested evidence URL")
    _require_url(record.get("finalUrl"), "archive.fdic.gov", "final evidence URL")
    redirects = record.get("redirectChain")
    if not isinstance(redirects, list) or len(redirects) > 8:
        raise DatasetValidationError("E14.7ai redirect chain is invalid.")
    for url in redirects:
        host = urlparse(url).hostname
        if urlparse(url).scheme != "https" or host not in {"www.fdic.gov", "archive.fdic.gov"}:
            raise DatasetValidationError("E14.7ai redirect chain leaves provider-primary hosts.")
    if not isinstance(record.get("requestId"), str) or len(record["requestId"]) < 3:
        raise DatasetValidationError("E14.7ai request identity is missing.")
    if not isinstance(record.get("retrievedAtUtc"), str) or len(record["retrievedAtUtc"]) < 20:
        raise DatasetValidationError("E14.7ai retrieval timestamp is missing.")
    if not isinstance(record.get("statusCode"), int) or not 200 <= record["statusCode"] <= 499:
        raise DatasetValidationError("E14.7ai evidence status code is invalid.")
    if not isinstance(record.get("responseSha256"), str) or re.fullmatch(r"[0-9a-f]{64}", record["responseSha256"]) is None:
        raise DatasetValidationError("E14.7ai evidence response hash is invalid.")
    if not isinstance(record.get("sizeBytes"), int) or record["sizeBytes"] < 1:
        raise DatasetValidationError("E14.7ai evidence size is invalid.")


def _require_url(value: Any, host: str, label: str) -> None:
    if not isinstance(value, str):
        raise DatasetValidationError(f"E14.7ai {label} is missing.")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != host:
        raise DatasetValidationError(f"E14.7ai {label} is off-provider.")


def _run_validator_self_test() -> dict[str, Any]:
    map_payload, manifest = _valid_fixture()
    validate_archive_map_semantics(map_payload, manifest)
    scenarios = {
        "partialRosterRejected": (lambda m, e: m["entries"].pop()),
        "duplicateQuarterRejected": (lambda m, e: m["entries"].__setitem__(1, copy.deepcopy(m["entries"][0]))),
        "provenanceMismatchRejected": (lambda m, e: e["records"][0].__setitem__("requestedUrl", "https://example.com/not-provider")),
        "outcomeMismatchRejected": (lambda m, e: e["records"][0].__setitem__("outcome", ABSENT)),
    }
    results: dict[str, bool] = {"validFixtureAccepted": True}
    for name, mutate in scenarios.items():
        candidate_map = copy.deepcopy(map_payload)
        candidate_evidence = copy.deepcopy(manifest)
        mutate(candidate_map, candidate_evidence)
        try:
            validate_archive_map_semantics(candidate_map, candidate_evidence)
        except DatasetValidationError:
            results[name] = True
        else:
            raise DatasetValidationError(f"E14.7ai validator self-test failed: {name}.")
    results["scenariosPassed"] = 5
    return results


def _valid_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    entries = []
    records = []
    for index, quarter in enumerate(_quarter_ids(), start=1):
        record_id = str(10000 + index)
        evidence_id = f"evidence-{quarter.lower()}"
        archive_url = f"https://archive.fdic.gov/view/fdic/{record_id}"
        digest = hashlib.sha256(quarter.encode("utf-8")).hexdigest()
        entries.append({"quarterId": quarter, "providerPrimaryUrl": f"https://www.fdic.gov/qbp/{quarter.lower()}.pdf", "outcome": RESOLVED, "evidenceId": evidence_id, "evidenceSha256": digest, "archiveRecordId": record_id, "archiveUrl": archive_url})
        records.append({"evidenceId": evidence_id, "quarterId": quarter, "outcome": RESOLVED, "requestId": f"request-{quarter.lower()}", "requestedUrl": archive_url, "finalUrl": archive_url, "redirectChain": [], "retrievedAtUtc": "2026-07-17T09:30:00Z", "statusCode": 200, "contentType": "text/html", "responseSha256": digest, "sizeBytes": 100, "fileName": f"{evidence_id}.html", "evidenceMarker": "provider-archive-record"})
    artifact = {"fileName": "fixture.json", "sha256": "0" * 64, "sizeBytes": 1}
    return ({"schemaVersion": 3, "artifactType": "E14FdicArchiveQuarterMap", "mapId": "e14-fdic-archive-quarter-map-v3", "status": "FDIC_ARCHIVE_QUARTER_MAP_PROVIDER_EVIDENCE_COMPLETE", "sourceCatalog": artifact, "evidenceManifest": artifact, "entries": entries, "authorizationPolicy": {"independentReviewRequired": True, "executionGateAuthorized": False, "requestCatalogV3MaterializationAuthorized": False, "sourceAcquisitionAuthorized": False}}, {"schemaVersion": 1, "artifactType": "E14FdicArchiveEvidenceManifest", "manifestId": "e14-fdic-archive-evidence-manifest-v1", "status": "FDIC_ARCHIVE_PROVIDER_EVIDENCE_COMPLETE", "records": records})


def _validate_inputs(contract: dict[str, Any], review: dict[str, Any], plan: dict[str, Any], evidence_schema: dict[str, Any], map_schema: dict[str, Any], map_audit_schema: dict[str, Any], audit_schema: dict[str, Any], hashes: dict[str, str]) -> None:
    auth = contract.get("authorizationPolicy", {})
    assessments = review.get("assessments", {})
    invalid = (
        contract.get("contractId") != "e14-fdic-archive-evidence-remediation-contract-v1"
        or contract.get("inputHashes") != hashes
        or auth.get("evidenceModelRemediationAuthorized") is not True
        or auth.get("semanticValidatorImplementationAuthorized") is not True
        or auth.get("independentReviewAuthorized") is not True
        or any(auth.get(key) is not False for key in ("networkAuthorized", "discoveryCatalogAuthorized", "executionGateAuthorized", "requestCatalogV3MaterializationAuthorized", "sourceAcquisitionAuthorized", "featureTransformationAuthorized", "candidateGenerationAuthorized", "evaluationAuthorized", "outerOosAuthorized"))
        or review.get("decision") != "needs_changes"
        or assessments.get("providerEvidenceUrlBound") is not False
        or assessments.get("complete79PartitionEnforceable") is not False
        or assessments.get("crossOutcomeUniquenessEnforceable") is not False
        or len(review.get("blockingFindings", [])) != 4
        or plan.get("planId") != "e14-fdic-archive-evidence-remediation-plan-v2"
        or evidence_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-evidence-manifest-v1.json"
        or map_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-quarter-map-v3.json"
        or map_schema.get("properties", {}).get("entries", {}).get("minItems") != 79
        or map_audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-quarter-map-audit-v3.json"
        or "validatorReport" not in map_audit_schema.get("required", [])
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-archive-evidence-remediation-audit-v1.json"
    )
    if invalid:
        raise DatasetValidationError("E14.7ai evidence remediation inputs or governance are invalid.")


def _quarter_ids() -> list[str]:
    return [f"{year}Q{quarter}" for year in range(2006, 2026) for quarter in range(1, 5) if not (year == 2025 and quarter == 4)]


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7ai {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
