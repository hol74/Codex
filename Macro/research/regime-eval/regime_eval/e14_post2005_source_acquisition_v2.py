from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "POST_2005_SOURCE_MANIFEST_V2_AND_REQUEST_CATALOG_V2_PREREGISTERED_EXECUTION_GATE_REQUIRED"
NEXT_ACTION = "Run a separate fail-closed metadata execution gate against manifest v2 and request catalog v2; do not acquire observations yet"
SOURCE_IDS = ["federal-reserve-h8-release-archive", "fdic-qbp-archive", "fred-dgs2", "fred-dgs10", "federal-reserve-g5-release-archive", "fred-dcpf3m", "fred-dtb3"]
FAMILY_IDS = ["bank-release-archived-balance-sheet-post2005-v2", "broad-treasury-rate-dislocation-post2005", "cross-g5-dollar-shock-post2005-v2", "funding-financial-cp-tiering-post2005"]
CANONICAL_HASHES = {
    "activeSourceVintagePolicyV2Sha256": "94db6eb64b83ea3d54ca36c8d3311f983ab48f998c4b6bb9e7218df8aad049fd",
    "policyActivationAuditSha256": "0c86c0545cddc580680804b4b3c0b701718450fd818381a19d435d94071c3d2f",
    "baseActiveTaxonomySha256": "3f69670e43315904e47a9bcae1957c62d780665b047355230198bb7a129e9d58",
    "scopeActivationAuditSha256": "77b38fe8be5c6fa235d4d68437ae0c184fa70eab7ea23d5839def575c112e9db",
    "legacySourceManifestV1Sha256": "2203aba40264054476a28b6c162e5eecc7346563bfb8a26f1339e65033881b90",
    "sourceAcquisitionEvidenceV2Sha256": "8d7c9e386c6a3adfce60e5f83acd0d14cc73c13ef2582cfb6519440671e446ef",
    "sourceAcquisitionPlanV2Sha256": "30572d4d2ac7332714b4f08b877e9567c49ddeb729ca2d043bd953c8acff23e4",
    "manifestSchemaV2Sha256": "c094f12716d83581382f566d5399775b041cd4e1d7f2f791a1f98824c0cf4b4b",
    "requestCatalogSchemaV2Sha256": "9cf67d3f0692494287c2f79426a1e45e3cd5dc913aa4e4aed3701627a44de58a",
    "preregistrationAuditSchemaV2Sha256": "5d4e5257d0c830e3de13a28b647747ae8cd6a234dc83a0fb025ac682f37deac2",
}
DECISION_POLICY = {
    "activePolicyV2AndBaseScopeMustBeExact": True,
    "h10MustBeAbsentFromManifestCatalogAndRawPaths": True,
    "g5RegimesAndNoBackcastPolicyMustBeFrozen": True,
    "g5MustRequire240UniqueMonthsAndDuplicateAdjudication": True,
    "fdicMustRequire79EligibleQuartersThrough2025Q3": True,
    "fdicQuarterEndCannotSubstituteForPublicationDate": True,
    "allSevenSourcesMustRemainMetadataReady": True,
    "manifestAndCatalogCannotMakeNetworkRequests": True,
    "executionRequiresSeparateGate": True,
    "legacyManifestAndSnapshotRemainImmutable": True,
}
AUTHORIZATION_POLICY = {
    "manifestAndRequestCatalogMaterializationAuthorized": True,
    "separateMetadataExecutionGateAuthorized": True,
    "networkRequestsAuthorized": False,
    "sourceAcquisitionExecutionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
MANIFEST_AUTHORIZATION = {
    "manifestAndRequestCatalogMaterializationAuthorized": True,
    "networkRequestsAuthorized": False,
    "sourceAcquisitionExecutionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
CATALOG_AUTHORIZATION = {
    "requestCatalogPreregistered": True,
    "networkRequestsAuthorized": False,
    "rawSourceAcquisitionAuthorized": False,
    "featureTransformationAuthorized": False,
    "candidateGenerationAuthorized": False,
    "evaluationAuthorized": False,
    "outerOosAuthorized": False,
}
ATOMICITY_POLICY = {
    "downloadToSiblingStagingDirectory": True,
    "validateBeforePublish": True,
    "publishBySingleDirectoryRename": True,
    "deleteStagingOnFailure": True,
    "existingSnapshotFailsClosed": True,
    "secretValuesExcludedFromFilesAndMetadata": True,
}
INTEGRITY_POLICY = {
    "providerPrimaryLocatorRequired": True,
    "rawBytesPreserved": True,
    "sha256Required": True,
    "retrievedAtUtcRequired": True,
    "releaseOrVintageMetadataRequired": True,
    "providerDiscoveredExpansionOnly": True,
    "partialAcquisitionFailsClosed": True,
    "unexpectedMethodologyBreakFailsClosed": True,
    "legacySnapshotReuseForbidden": True,
}


def write_e14_post2005_source_acquisition_v2(
    contract_path: str | Path,
    active_policy_path: str | Path,
    policy_activation_audit_path: str | Path,
    base_taxonomy_path: str | Path,
    scope_activation_audit_path: str | Path,
    legacy_manifest_path: str | Path,
    evidence_path: str | Path,
    plan_path: str | Path,
    manifest_schema_path: str | Path,
    request_schema_path: str | Path,
    audit_schema_path: str | Path,
    manifest_output_path: str | Path,
    request_catalog_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path, Path]:
    labels = ("contract", "active policy v2", "policy activation audit", "base active taxonomy", "scope activation audit", "legacy manifest v1", "source evidence v2", "source plan v2", "manifest schema v2", "request schema v2", "audit schema v2")
    paths = (contract_path, active_policy_path, policy_activation_audit_path, base_taxonomy_path, scope_activation_audit_path, legacy_manifest_path, evidence_path, plan_path, manifest_schema_path, request_schema_path, audit_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    contract, policy, activation_audit, taxonomy, scope_audit, legacy_manifest, evidence, plan, manifest_schema, request_schema, audit_schema = (item[2] for item in artifacts)
    hashes = {
        name: _sha(artifacts[index][1])
        for index, name in enumerate(CANONICAL_HASHES, start=1)
    }
    _validate_inputs(contract, policy, activation_audit, taxonomy, scope_audit, legacy_manifest, evidence, plan, manifest_schema, request_schema, audit_schema, hashes, artifacts)

    evidence_by_id = {item["sourceId"]: item for item in evidence["sources"]}
    sources = []
    for source in plan["sources"]:
        readiness = evidence_by_id[source["sourceId"]]
        sources.append({
            **source,
            "providerPrimaryLocators": readiness["evidenceUrls"],
            "coverageFrom": readiness["coverageFrom"],
            "readinessEvidence": {key: readiness[key] for key in ("providerPrimaryPageReachable", "licensingCleared", "componentCoverageVerified", "releaseProofComplete", "vintageProofComplete", "methodologyManifestFeasible")},
        })

    manifest = {
        "schemaVersion": 2,
        "artifactType": "E14Post2005SourceAcquisitionManifest",
        "manifestId": "e14-post2005-source-acquisition-manifest-v2",
        "activePolicy": _artifact(artifacts[1][0], artifacts[1][1]),
        "activationAudit": _artifact(artifacts[2][0], artifacts[2][1]),
        "baseTaxonomy": _artifact(artifacts[3][0], artifacts[3][1]),
        "supersedesManifest": _artifact(artifacts[5][0], artifacts[5][1]),
        "window": plan["window"],
        "snapshotRoot": plan["snapshotRoot"],
        "sources": sources,
        "featureFamilies": plan["featureFamilies"],
        "integrityPolicy": plan["integrityPolicy"],
        "authorizationPolicy": MANIFEST_AUTHORIZATION,
        "status": STATUS,
    }
    catalog = {
        "schemaVersion": 2,
        "artifactType": "E14Post2005SourceAcquisitionRequestCatalog",
        "requestCatalogId": "e14-post2005-source-acquisition-requests-v2",
        "manifestId": "e14-post2005-source-acquisition-manifest-v2",
        "activePolicy": _artifact(artifacts[1][0], artifacts[1][1]),
        "snapshotRoot": plan["snapshotRoot"],
        "requests": plan["requests"],
        "atomicityPolicy": ATOMICITY_POLICY,
        "authorizationPolicy": CATALOG_AUTHORIZATION,
        "status": STATUS,
    }
    manifest_raw = _json_bytes(manifest)
    catalog_raw = _json_bytes(catalog)
    outputs = tuple(Path(path).resolve() for path in (manifest_output_path, request_catalog_output_path, audit_output_path))
    expected_names = ("e14-post2005-source-acquisition-manifest-v2.json", "e14-post2005-source-acquisition-requests-v2.json", "e14-post2005-source-acquisition-preregistration-audit-v2.json")
    protected_parent = artifacts[2][0].parent
    protected_roots = (
        protected_parent / "completed-policy-redesign-receipts-v1",
        protected_parent / "e14-post2005-policy-redesign-dossiers-v1",
        protected_parent / "e14-post2005-policy-redesign-review-handoff-v1",
        protected_parent.parent / "post2005-source-snapshots-v1",
        protected_parent.parent / "post2005-source-snapshots-v2",
    )
    if (
        tuple(path.name for path in outputs) != expected_names
        or len(set(outputs)) != 3
        or any(path.exists() for path in outputs)
        or any(path in {item[0] for item in artifacts} for path in outputs)
        or any(path.is_relative_to(root.resolve()) for path in outputs for root in protected_roots)
    ):
        raise DatasetValidationError("E14.7t output path is invalid, occupied, or overlaps protected evidence/snapshots.")

    audit = {
        "schemaVersion": 2,
        "artifactType": "E14Post2005SourceAcquisitionPreregistrationAudit",
        "status": STATUS,
        "inputs": {name: _artifact(file, raw) for name, (file, raw, _) in zip(("acquisitionContractV2", "activeSourceVintagePolicyV2", "policyActivationAudit", "baseActiveTaxonomy", "scopeActivationAudit", "legacySourceManifestV1", "sourceAcquisitionEvidenceV2", "sourceAcquisitionPlanV2", "manifestSchemaV2", "requestCatalogSchemaV2", "preregistrationAuditSchemaV2"), artifacts)},
        "outputs": {"sourceAcquisitionManifestV2": _artifact(outputs[0], manifest_raw), "requestCatalogV2": _artifact(outputs[1], catalog_raw)},
        "inventory": {
            "sourceCount": len(sources),
            "featureFamilyCount": len(plan["featureFamilies"]),
            "requestTemplateCount": len(plan["requests"]),
            "retiredH10ReferenceCount": _count_h10(manifest) + _count_h10(catalog),
            "providerPrimaryLocatorCount": sum(len(item["providerPrimaryLocators"]) for item in sources),
        },
        "checks": {
            "allInputHashesExact": True,
            "activePolicyV2Exact": True,
            "baseTaxonomyAndLabelsUnchanged": True,
            "legacyManifestV1Unchanged": True,
            "exactSevenSourceRoster": True,
            "h10AbsentFromManifestCatalogAndRawPaths": True,
            "g5ReplacesH10": True,
            "g5MethodologyRegimesFrozen": True,
            "g5UniqueMonthCoverageRequirementFrozen": True,
            "fdicActualPublicationProofFrozen": True,
            "fdicEligibleQuarterBoundaryFrozen": True,
            "allSourcesMetadataReady": True,
            "outputsSchemaClosed": True,
            "networkRequestsAbsent": True,
        },
        "protocol": {"manifestFrozen": True, "requestCatalogFrozen": True, "networkRequestsMade": 0, "observationsAcquired": 0, "rawArtifactsWritten": 0, "featuresTransformed": 0, "candidatesGenerated": 0, "evaluationPerformed": False, "outerOosRead": False},
        "decision": {"manifestAndRequestCatalogReady": True, "separateExecutionGateAuthorized": True, "sourceAcquisitionExecutionAuthorized": False, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": NEXT_ACTION},
        "implementation": {"module": "regime_eval.e14_post2005_source_acquisition_v2", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    _validate_outputs(manifest, catalog, audit)
    _write_many(((outputs[0], manifest_raw), (outputs[1], catalog_raw), (outputs[2], _json_bytes(audit))))
    return outputs


def _validate_inputs(contract: dict[str, Any], policy: dict[str, Any], activation_audit: dict[str, Any], taxonomy: dict[str, Any], scope_audit: dict[str, Any], legacy_manifest: dict[str, Any], evidence: dict[str, Any], plan: dict[str, Any], manifest_schema: dict[str, Any], request_schema: dict[str, Any], audit_schema: dict[str, Any], hashes: dict[str, str], artifacts: list[tuple[Path, bytes, dict[str, Any]]]) -> None:
    source_ids = [item.get("sourceId") for item in plan.get("sources", [])]
    evidence_ids = [item.get("sourceId") for item in evidence.get("sources", [])]
    family_ids = [item.get("familyId") for item in plan.get("featureFamilies", [])]
    request_ids = [item.get("requestId") for item in plan.get("requests", [])]
    request_sources = {item.get("sourceId") for item in plan.get("requests", [])}
    family_sources = {source for family in plan.get("featureFamilies", []) for source in family.get("sourceIds", [])}
    readiness_keys = ("providerPrimaryPageReachable", "licensingCleared", "componentCoverageVerified", "releaseProofComplete", "vintageProofComplete", "methodologyManifestFeasible")
    evidence_by_id = {item.get("sourceId"): item for item in evidence.get("sources", [])}
    cross = next((item for item in plan.get("featureFamilies", []) if item.get("mechanism") == "cross-border-growth"), {})
    bank = next((item for item in plan.get("featureFamilies", []) if item.get("mechanism") == "banking-credit"), {})
    g5_request = next((item for item in plan.get("requests", []) if item.get("requestId") == "g5-dated-release-expansion-v2"), {})
    fdic_request = next((item for item in plan.get("requests", []) if item.get("requestId") == "fdic-qbp-publication-expansion-v2"), {})
    serialized_plan = json.dumps(plan, sort_keys=True).lower()
    if (
        contract.get("contractId") != "e14-post2005-source-acquisition-contract-v2"
        or contract.get("inputHashes") != hashes or hashes != CANONICAL_HASHES
        or contract.get("expectedSourceIds") != SOURCE_IDS
        or contract.get("retiredSourceIdsForbiddenEverywhere") != ["federal-reserve-h10-release-archive"]
        or contract.get("expectedFeatureFamilyIds") != FAMILY_IDS
        or contract.get("expectedRequestTemplateCount") != 11
        or contract.get("decisionPolicy") != DECISION_POLICY
        or contract.get("authorizationPolicy") != AUTHORIZATION_POLICY
        or contract.get("expectedStatus") != STATUS or contract.get("nextAllowedAction") != NEXT_ACTION
        or policy.get("policyId") != "e14-post2005-active-source-vintage-policy-v2"
        or policy.get("status") != "POST_2005_REDESIGNED_POLICY_ACTIVE_REQUEST_CATALOG_PREREGISTRATION_REQUIRED"
        or policy.get("authorization", {}).get("requestCatalogGenerationAuthorized") is not True
        or policy.get("authorization", {}).get("sourceAcquisitionAuthorized") is not False
        or policy.get("governance", {}).get("legacyH10ManifestAndSnapshotNotValidForPolicyV2") is not True
        or activation_audit.get("status") != "POST_2005_REDESIGNED_POLICY_ACTIVE_REQUEST_CATALOG_PREREGISTRATION_REQUIRED"
        or activation_audit.get("outputs", {}).get("activePolicy") != _artifact(artifacts[1][0], artifacts[1][1])
        or activation_audit.get("decision", {}).get("sourceManifestAndRequestCatalogPreregistrationAuthorized") is not True
        or activation_audit.get("decision", {}).get("sourceAcquisitionAuthorized") is not False
        or taxonomy.get("taxonomyId") != "us-financial-stress-post2005-v1" or taxonomy.get("activation", {}).get("labelsAccepted") is not True
        or scope_audit.get("outputs", {}).get("activeTaxonomy") != _artifact(artifacts[3][0], artifacts[3][1])
        or legacy_manifest.get("manifestId") != "e14-post2005-source-acquisition-manifest-v1"
        or plan.get("planId") != "e14-post2005-source-acquisition-plan-v2" or plan.get("policyId") != policy.get("policyId")
        or plan.get("window") != {"startInclusive": "2006-01-01", "endInclusive": "2025-12-31"}
        or plan.get("snapshotRoot") != "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
        or source_ids != SOURCE_IDS or len(set(source_ids)) != 7 or evidence_ids != SOURCE_IDS
        or family_ids != FAMILY_IDS or family_sources != set(SOURCE_IDS) or request_sources != set(SOURCE_IDS)
        or len(request_ids) != 11 or len(set(request_ids)) != 11
        or any(not all(evidence_by_id[source].get(key) is True for key in readiness_keys) or evidence_by_id[source].get("blockingReasons") != [] for source in SOURCE_IDS)
        or "federal-reserve-h10-release-archive" in serialized_plan or "federal-reserve/h10" in serialized_plan
        or cross.get("sourceIds") != ["federal-reserve-g5-release-archive"]
        or bank.get("sourceIds") != ["federal-reserve-h8-release-archive", "fdic-qbp-archive"]
        or "no-cross-regime-splice-rebase-percentile-or-threshold-sharing" not in next(item for item in plan["sources"] if item["sourceId"] == "federal-reserve-g5-release-archive")["methodologyRegimes"]
        or g5_request.get("expansionPolicy", {}).get("expectedUniqueMonthCount") != 240
        or g5_request.get("expansionPolicy", {}).get("duplicateOrCorrectionReleaseRequiresAdjudication") is not True
        or fdic_request.get("expansionPolicy", {}).get("expectedEligibleQuarterCount") != 79
        or fdic_request.get("expansionPolicy", {}).get("lastEligibleQuarter") != "2025Q3"
        or fdic_request.get("expansionPolicy", {}).get("excludedQuarter") != "2025Q4"
        or fdic_request.get("expansionPolicy", {}).get("quarterEndCannotSubstituteForPublicationDate") is not True
        or plan.get("authorizationPolicy") != MANIFEST_AUTHORIZATION
        or not all(plan.get("integrityPolicy", {}).values()) or len(plan.get("integrityPolicy", {})) != 9
        or manifest_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-acquisition-manifest-v2.json"
        or request_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-acquisition-requests-v2.json"
        or audit_schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-acquisition-preregistration-audit-v2.json"
    ):
        raise DatasetValidationError("E14.7t source manifest/request-catalog inputs are invalid.")


def _validate_outputs(manifest: dict[str, Any], catalog: dict[str, Any], audit: dict[str, Any]) -> None:
    expected_manifest_keys = {"schemaVersion", "artifactType", "manifestId", "activePolicy", "activationAudit", "baseTaxonomy", "supersedesManifest", "window", "snapshotRoot", "sources", "featureFamilies", "integrityPolicy", "authorizationPolicy", "status"}
    expected_catalog_keys = {"schemaVersion", "artifactType", "requestCatalogId", "manifestId", "activePolicy", "snapshotRoot", "requests", "atomicityPolicy", "authorizationPolicy", "status"}
    expected_audit_keys = {"schemaVersion", "artifactType", "status", "inputs", "outputs", "inventory", "checks", "protocol", "decision", "implementation"}
    input_keys = {"acquisitionContractV2", "activeSourceVintagePolicyV2", "policyActivationAudit", "baseActiveTaxonomy", "scopeActivationAudit", "legacySourceManifestV1", "sourceAcquisitionEvidenceV2", "sourceAcquisitionPlanV2", "manifestSchemaV2", "requestCatalogSchemaV2", "preregistrationAuditSchemaV2"}
    artifact_keys = {"fileName", "sha256", "sizeBytes"}
    source_keys = {"sourceId", "provider", "frequency", "retrievalMode", "seriesOrTables", "rawArtifactPath", "asOfPolicy", "methodologyRegimes", "providerPrimaryLocators", "coverageFrom", "readinessEvidence"}
    readiness_keys = {"providerPrimaryPageReachable", "licensingCleared", "componentCoverageVerified", "releaseProofComplete", "vintageProofComplete", "methodologyManifestFeasible"}
    family_keys = {"familyId", "mechanism", "sourceIds", "components", "minimumHistoryMonths"}
    request_keys = {"requestId", "sourceId", "urlTemplate", "outputRelativePath", "contentValidation", "maximumBytes", "usageBoundary", "expansionPolicy", "realtimeChunks"}
    artifacts = list(audit.get("inputs", {}).values()) + list(audit.get("outputs", {}).values())
    if (
        set(manifest) != expected_manifest_keys or set(catalog) != expected_catalog_keys or set(audit) != expected_audit_keys
        or manifest.get("schemaVersion") != 2 or catalog.get("schemaVersion") != 2 or audit.get("schemaVersion") != 2
        or manifest.get("artifactType") != "E14Post2005SourceAcquisitionManifest"
        or catalog.get("artifactType") != "E14Post2005SourceAcquisitionRequestCatalog"
        or audit.get("artifactType") != "E14Post2005SourceAcquisitionPreregistrationAudit"
        or manifest.get("status") != STATUS or catalog.get("status") != STATUS or audit.get("status") != STATUS
        or manifest.get("manifestId") != "e14-post2005-source-acquisition-manifest-v2"
        or catalog.get("requestCatalogId") != "e14-post2005-source-acquisition-requests-v2" or catalog.get("manifestId") != manifest.get("manifestId")
        or [item.get("sourceId") for item in manifest.get("sources", [])] != SOURCE_IDS
        or any(set(item) != source_keys or set(item.get("readinessEvidence", {})) != readiness_keys or any(value is not True for value in item["readinessEvidence"].values()) for item in manifest.get("sources", []))
        or [item.get("familyId") for item in manifest.get("featureFamilies", [])] != FAMILY_IDS
        or any(set(item) != family_keys or item.get("minimumHistoryMonths") != 60 for item in manifest.get("featureFamilies", []))
        or len(catalog.get("requests", [])) != 11 or any(set(item) != request_keys for item in catalog.get("requests", []))
        or manifest.get("authorizationPolicy") != MANIFEST_AUTHORIZATION
        or manifest.get("integrityPolicy") != INTEGRITY_POLICY
        or catalog.get("authorizationPolicy") != CATALOG_AUTHORIZATION
        or catalog.get("atomicityPolicy") != ATOMICITY_POLICY
        or any(not _valid_request(item) for item in catalog.get("requests", []))
        or _count_h10(manifest) != 0 or _count_h10(catalog) != 0
        or set(audit.get("inputs", {})) != input_keys or set(audit.get("outputs", {})) != {"sourceAcquisitionManifestV2", "requestCatalogV2"}
        or any(not isinstance(item, dict) or set(item) != artifact_keys or not item.get("fileName") or not isinstance(item.get("sizeBytes"), int) or item["sizeBytes"] < 1 or not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64 for item in artifacts)
        or audit.get("inventory") != {"sourceCount": 7, "featureFamilyCount": 4, "requestTemplateCount": 11, "retiredH10ReferenceCount": 0, "providerPrimaryLocatorCount": 17}
        or any(value is not True for value in audit.get("checks", {}).values()) or len(audit.get("checks", {})) != 14
        or audit.get("protocol") != {"manifestFrozen": True, "requestCatalogFrozen": True, "networkRequestsMade": 0, "observationsAcquired": 0, "rawArtifactsWritten": 0, "featuresTransformed": 0, "candidatesGenerated": 0, "evaluationPerformed": False, "outerOosRead": False}
        or audit.get("decision") != {"manifestAndRequestCatalogReady": True, "separateExecutionGateAuthorized": True, "sourceAcquisitionExecutionAuthorized": False, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": NEXT_ACTION}
        or set(audit.get("implementation", {})) != {"module", "sourceSha256"}
        or audit.get("implementation", {}).get("module") != "regime_eval.e14_post2005_source_acquisition_v2"
        or not isinstance(audit.get("implementation", {}).get("sourceSha256"), str) or len(audit["implementation"]["sourceSha256"]) != 64
    ):
        raise DatasetValidationError("E14.7t generated outputs violate the closed preregistration contract.")


def _valid_request(request: dict[str, Any]) -> bool:
    expansion = request.get("expansionPolicy")
    chunks = request.get("realtimeChunks")
    basic_keys = {"discoveryRequestId", "placeholder", "allowOnlyProviderDiscoveredValues"}
    fdic_keys = basic_keys | {"expectedEligibleQuarterCount", "firstEligibleQuarter", "lastEligibleQuarter", "excludedQuarter", "quarterEndCannotSubstituteForPublicationDate"}
    g5_keys = basic_keys | {"expectedUniqueMonthCount", "firstMonth", "lastMonth", "duplicateOrCorrectionReleaseRequiresAdjudication"}
    if expansion is not None:
        if not isinstance(expansion, dict) or set(expansion) not in (basic_keys, fdic_keys, g5_keys) or expansion.get("allowOnlyProviderDiscoveredValues") is not True:
            return False
        if set(expansion) == fdic_keys and expansion != {"discoveryRequestId": "fdic-qbp-publication-index-v2", "placeholder": "PROVIDER_PRIMARY_PUBLICATION_URL,PUBLICATION_DATE,DOCUMENT_SLUG", "allowOnlyProviderDiscoveredValues": True, "expectedEligibleQuarterCount": 79, "firstEligibleQuarter": "2006Q1", "lastEligibleQuarter": "2025Q3", "excludedQuarter": "2025Q4", "quarterEndCannotSubstituteForPublicationDate": True}:
            return False
        if set(expansion) == g5_keys and expansion != {"discoveryRequestId": "g5-release-calendar-v2", "placeholder": "RELEASE_DATE", "allowOnlyProviderDiscoveredValues": True, "expectedUniqueMonthCount": 240, "firstMonth": "2006-01", "lastMonth": "2025-12", "duplicateOrCorrectionReleaseRequiresAdjudication": True}:
            return False
    if chunks is not None and (not isinstance(chunks, list) or len(chunks) != 4 or any(not isinstance(chunk, list) or len(chunk) != 2 or any(not isinstance(value, str) for value in chunk) for chunk in chunks)):
        return False
    return True


def _count_h10(payload: dict[str, Any]) -> int:
    text = json.dumps(payload, sort_keys=True).lower()
    return text.count("federal-reserve-h10") + text.count("federal-reserve/h10")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    try:
        raw = file.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        return file, raw, payload
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise DatasetValidationError(f"E14.7t {label} is not valid UTF-8 JSON: {file}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write_new(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14.7t output already exists: {path}") from error


def _write_many(items: tuple[tuple[Path, bytes], ...]) -> None:
    created: list[Path] = []
    try:
        for path, raw in items:
            _write_new(path, raw)
            created.append(path)
    except (DatasetValidationError, OSError) as error:
        for path in reversed(created):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        if isinstance(error, DatasetValidationError):
            raise
        raise DatasetValidationError("E14.7t output set could not be published atomically.") from error
