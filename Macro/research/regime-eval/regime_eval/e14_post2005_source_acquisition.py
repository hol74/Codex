from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "POST_2005_SOURCE_ACQUISITION_MANIFEST_FROZEN_EXECUTION_REQUIRES_SEPARATE_GATE"
MECHANISMS = ("banking-credit", "broad-market-repricing", "cross-border-growth", "funding-liquidity")


def write_e14_post2005_source_acquisition_manifest(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    activation_audit_path: str | Path,
    scope_plan_path: str | Path,
    source_evidence_path: str | Path,
    acquisition_plan_path: str | Path,
    schema_path: str | Path,
    manifest_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    labels = ("contract", "active taxonomy", "activation audit", "scope plan", "source evidence", "acquisition plan", "manifest schema")
    paths = (contract_path, taxonomy_path, activation_audit_path, scope_plan_path, source_evidence_path, acquisition_plan_path, schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (_, _, contract), (taxonomy_file, taxonomy_raw, taxonomy), (activation_file, activation_raw, activation), \
        (_, scope_raw, scope_plan), (_, evidence_raw, evidence), (_, plan_raw, plan), (_, schema_raw, schema) = artifacts
    actual_hashes = {
        "activeTaxonomySha256": _sha(taxonomy_raw),
        "scopeActivationAuditSha256": _sha(activation_raw),
        "scopeFeasibilityPlanSha256": _sha(scope_raw),
        "sourceFeasibilityEvidenceSha256": _sha(evidence_raw),
        "sourceAcquisitionPlanSha256": _sha(plan_raw),
        "sourceAcquisitionSchemaSha256": _sha(schema_raw),
    }
    _validate_inputs(contract, taxonomy, activation, scope_plan, evidence, plan, schema, actual_hashes)

    evidence_by_id = {item["sourceId"]: item for item in evidence["sources"]}
    sources = []
    for source in plan["sources"]:
        readiness = evidence_by_id[source["sourceId"]]
        sources.append({
            **source,
            "providerPrimaryLocators": readiness["evidenceUrls"],
            "coverageFrom": readiness["coverageFrom"],
            "readinessEvidence": {
                "providerPrimaryPageReachable": readiness["providerPrimaryPageReachable"],
                "licensingCleared": readiness["licensingCleared"],
                "componentCoverageVerified": readiness["componentCoverageVerified"],
                "releaseProofComplete": readiness["releaseProofComplete"],
                "vintageProofComplete": readiness["vintageProofComplete"],
                "methodologyManifestFeasible": readiness["methodologyManifestFeasible"],
            },
        })

    manifest = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005SourceAcquisitionManifest",
        "manifestId": "e14-post2005-source-acquisition-manifest-v1",
        "taxonomy": _artifact(taxonomy_file, taxonomy_raw),
        "activationAudit": _artifact(activation_file, activation_raw),
        "window": plan["window"],
        "snapshotRoot": plan["snapshotRoot"],
        "sources": sources,
        "featureFamilies": plan["featureFamilies"],
        "integrityPolicy": plan["integrityPolicy"],
        "authorizationPolicy": plan["authorizationPolicy"],
        "status": STATUS,
    }
    manifest_raw = _json_bytes(manifest)
    manifest_path = Path(manifest_output_path).resolve()
    audit_path = Path(audit_output_path).resolve()
    if manifest_path.exists() or audit_path.exists():
        raise DatasetValidationError("Immutable E14.7i source-acquisition output already exists.")
    _write(manifest_path, manifest_raw)

    audit = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005SourceAcquisitionPreregistrationAudit",
        "status": STATUS,
        "inputs": {
            name: _artifact(file, raw)
            for name, (file, raw, _) in zip(
                ("acquisitionContract", "activeTaxonomy", "scopeActivationAudit", "scopeFeasibilityPlan", "sourceFeasibilityEvidence", "sourceAcquisitionPlan", "sourceAcquisitionSchema"),
                artifacts,
            )
        },
        "outputs": {"sourceAcquisitionManifest": _artifact(manifest_path, manifest_raw)},
        "inventory": {
            "sourceCount": len(sources),
            "featureFamilyCount": len(plan["featureFamilies"]),
            "featureFamilyCountByMechanism": dict(Counter(item["mechanism"] for item in plan["featureFamilies"])),
            "providerPrimaryLocatorCount": sum(len(item["providerPrimaryLocators"]) for item in sources),
        },
        "checks": {
            "allInputHashesExact": True,
            "activeTaxonomyRequired": True,
            "allSourcesMetadataReady": True,
            "allSourcesResolveToFeatureFamilies": True,
            "asOfPoliciesFrozen": True,
            "methodologyRegimesFrozen": True,
            "rawPathsUnique": True,
            "integrityPolicyFailClosed": True,
            "observationsAbsent": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "manifestFrozen": True,
            "networkRequestsMade": 0,
            "observationsAcquired": 0,
            "rawArtifactsWritten": 0,
            "featuresTransformed": 0,
            "candidatesGenerated": 0,
            "outerOosRead": False,
        },
        "decision": {
            "sourceAcquisitionManifestReady": True,
            "sourceAcquisitionExecutionAuthorized": False,
            "featureTransformationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "evaluationAuthorized": False,
            "outerOosAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {"module": "regime_eval.e14_post2005_source_acquisition", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    return manifest_path, _write(audit_path, _json_bytes(audit))


def _validate_inputs(
    contract: dict[str, Any], taxonomy: dict[str, Any], activation: dict[str, Any],
    scope_plan: dict[str, Any], evidence: dict[str, Any], plan: dict[str, Any],
    schema: dict[str, Any], actual_hashes: dict[str, str],
) -> None:
    expected_source_ids = contract.get("expectedSourceIds", [])
    sources = plan.get("sources", [])
    source_ids = [item.get("sourceId") for item in sources]
    evidence_by_id = {item.get("sourceId"): item for item in evidence.get("sources", [])}
    families = plan.get("featureFamilies", [])
    family_source_ids = {source_id for item in families for source_id in item.get("sourceIds", [])}
    counts = dict(Counter(item.get("mechanism") for item in families))
    scope_families = {
        item["familyId"]: {key: item[key] for key in ("familyId", "mechanism", "sourceIds", "components", "minimumHistoryMonths")}
        for item in scope_plan.get("post2005FeatureFamilies", [])
    }
    plan_families = {item.get("familyId"): item for item in families}
    readiness_keys = ("providerPrimaryPageReachable", "licensingCleared", "componentCoverageVerified", "releaseProofComplete", "vintageProofComplete", "methodologyManifestFeasible")
    integrity = plan.get("integrityPolicy", {})
    authorization = plan.get("authorizationPolicy", {})
    if (
        contract.get("contractId") != "e14-post2005-source-acquisition-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("expectedStatus") != STATUS
        or not all(contract.get("decisionPolicy", {}).values())
        or taxonomy.get("taxonomyId") != "us-financial-stress-post2005-v1"
        or taxonomy.get("activation", {}).get("active") is not True
        or taxonomy.get("activation", {}).get("labelsAccepted") is not True
        or taxonomy.get("activation", {}).get("sourceAcquisitionAuthorized") is not False
        or activation.get("status") != "POST_2005_SCOPE_ACTIVE_SOURCE_PREREGISTRATION_REQUIRED"
        or activation.get("decision", {}).get("post2005ScopeActivated") is not True
        or plan.get("planId") != "e14-post2005-source-acquisition-plan-v1"
        or plan.get("scopeId") != taxonomy.get("scopeId")
        or plan.get("taxonomyId") != taxonomy.get("taxonomyId")
        or plan.get("window") != {"startInclusive": "2006-01-01", "endInclusive": "2025-12-31"}
        or source_ids != expected_source_ids or len(source_ids) != len(set(source_ids)) == 7
        or set(source_ids) != family_source_ids
        or counts != contract.get("expectedFeatureFamilyCountByMechanism")
        or set(plan_families) != set(scope_families)
        or any(plan_families[key] != scope_families[key] for key in scope_families)
        or any(source_id not in evidence_by_id for source_id in source_ids)
        or any(not all(evidence_by_id[source_id].get(key) is True for key in readiness_keys) for source_id in source_ids)
        or any(evidence_by_id[source_id].get("blockingReasons") != [] for source_id in source_ids)
        or any(not item.get("asOfPolicy") or not item.get("methodologyRegimes") or not item.get("rawArtifactPath") for item in sources)
        or len({item["rawArtifactPath"] for item in sources}) != 7
        or not all(integrity.values())
        or authorization != {"manifestMaterializationAuthorized": True, "sourceAcquisitionExecutionAuthorized": False, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False}
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-source-acquisition-manifest-v1.json"
    ):
        raise DatasetValidationError("E14.7i source-acquisition preregistration inputs are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7i {label} is not valid JSON: {source}") from error


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
        raise DatasetValidationError(f"Immutable E14.7i output exists: {path}") from error
    return path
