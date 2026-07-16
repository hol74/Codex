from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_post2005_source_execution_gate_v2 import _validate_schema_value


STATUS = "FDIC_PUBLICATION_METADATA_COLLECTION_PREREGISTERED_EXECUTION_REVIEW_REQUIRED"
CONTRACT_SHA256 = "42b4c7b3b8761f956aee7eec27d1a2db230d99c8229440a1c3c0f012caba4ffc"
HASH_KEYS = (
    "remediationProposalV1Sha256",
    "remediationAuditV1Sha256",
    "independentReviewV1Sha256",
    "independentReviewSchemaV1Sha256",
    "collectionPlanV1Sha256",
    "auditSchemaV1Sha256",
)
FORBIDDEN_AUTHORIZATIONS = (
    "metadataNetworkCollectionAuthorized",
    "requestCatalogV3MaterializationAuthorized",
    "sourceAcquisitionAuthorized",
    "featureTransformationAuthorized",
    "candidateGenerationAuthorized",
    "evaluationAuthorized",
    "outerOosAuthorized",
)


def write_e14_fdic_publication_metadata_preregistration(
    contract_path: str | Path,
    remediation_proposal_path: str | Path,
    remediation_audit_path: str | Path,
    independent_review_path: str | Path,
    independent_review_schema_path: str | Path,
    collection_plan_path: str | Path,
    audit_schema_path: str | Path,
    repository_root: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "contract",
        "remediation proposal",
        "remediation audit",
        "independent review",
        "independent review schema",
        "collection plan",
        "audit schema",
    )
    paths = (
        contract_path,
        remediation_proposal_path,
        remediation_audit_path,
        independent_review_path,
        independent_review_schema_path,
        collection_plan_path,
        audit_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, proposal, audit, review, review_schema, plan, audit_schema = (
        item[2] for item in artifacts
    )
    if _sha(artifacts[0][1]) != CONTRACT_SHA256:
        raise DatasetValidationError("E14.7y metadata preregistration contract hash is not canonical.")
    hashes = {
        key: _sha(artifacts[index][1])
        for index, key in enumerate(HASH_KEYS, start=1)
    }
    _validate_inputs(contract, proposal, audit, review, review_schema, plan, audit_schema, hashes)

    root = Path(repository_root).resolve()
    output = Path(output_path).resolve()
    snapshot_root = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
    catalog_v3 = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
    if output.is_relative_to(snapshot_root):
        raise DatasetValidationError("E14.7y audit output cannot be written inside snapshot v2.")
    if catalog_v3.exists() or snapshot_root.exists():
        raise DatasetValidationError("E14.7y catalog v3 or snapshot v2 already exists; fail closed.")

    quarter_ids = _quarter_ids(2006, 1, 2025, 3)
    if len(quarter_ids) != 79 or quarter_ids[0] != "2006Q1" or quarter_ids[-1] != "2025Q3":
        raise DatasetValidationError("E14.7y computed FDIC quarter roster is not exactly 79 rows.")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FdicPublicationMetadataPreregistrationAudit",
        "status": STATUS,
        "inputs": {
            "contract": _artifact(*artifacts[0][:2]),
            "remediationProposal": _artifact(*artifacts[1][:2]),
            "remediationAudit": _artifact(*artifacts[2][:2]),
            "independentReview": _artifact(*artifacts[3][:2]),
            "reviewSchema": _artifact(*artifacts[4][:2]),
            "collectionPlan": _artifact(*artifacts[5][:2]),
            "auditSchema": _artifact(*artifacts[6][:2]),
        },
        "inventory": {
            "requiredQuarterCount": 79,
            "resolvedPublicationProofCount": 0,
            "pendingPublicationProofCount": 79,
            "firstQuarter": "2006Q1",
            "lastQuarter": "2025Q3",
        },
        "quarterIds": quarter_ids,
        "checks": {
            "allInputHashesExact": True,
            "independentReviewAccepted": True,
            "quarterRosterExact": True,
            "publicationProofGapPreserved": True,
            "providerPrimaryEvidenceRequired": True,
            "forbiddenSubstitutesExplicit": True,
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
            "metadataCollectionPreregistered": True,
            "metadataOnlyExecutionReviewAuthorized": True,
            "metadataNetworkCollectionAuthorized": False,
            "requestCatalogV3MaterializationAuthorized": False,
            "sourceAcquisitionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_fdic_publication_metadata_preregistration",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    _validate_schema_value(payload, audit_schema, audit_schema, "$")
    if output.exists():
        raise DatasetValidationError("Immutable E14.7y metadata preregistration output already exists.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return output


def _validate_inputs(
    contract: dict[str, Any],
    proposal: dict[str, Any],
    audit: dict[str, Any],
    review: dict[str, Any],
    review_schema: dict[str, Any],
    plan: dict[str, Any],
    audit_schema: dict[str, Any],
    hashes: dict[str, str],
) -> None:
    auth = contract.get("authorizationPolicy", {})
    execution = plan.get("executionPolicy", {})
    scope = plan.get("scope", {})
    completion = plan.get("completionPolicy", {})
    review_assessments = review.get("assessments", {})
    _validate_schema_value(review, review_schema, review_schema, "$")
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-fdic-publication-metadata-preregistration-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedQuarterCount") != 79
        or contract.get("expectedResolvedPublicationProofCount") != 0
        or auth.get("metadataCollectionPreregistrationAuthorized") is not True
        or auth.get("metadataOnlyExecutionReviewAuthorized") is not True
        or any(auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or proposal.get("status") != "POST_2005_ACQUISITION_REMEDIATION_PREREGISTERED_INDEPENDENT_REVIEW_REQUIRED"
        or proposal.get("openRequirements", [{}])[0].get("requiredRowCount") != 79
        or proposal.get("openRequirements", [{}])[0].get("satisfied") is not False
        or audit.get("inventory", {}).get("fdicEligibleQuarterCount") != 79
        or audit.get("inventory", {}).get("fdicResolvedPublicationProofCount") != 0
        or audit.get("decision", {}).get("requestCatalogV3MaterializationAuthorized") is not False
        or review.get("decision") != "accept"
        or review.get("proposalSha256") != hashes["remediationProposalV1Sha256"]
        or not review_assessments
        or any(value is not True for value in review_assessments.values())
        or review_schema.get("$id") != "https://macro-regime.local/schemas/e14-acquisition-remediation-independent-review-v1.json"
        or plan.get("planId") != "e14-fdic-publication-metadata-preregistration-plan-v1"
        or scope != {
            "provider": "FDIC",
            "providerHost": "www.fdic.gov",
            "firstQuarter": "2006Q1",
            "lastQuarter": "2025Q3",
            "requiredRowCount": 79,
            "evidenceKindsAllowed": [
                "provider-primary-release-page",
                "provider-primary-publication-statement",
            ],
        }
        or set(plan.get("forbiddenSubstitutes", [])) != {
            "quarter-end-date",
            "http-last-modified",
            "estimated-publication-lag",
            "non-provider-secondary-source",
        }
        or execution.get("thisStepMayUseNetwork") is not False
        or execution.get("thisStepMayWriteEvidenceRows") is not False
        or execution.get("subsequentMetadataOnlyCollectionMayBeProposed") is not True
        or any(execution.get(key) is not False for key in (
            "eventTimePayloadDownloadAuthorized",
            "requestCatalogV3MaterializationAuthorized",
            "sourceAcquisitionAuthorized",
            "featureTransformationAuthorized",
            "candidateGenerationAuthorized",
            "evaluationAuthorized",
            "outerOosAuthorized",
        ))
        or completion.get("all79RowsRequired") is not True
        or completion.get("independentReviewRequiredBeforeCatalogV3") is not True
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-fdic-publication-metadata-preregistration-audit-v1.json"
    )
    if invalid:
        raise DatasetValidationError("E14.7y metadata preregistration inputs or governance are invalid.")


def _quarter_ids(start_year: int, start_quarter: int, end_year: int, end_quarter: int) -> list[str]:
    rows: list[str] = []
    year, quarter = start_year, start_quarter
    while (year, quarter) <= (end_year, end_quarter):
        rows.append(f"{year}Q{quarter}")
        if quarter == 4:
            year, quarter = year + 1, 1
        else:
            quarter += 1
    return rows


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7y {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
