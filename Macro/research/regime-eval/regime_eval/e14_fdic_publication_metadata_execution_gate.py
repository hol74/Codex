from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_PUBLICATION_METADATA_EXECUTION_GATE_PASSED_COLLECTION_SEPARATELY_AUTHORIZED"
CONTRACT_SHA256 = "fcdf1bdf709b2019552219a3c1f080bfb1c66133be183a2475c70addd14060f7"
HASH_KEYS = (
    "preregistrationContractV1Sha256",
    "preregistrationAuditV1Sha256",
    "independentReviewV1Sha256",
    "independentReviewSchemaV1Sha256",
    "executionPlanV1Sha256",
    "gateSchemaV1Sha256",
)


def write_e14_fdic_publication_metadata_execution_gate(
    contract_path: str | Path,
    preregistration_contract_path: str | Path,
    preregistration_audit_path: str | Path,
    independent_review_path: str | Path,
    independent_review_schema_path: str | Path,
    execution_plan_path: str | Path,
    gate_schema_path: str | Path,
    repository_root: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "execution gate contract",
        "preregistration contract",
        "preregistration audit",
        "independent review",
        "independent review schema",
        "execution plan",
        "gate schema",
    )
    paths = (
        contract_path,
        preregistration_contract_path,
        preregistration_audit_path,
        independent_review_path,
        independent_review_schema_path,
        execution_plan_path,
        gate_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, prereg_contract, prereg_audit, review, review_schema, plan, gate_schema = (
        item[2] for item in artifacts
    )
    if _sha(artifacts[0][1]) != CONTRACT_SHA256:
        raise DatasetValidationError("E14.7aa execution-gate contract hash is not canonical.")
    hashes = {
        key: _sha(artifacts[index][1])
        for index, key in enumerate(HASH_KEYS, start=1)
    }
    _validate_inputs(
        contract, prereg_contract, prereg_audit, review, review_schema,
        plan, gate_schema, hashes,
    )

    root = Path(repository_root).resolve()
    output = Path(output_path).resolve()
    snapshot_root = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
    catalog_v3 = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
    if output.is_relative_to(snapshot_root):
        raise DatasetValidationError("E14.7aa gate output cannot be inside snapshot v2.")
    if catalog_v3.exists() or snapshot_root.exists():
        raise DatasetValidationError("E14.7aa catalog v3 or snapshot v2 already exists; fail closed.")

    network = plan["networkPolicy"]
    retry = plan["retryPolicy"]
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FdicPublicationMetadataExecutionGateAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(*artifacts[0][:2]),
            "preregistrationContract": _artifact(*artifacts[1][:2]),
            "preregistrationAudit": _artifact(*artifacts[2][:2]),
            "independentReview": _artifact(*artifacts[3][:2]),
            "independentReviewSchema": _artifact(*artifacts[4][:2]),
            "executionPlan": _artifact(*artifacts[5][:2]),
            "gateSchema": _artifact(*artifacts[6][:2]),
        },
        "limits": {
            "allowedHosts": network["allowedHosts"],
            "maximumLogicalRequests": network["maximumLogicalRequests"],
            "maximumPhysicalRequests": network["maximumPhysicalRequests"],
            "maximumRedirectsPerRequest": network["maximumRedirectsPerRequest"],
            "timeoutSeconds": network["timeoutSeconds"],
            "maximumResponseBytes": network["maximumResponseBytes"],
            "acceptedContentTypePrefixes": network["acceptedContentTypePrefixes"],
            "maximumAttemptsPerLogicalRequest": retry["maximumAttemptsPerLogicalRequest"],
        },
        "checks": {
            "allInputHashesExact": True,
            "independentReviewAccepted": True,
            "quarterRosterExact": True,
            "providerHostPinned": True,
            "redirectPolicyFailClosed": True,
            "contentTypeAndByteLimitsFrozen": True,
            "retryBudgetBounded": True,
            "atomicPublicationRequired": True,
            "catalogV3Absent": True,
            "snapshotV2Absent": True,
        },
        "protocol": {
            "networkRequestsMade": 0,
            "metadataRowsCollected": 0,
            "rawArtifactsWritten": 0,
            "requestCatalogsMaterialized": 0,
            "eventTimePayloadsDownloaded": 0,
            "featuresTransformed": 0,
            "candidatesGenerated": 0,
            "evaluationPerformed": False,
            "outerOosRead": False,
        },
        "decision": {
            "metadataNetworkCollectionAuthorized": True,
            "eventTimePayloadDownloadAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_fdic_publication_metadata_execution_gate",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_schema_value(payload, gate_schema, gate_schema, "$")
    if output.exists():
        raise DatasetValidationError("Immutable E14.7aa execution-gate output already exists.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return output


def _validate_inputs(
    contract: dict[str, Any],
    prereg_contract: dict[str, Any],
    prereg_audit: dict[str, Any],
    review: dict[str, Any],
    review_schema: dict[str, Any],
    plan: dict[str, Any],
    gate_schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    network = plan.get("networkPolicy", {})
    retry = plan.get("retryPolicy", {})
    evidence = plan.get("evidencePolicy", {})
    publication = plan.get("publicationPolicy", {})
    auth = plan.get("authorizationPolicy", {})
    _validate_schema_value(review, review_schema, review_schema, "$")
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-fdic-publication-metadata-execution-gate-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("decisionPolicy") != {
            "allInputHashesMustMatchExactly": True,
            "independentReviewMustAcceptAllAssessments": True,
            "quarterRosterMustRemain79": True,
            "networkLimitsMustBeBounded": True,
            "offProviderRedirectMustFailClosed": True,
            "partialPublicationForbidden": True,
            "gateItselfMustMakeZeroNetworkRequests": True,
            "catalogV3MustRemainAbsent": True,
            "snapshotV2MustRemainAbsent": True,
        }
        or prereg_contract.get("contractId") != "e14-fdic-publication-metadata-preregistration-contract-v1"
        or prereg_contract.get("expectedQuarterCount") != 79
        or prereg_audit.get("status") != "FDIC_PUBLICATION_METADATA_COLLECTION_PREREGISTERED_EXECUTION_REVIEW_REQUIRED"
        or prereg_audit.get("inventory", {}).get("requiredQuarterCount") != 79
        or prereg_audit.get("inventory", {}).get("resolvedPublicationProofCount") != 0
        or len(prereg_audit.get("quarterIds", [])) != 79
        or review.get("decision") != "accept"
        or review.get("auditSha256") != hashes["preregistrationAuditV1Sha256"]
        or any(value is not True for value in review.get("assessments", {}).values())
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-publication-metadata-independent-review-v1.json"
        or plan.get("planId") != "e14-fdic-publication-metadata-execution-plan-v1"
        or plan.get("expectedQuarterCount") != 79
        or network != {
            "allowedHosts": ["www.fdic.gov"],
            "httpsOnly": True,
            "metadataOnly": True,
            "maximumLogicalRequests": 158,
            "maximumPhysicalRequests": 316,
            "maximumRedirectsPerRequest": 3,
            "redirectsMustRemainOnAllowedHost": True,
            "timeoutSeconds": 30,
            "maximumResponseBytes": 8388608,
            "acceptedContentTypePrefixes": ["text/html", "application/pdf"],
            "userAgent": "MacroRegimeResearchMetadataCollector/1.0",
        }
        or retry != {
            "maximumAttemptsPerLogicalRequest": 2,
            "retryableStatusCodes": [408, 429, 500, 502, 503, 504],
            "deterministicBackoffSeconds": [1],
            "retryOnContentTypeFailure": False,
            "retryOnOffProviderRedirect": False,
            "retryOnOversizeResponse": False,
        }
        or network.get("maximumPhysicalRequests") != network.get("maximumLogicalRequests") * retry.get("maximumAttemptsPerLogicalRequest", 0)
        or evidence.get("all79RowsRequired") is not True
        or evidence.get("duplicateQuarterIdsForbidden") is not True
        or set(evidence.get("forbiddenSubstitutes", [])) != {"quarter-end-date", "http-last-modified", "estimated-publication-lag", "non-provider-secondary-source"}
        or publication != {
            "stagingDirectoryName": ".e14-fdic-publication-metadata-v1.staging",
            "ledgerFileName": "e14-fdic-publication-date-ledger-v1.json",
            "auditFileName": "e14-fdic-publication-metadata-collection-audit-v1.json",
            "publishOnlyWhenAll79RowsValidate": True,
            "singleAtomicDirectoryRenameRequired": True,
            "removeStagingOnFailure": True,
            "partialLedgerPublicationForbidden": True,
            "overwriteForbidden": True,
        }
        or auth != {
            "gateMakesNetworkRequests": False,
            "successfulGateAuthorizesMetadataNetworkCollection": True,
            "eventTimePayloadDownloadAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
        }
        or gate_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-publication-metadata-execution-gate-audit-v1.json"
    )
    if invalid:
        raise DatasetValidationError("E14.7aa metadata execution-gate inputs or governance are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7aa {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
