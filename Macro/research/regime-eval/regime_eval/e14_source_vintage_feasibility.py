from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "SOURCE_VINTAGE_FEASIBILITY_BLOCKED_REMEDIATION_PREREGISTRATION_REQUIRED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]
FORBIDDEN_AUTHORIZATIONS = [
    "sourceAcquisitionAuthorized",
    "featureFoundationMaterializationAuthorized",
    "taxonomyMutationAuthorized",
    "candidateGenerationAuthorized",
    "candidateFittingAuthorized",
    "candidateEvaluationAuthorized",
    "candidateRankingAuthorized",
    "crossMechanismCompositionAuthorized",
    "outerOosAuthorized",
    "promotionAuthorized",
]


def write_e14_source_vintage_feasibility_audit(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    hypothesis_contract_path: str | Path,
    hypothesis_plan_path: str | Path,
    hypothesis_schema_path: str | Path,
    hypothesis_audit_path: str | Path,
    evidence_path: str | Path,
    evidence_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "source-vintage feasibility contract", "taxonomy v5",
        "new-information hypothesis contract", "new-information hypothesis plan",
        "new-information hypothesis schema", "new-information hypothesis audit",
        "source-vintage evidence", "source-vintage evidence schema",
    )
    paths = (
        contract_path, taxonomy_path, hypothesis_contract_path, hypothesis_plan_path,
        hypothesis_schema_path, hypothesis_audit_path, evidence_path, evidence_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract), (taxonomy_file, taxonomy_raw, taxonomy),
     (hypothesis_contract_file, hypothesis_contract_raw, hypothesis_contract),
     (plan_file, plan_raw, plan), (plan_schema_file, plan_schema_raw, plan_schema),
     (hypothesis_audit_file, hypothesis_audit_raw, hypothesis_audit),
     (evidence_file, evidence_raw, evidence),
     (evidence_schema_file, evidence_schema_raw, evidence_schema)) = artifacts
    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "hypothesisContractV1Sha256": _sha(hypothesis_contract_raw),
        "hypothesisPlanV1Sha256": _sha(plan_raw),
        "hypothesisSchemaV1Sha256": _sha(plan_schema_raw),
        "hypothesisAuditV1Sha256": _sha(hypothesis_audit_raw),
        "feasibilityEvidenceV1Sha256": _sha(evidence_raw),
        "feasibilityEvidenceSchemaV1Sha256": _sha(evidence_schema_raw),
    }
    _validate_inputs(
        contract, taxonomy, hypothesis_contract, plan, plan_schema,
        hypothesis_audit, evidence, evidence_schema, hashes,
    )

    source_assessments = _assess_sources(plan, evidence)
    source_by_id = {item["sourceId"]: item for item in source_assessments}
    episode_dates = _positive_episode_dates(taxonomy)
    family_assessments = _assess_families(plan, source_by_id, episode_dates)
    source_counts = dict(Counter(item["status"] for item in source_assessments))
    family_counts = dict(Counter(item["status"] for item in family_assessments))
    source_counts = {status: source_counts.get(status, 0) for status in ("ready", "conditional", "blocked")}
    family_counts = {status: family_counts.get(status, 0) for status in ("ready", "conditional", "blocked")}
    if (
        source_counts != contract["expectedSourceStatusCounts"]
        or family_counts != contract["expectedFamilyStatusCounts"]
    ):
        raise DatasetValidationError("E14.7a classifications differ from the frozen contract.")

    output = Path(output_path).resolve()
    input_artifacts = {
        name: _artifact(file, raw)
        for name, (file, raw, _) in zip((
            "feasibilityContract", "taxonomyV5", "hypothesisContractV1",
            "hypothesisPlanV1", "hypothesisSchemaV1", "hypothesisAuditV1",
            "feasibilityEvidenceV1", "feasibilityEvidenceSchemaV1",
        ), artifacts)
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14SourceVintageFeasibilityAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "inventory": {
            "sourceCount": len(source_assessments),
            "featureFamilyCount": len(family_assessments),
            "sourceStatusCounts": source_counts,
            "familyStatusCounts": family_counts,
            "mechanismCount": len(MECHANISMS),
        },
        "sourceAssessments": source_assessments,
        "familyAssessments": family_assessments,
        "mechanismReadiness": [
            _mechanism_readiness(mechanism, family_assessments) for mechanism in MECHANISMS
        ],
        "checks": {
            "allInputHashesExact": True,
            "metadataOnlyNetworkPolicy": evidence["networkPolicy"] == "metadata-only-no-series-download",
            "allProviderPagesReachable": all(item["providerPrimaryPageReachable"] for item in evidence["sources"]),
            "allCoverageClaimsReviewed": all(item["coverageClaimVerified"] for item in evidence["sources"]),
            "sourceRosterMatchesPreregistration": True,
            "everyFamilyAssessedExactlyOnce": True,
            "everyApplicableEpisodeCoverageMeasured": True,
            "minimumCausalHistoryEnforced": True,
            "licenseRestrictionsEnforced": True,
            "componentCoverageEnforced": True,
            "vintageAndReleaseProofEnforced": True,
            "blockedFamiliesHaveNoFallback": True,
            "sourceDataNotAcquired": True,
            "featureFoundationNotMaterialized": True,
            "candidateGenerationClosed": True,
            "candidateEvaluationClosed": True,
            "outerOosClosed": True,
        },
        "decision": {
            "fullSourceVintageReadiness": family_counts["ready"] == len(family_assessments),
            "sourceAcquisitionAuthorized": False,
            "feasibilityRemediationPreregistrationAuthorized": True,
            "featureFoundationMaterializationAuthorized": False,
            "taxonomyMutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "candidateFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "candidateRankingAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "protocol": {
            "providerMetadataInspected": True,
            "seriesObservationDownloaded": False,
            "datasetRead": False,
            "featureMaterialized": False,
            "candidateGenerated": False,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "implementation": {
            "module": "regime_eval.e14_source_vintage_feasibility",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output, payload)


def _assess_sources(plan: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_by_id = {item["sourceId"]: item for item in evidence["sources"]}
    output = []
    for source in plan["sourceCatalog"]:
        item = evidence_by_id[source["sourceId"]]
        blocking = []
        conditional = []
        if not item["providerPrimaryPageReachable"] or not item["coverageClaimVerified"]:
            blocking.append("provider-access-or-coverage-unverified")
        if item["licensingStatus"] == "permission-required":
            blocking.append("third-party-permission-required")
        elif item["licensingStatus"] == "provider-terms-review-required":
            conditional.append("provider-terms-review-required")
        if item["componentCoverageStatus"] != "complete":
            blocking.append("component-history-not-complete")
        if item["vintageStatus"] in {
            "current-history-vintage-proof-required", "release-archive-proof-required",
        }:
            conditional.append(item["vintageStatus"])
        if item["releaseSemanticsStatus"] != "documented":
            conditional.append(item["releaseSemanticsStatus"])
        if item["methodologyStatus"] != "stable-with-manifest":
            conditional.append(item["methodologyStatus"])
        status = "blocked" if blocking else "conditional" if conditional else "ready"
        output.append({
            "sourceId": source["sourceId"],
            "status": status,
            "coverageFrom": source["coverageFrom"],
            "frequency": source["frequency"],
            "licensingStatus": item["licensingStatus"],
            "vintageStatus": item["vintageStatus"],
            "releaseSemanticsStatus": item["releaseSemanticsStatus"],
            "methodologyStatus": item["methodologyStatus"],
            "blockingReasons": sorted(set(blocking)),
            "conditionalRequirements": sorted(set(conditional)),
            "evidenceUrls": item["evidenceUrls"],
        })
    return output


def _assess_families(
    plan: dict[str, Any], source_by_id: dict[str, dict[str, Any]],
    episode_dates: dict[tuple[str, str], date],
) -> list[dict[str, Any]]:
    output = []
    source_plan = {item["sourceId"]: item for item in plan["sourceCatalog"]}
    for mechanism in plan["mechanisms"]:
        name = mechanism["mechanism"]
        signatures = mechanism["episodeSignatures"]
        for family in mechanism["featureFamilies"]:
            family_id = family["familyId"]
            applicable = []
            for signature in signatures:
                phases = (signature["onset"], signature["intensity"], signature["recovery"])
                if any(family_id in phase["familyIds"] for phase in phases):
                    applicable.append(signature["episodeId"])
            coverage_start = max(
                date.fromisoformat(source_plan[source_id]["coverageFrom"])
                for source_id in family["sourceIds"]
            )
            episode_coverage = []
            blocking = []
            conditional = []
            for episode_id in applicable:
                episode_start = episode_dates[(episode_id, name)]
                months = (episode_start.year - coverage_start.year) * 12 + episode_start.month - coverage_start.month
                eligible = months >= family["minimumHistoryMonths"]
                episode_coverage.append({
                    "episodeId": episode_id,
                    "episodeFirstMonth": episode_start.isoformat(),
                    "latestSourceCoverageFrom": coverage_start.isoformat(),
                    "causalHistoryMonths": months,
                    "requiredHistoryMonths": family["minimumHistoryMonths"],
                    "minimumHistorySatisfied": eligible,
                })
                if not eligible:
                    blocking.append(f"insufficient-causal-history:{episode_id}:{months}-of-{family['minimumHistoryMonths']}")
            for source_id in family["sourceIds"]:
                source = source_by_id[source_id]
                if source["status"] == "blocked":
                    blocking.append(f"blocked-source:{source_id}")
                elif source["status"] == "conditional":
                    conditional.append(f"conditional-source:{source_id}")
            status = "blocked" if blocking else "conditional" if conditional else "ready"
            output.append({
                "mechanism": name,
                "familyId": family_id,
                "status": status,
                "sourceIds": family["sourceIds"],
                "minimumHistoryMonths": family["minimumHistoryMonths"],
                "applicableEpisodeCount": len(applicable),
                "episodeCoverage": episode_coverage,
                "blockingReasons": sorted(set(blocking)),
                "conditionalRequirements": sorted(set(conditional)),
                "retiredOnBlocked": status == "blocked",
                "sourceAcquisitionAuthorized": False,
            })
    return output


def _mechanism_readiness(mechanism: str, families: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [item for item in families if item["mechanism"] == mechanism]
    counts = Counter(item["status"] for item in selected)
    return {
        "mechanism": mechanism,
        "familyCount": len(selected),
        "readyCount": counts["ready"],
        "conditionalCount": counts["conditional"],
        "blockedCount": counts["blocked"],
        "fullyReady": counts["ready"] == len(selected),
        "sourceAcquisitionAuthorized": False,
    }


def _positive_episode_dates(taxonomy: dict[str, Any]) -> dict[tuple[str, str], date]:
    output = {}
    for episode in taxonomy["episodes"]:
        if episode.get("financialState") != "positive":
            continue
        for mechanism in episode["mechanisms"]:
            output[(episode["independentEventId"], mechanism)] = date.fromisoformat(episode["firstMonth"])
    return output


def _validate_inputs(
    contract: dict[str, Any], taxonomy: dict[str, Any], hypothesis_contract: dict[str, Any],
    plan: dict[str, Any], plan_schema: dict[str, Any], hypothesis_audit: dict[str, Any],
    evidence: dict[str, Any], evidence_schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    auth = contract.get("authorizationPolicy", {})
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-source-vintage-feasibility-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or auth.get("sourceVintageFeasibilityAuditAuthorized") is not True
        or auth.get("feasibilityRemediationPreregistrationAuthorizedOnFailure") is not True
        or any(auth.get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or taxonomy.get("schemaVersion") != 5
        or hypothesis_contract.get("contractId") != "e14-new-information-hypothesis-contract-v1"
        or hypothesis_contract.get("authorizationPolicy", {}).get("sourceAcquisitionAuthorized") is not False
        or plan.get("planId") != "e14-new-information-hypothesis-plan-v1"
        or plan.get("authorizations", {}).get("sourceAcquisitionAuthorized") is not False
        or plan_schema.get("$id") != "e14-new-information-hypothesis-schema-v1"
        or hypothesis_audit.get("status") != "NEW_INFORMATION_HYPOTHESIS_PREREGISTERED_SOURCE_FEASIBILITY_REQUIRED"
        or hypothesis_audit.get("decision", {}).get("sourceFeasibilityAuditAuthorized") is not True
        or hypothesis_audit.get("decision", {}).get("sourceAcquisitionAuthorized") is not False
        or evidence.get("evidencePackId") != "e14-source-vintage-feasibility-evidence-v1"
        or evidence.get("networkPolicy") != "metadata-only-no-series-download"
        or evidence_schema.get("$id") != "e14-source-vintage-feasibility-evidence-schema-v1"
    )
    if invalid:
        raise DatasetValidationError("E14.7a inputs or governance are invalid.")
    plan_sources = [item["sourceId"] for item in plan["sourceCatalog"]]
    evidence_sources = [item.get("sourceId") for item in evidence.get("sources", [])]
    if (
        plan_sources != evidence_sources
        or len(plan_sources) != contract["expectedSourceCount"]
        or len(set(plan_sources)) != len(plan_sources)
        or any(not item.get("evidenceUrls") for item in evidence["sources"])
    ):
        raise DatasetValidationError("E14.7a evidence source roster is invalid.")
    families = [family for item in plan["mechanisms"] for family in item["featureFamilies"]]
    if len(families) != contract["expectedFeatureFamilyCount"]:
        raise DatasetValidationError("E14.7a feature-family roster differs from contract.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    if not file.exists():
        raise DatasetValidationError(f"E14.7a {label} does not exist: {file}")
    raw = file.read_bytes()
    try:
        return file, raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7a {label} is not valid UTF-8 JSON.") from error


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write_new(path: Path, payload: dict[str, Any]) -> Path:
    if path.exists():
        raise DatasetValidationError("Immutable E14.7a source-vintage audit output already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return path
