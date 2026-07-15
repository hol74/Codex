from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "NEW_INFORMATION_HYPOTHESIS_PREREGISTERED_SOURCE_FEASIBILITY_REQUIRED"
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


def write_e14_new_information_hypothesis_audit(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    mechanism_contract_path: str | Path,
    historical_source_catalog_path: str | Path,
    no_go_diagnostic_path: str | Path,
    hypothesis_plan_path: str | Path,
    hypothesis_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "new-information hypothesis contract", "taxonomy v5", "mechanism contract v1",
        "historical source catalog v1", "no-go diagnostic v1",
        "new-information hypothesis plan v1", "new-information hypothesis schema v1",
    )
    paths = (
        contract_path, taxonomy_path, mechanism_contract_path, historical_source_catalog_path,
        no_go_diagnostic_path, hypothesis_plan_path, hypothesis_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract), (taxonomy_file, taxonomy_raw, taxonomy),
     (mechanism_file, mechanism_raw, mechanism_contract),
     (catalog_file, catalog_raw, source_catalog),
     (diagnostic_file, diagnostic_raw, diagnostic), (plan_file, plan_raw, plan),
     (schema_file, schema_raw, schema)) = artifacts
    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "mechanismContractV1Sha256": _sha(mechanism_raw),
        "historicalSourceCatalogV1Sha256": _sha(catalog_raw),
        "noGoDiagnosticV1Sha256": _sha(diagnostic_raw),
        "hypothesisPlanV1Sha256": _sha(plan_raw),
        "hypothesisSchemaV1Sha256": _sha(schema_raw),
    }
    _validate(
        contract, taxonomy, mechanism_contract, source_catalog, diagnostic, plan, schema, hashes
    )

    mechanisms = {item["mechanism"]: item for item in plan["mechanisms"]}
    prior_source_ids = {item["id"] for item in source_catalog["sources"]}
    source_ids = {item["sourceId"] for item in plan["sourceCatalog"]}
    feature_family_count = sum(len(item["featureFamilies"]) for item in plan["mechanisms"])
    episode_signature_count = sum(len(item["episodeSignatures"]) for item in plan["mechanisms"])
    new_sources_by_mechanism = {}
    for mechanism, item in mechanisms.items():
        used = {
            source_id
            for family in item["featureFamilies"]
            for source_id in family["sourceIds"]
        }
        new_sources_by_mechanism[mechanism] = sorted(used - prior_source_ids)

    output = Path(output_path).resolve()
    input_artifacts = {
        name: _artifact(file, raw)
        for name, (file, raw, _) in zip((
            "hypothesisContract", "taxonomyV5", "mechanismContractV1",
            "historicalSourceCatalogV1", "noGoDiagnosticV1",
            "hypothesisPlanV1", "hypothesisSchemaV1",
        ), artifacts)
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14NewInformationHypothesisAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "inventory": {
            "mechanismCount": len(mechanisms),
            "sourceCount": len(source_ids),
            "featureFamilyCount": feature_family_count,
            "episodeSignatureCount": episode_signature_count,
            "episodeSignatureCountByMechanism": {
                mechanism: len(mechanisms[mechanism]["episodeSignatures"])
                for mechanism in MECHANISMS
            },
            "newSourceCountByMechanism": {
                mechanism: len(new_sources_by_mechanism[mechanism])
                for mechanism in MECHANISMS
            },
        },
        "checks": {
            "allInputHashesExact": True,
            "priorCandidateFamilyClosedNoGo": True,
            "fourMechanismsExactlyOnce": True,
            "finiteFeatureFamilyRoster": True,
            "atLeastTwoFeatureFamiliesPerMechanism": True,
            "atLeastOneNewSourcePerMechanism": True,
            "allFeatureSourcesResolveWithinPlan": True,
            "everyFrozenLoeoEpisodeHasOneSignature": True,
            "onsetIntensityRecoverySeparated": True,
            "falsificationConditionsFrozen": True,
            "ablationDesignFrozenBeforePopulation": True,
            "missingnessExplicit": True,
            "methodologyRegimesExplicit": True,
            "taxonomyV5Unchanged": True,
            "sourceDataNotAcquired": True,
            "featureFoundationNotMaterialized": True,
            "candidateGenerationClosed": True,
            "candidateFittingClosed": True,
            "candidateEvaluationClosed": True,
            "outerOosClosed": True,
        },
        "newSourcesByMechanism": new_sources_by_mechanism,
        "featureFamilies": {
            mechanism: [family["familyId"] for family in mechanisms[mechanism]["featureFamilies"]]
            for mechanism in MECHANISMS
        },
        "episodeIdsByMechanism": {
            mechanism: [item["episodeId"] for item in mechanisms[mechanism]["episodeSignatures"]]
            for mechanism in MECHANISMS
        },
        "decision": {
            "newInformationHypothesisPreregistered": True,
            "sourceFeasibilityAuditAuthorized": True,
            "sourceAcquisitionAuthorized": False,
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
            "datasetRead": False,
            "sourceDownloaded": False,
            "featureMaterialized": False,
            "taxonomyMutated": False,
            "candidateGenerated": False,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "candidateRanked": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "implementation": {
            "module": "regime_eval.e14_new_information_hypothesis",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output, payload)


def _validate(
    contract: dict[str, Any], taxonomy: dict[str, Any], mechanism_contract: dict[str, Any],
    source_catalog: dict[str, Any], diagnostic: dict[str, Any], plan: dict[str, Any],
    schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    invalid = (
        contract.get("schemaVersion") != 1
        or contract.get("contractId") != "e14-new-information-hypothesis-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedStatus") != STATUS
        or contract.get("requiredMechanisms") != MECHANISMS
        or not contract.get("authorizationPolicy", {}).get("hypothesisPreregistrationAuthorized")
        or not contract.get("authorizationPolicy", {}).get("sourceFeasibilityAuditAuthorized")
        or any(contract.get("authorizationPolicy", {}).get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
        or diagnostic.get("status") != "LOEO_V2_NO_GO_DIAGNOSED_NEW_INFORMATION_HYPOTHESIS_REQUIRED"
        or diagnostic.get("decision", {}).get("existingCandidateFamilyClosedNoGo") is not True
        or diagnostic.get("decision", {}).get("newInformationHypothesisDesignAuthorized") is not True
        or diagnostic.get("decision", {}).get("candidateEvaluationAuthorized") is not False
        or mechanism_contract.get("requiredMechanisms") != [
            "broad-market-repricing", "funding-liquidity", "banking-credit", "cross-border-growth"
        ]
        or schema.get("$id") != "e14-new-information-hypothesis-schema-v1"
        or plan.get("schemaVersion") != 1
        or plan.get("planId") != "e14-new-information-hypothesis-plan-v1"
        or plan.get("authorizations") != contract.get("authorizationPolicy")
        or taxonomy.get("schemaVersion") != 5
        or source_catalog.get("catalogId") != "e14-historical-source-catalog-v1"
    )
    if invalid:
        raise DatasetValidationError("E14.7 hypothesis inputs or governance are invalid.")

    mechanisms = plan.get("mechanisms", [])
    if [item.get("mechanism") for item in mechanisms] != MECHANISMS:
        raise DatasetValidationError("E14.7 mechanisms must occur exactly once in frozen order.")
    sources = plan.get("sourceCatalog", [])
    source_ids = [item.get("sourceId") for item in sources]
    if (
        len(source_ids) != len(set(source_ids))
        or any(not item.get("url", "").startswith("https://") for item in sources)
        or any(not item.get("knownLimitations") for item in sources)
    ):
        raise DatasetValidationError("E14.7 source catalog is not finite, unique and reviewable.")

    prior_sources = {item["id"] for item in source_catalog["sources"]}
    diagnostic_episodes = {
        mechanism: {item["episodeId"] for item in diagnostic["episodeDiagnostics"][mechanism]}
        for mechanism in MECHANISMS
    }
    family_ids: set[str] = set()
    feature_family_count = 0
    for mechanism in mechanisms:
        name = mechanism["mechanism"]
        families = mechanism.get("featureFamilies", [])
        ids = [item.get("familyId") for item in families]
        feature_family_count += len(families)
        if len(families) < 2 or len(ids) != len(set(ids)) or family_ids.intersection(ids):
            raise DatasetValidationError("E14.7 feature families are not finite and mechanism-specific.")
        family_ids.update(ids)
        used_sources = {source for family in families for source in family.get("sourceIds", [])}
        if not used_sources.issubset(set(source_ids)) or not (used_sources - prior_sources):
            raise DatasetValidationError("E14.7 each mechanism requires at least one new resolved source.")
        for family in families:
            if (
                family.get("missingnessPolicy") != "explicit-missing-no-zero-imputation"
                or not family.get("regimePolicy")
                or family.get("minimumHistoryMonths", 0) < 36
            ):
                raise DatasetValidationError("E14.7 family availability policy is invalid.")
        signatures = mechanism.get("episodeSignatures", [])
        episode_ids = [item.get("episodeId") for item in signatures]
        if (
            len(episode_ids) != len(set(episode_ids))
            or set(episode_ids) != diagnostic_episodes[name]
            or len(signatures) != contract["expectedEpisodeSignatureCountByMechanism"][name]
        ):
            raise DatasetValidationError("E14.7 episode signatures do not match the frozen LOEO episodes.")
        for signature in signatures:
            if not signature.get("falsificationCondition"):
                raise DatasetValidationError("E14.7 falsification conditions are required.")
            for phase in ("onset", "intensity", "recovery"):
                value = signature.get(phase, {})
                window = value.get("windowMonths", [])
                if (
                    not set(value.get("familyIds", [])).issubset(set(ids))
                    or not value.get("familyIds")
                    or len(window) != 2
                    or window[0] > window[1]
                ):
                    raise DatasetValidationError("E14.7 phase signatures are invalid.")
        if len(mechanism.get("ablationIds", [])) < 3:
            raise DatasetValidationError("E14.7 ablation design is incomplete.")

    if feature_family_count != contract["expectedFeatureFamilyCount"]:
        raise DatasetValidationError("E14.7 feature-family budget differs from contract.")
    if (
        plan.get("readinessPolicy", {}).get("nextRequiredArtifact")
        != "E14.7a source-and-vintage feasibility audit"
        or plan.get("ablationPolicy", {}).get("candidateBudgetDeferredUntilReadiness") is not True
        or any(plan.get("authorizations", {}).get(key) is not False for key in FORBIDDEN_AUTHORIZATIONS)
    ):
        raise DatasetValidationError("E14.7 readiness boundary is invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    file = Path(path).resolve()
    if not file.exists():
        raise DatasetValidationError(f"E14.7 {label} does not exist: {file}")
    raw = file.read_bytes()
    try:
        return file, raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7 {label} is not valid UTF-8 JSON.") from error


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write_new(path: Path, payload: dict[str, Any]) -> Path:
    if path.exists():
        raise DatasetValidationError("Immutable E14.7 hypothesis audit output already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return path
