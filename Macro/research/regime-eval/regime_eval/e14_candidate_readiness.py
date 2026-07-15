from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_taxonomy_v4 import _same_mechanism_conflicts


BLOCKED_STATUS = "CANDIDATE_READINESS_BLOCKED_FOUNDATION_AND_PROTOCOL"
READY_STATUS = "CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED"


def write_e14_candidate_readiness_gate(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    materialization_audit_path: str | Path,
    mechanism_contract_path: str | Path,
    source_catalog_path: str | Path,
    legacy_candidate_protocol_path: str | Path,
    legacy_foundation_lock_path: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_raw, contract = _read(contract_path, "readiness contract")
    taxonomy_file, taxonomy_raw, taxonomy = _read(taxonomy_path, "taxonomy v5")
    audit_file, audit_raw, audit = _read(materialization_audit_path, "materialization audit")
    mechanism_file, mechanism_raw, mechanism = _read(mechanism_contract_path, "mechanism contract")
    catalog_file, catalog_raw, catalog = _read(source_catalog_path, "source catalog")
    protocol_file, protocol_raw, protocol = _read(legacy_candidate_protocol_path, "legacy protocol")
    lock_file, lock_raw, lock = _read(legacy_foundation_lock_path, "legacy foundation lock")
    _validate_contract(
        contract, taxonomy, audit, mechanism, catalog, protocol, lock,
        taxonomy_raw, audit_raw, mechanism_raw, catalog_raw, protocol_raw, lock_raw,
    )

    required = contract["requiredMechanisms"]
    taxonomy_mechanisms = set(taxonomy["mechanisms"])
    detector_mechanisms = {item["mechanism"] for item in mechanism["detectors"]}
    features = [
        {"detectorId": detector["detectorId"], "mechanism": detector["mechanism"], **feature}
        for detector in mechanism["detectors"]
        for feature in detector["featureProposals"]
    ]
    populated = [item for item in features if item.get("status") == "populated-manifested"]
    source_ids = {item["id"] for item in catalog["sources"]}
    feature_sources_known = all(item["sourceId"] in source_ids for item in features)
    conflicts = _same_mechanism_conflicts(taxonomy)
    taxonomy_sha = hashlib.sha256(taxonomy_raw).hexdigest()

    checks = {
        "taxonomyHashBound": taxonomy_sha == contract["inputHashes"]["taxonomyV5Sha256"],
        "taxonomyMaterializationAccepted": audit["decision"]["taxonomyV5Ready"] is True,
        "taxonomyCoverageSufficient": taxonomy["coverage"]["coverageThresholdsSatisfied"] is True,
        "sameMechanismMonthStatesConsistent": not conflicts,
        "requiredMechanismsPresent": taxonomy_mechanisms == set(required),
        "oneIndependentDetectorPerMechanism": detector_mechanisms == set(required)
        and len(mechanism["detectors"]) == len(required),
        "allFeatureSourcesKnown": feature_sources_known,
        "pointInTimeFeatureFoundationMaterialized": False,
        "allDetectorFeaturesPopulated": len(populated) == len(features),
        "generationProtocolBoundToTaxonomyV5": protocol.get("foundationLockSha256") == taxonomy_sha,
        "generationProtocolMechanismSeparated": set(protocol.get("tasks", {})) == set(required),
        "innerOnlyThresholdSelection": protocol.get("thresholdSelection", {}).get("scope")
        == "inner-fit-only",
        "causalTrainOnlyTransforms": all(
            protocol.get("constraints", {}).get(key) is True
            for key in ("causalFeaturesOnly", "trainOnlyTransforms")
        ),
        "missingnessExplicit": protocol.get("constraints", {}).get("missingValuesRemainExplicit")
        is True,
        "outerOosClosed": "Forbidden" in protocol.get("selectionPolicy", {}).get("outerOos", ""),
    }
    blockers = []
    if not checks["allDetectorFeaturesPopulated"]:
        blockers.append("DETECTOR_FEATURES_NOT_POPULATED")
    if not checks["pointInTimeFeatureFoundationMaterialized"]:
        blockers.append("FEATURE_FOUNDATION_NOT_MATERIALIZED")
    if not checks["generationProtocolBoundToTaxonomyV5"]:
        blockers.append("GENERATION_PROTOCOL_FOUNDATION_MISMATCH")
    if not checks["generationProtocolMechanismSeparated"]:
        blockers.append("GENERATION_PROTOCOL_TASK_GRAMMAR_MISMATCH")
    if blockers != contract["expectedCurrentBlockers"]:
        raise DatasetValidationError("E14 candidate-readiness blockers differ from the frozen expectation.")

    ready = not blockers and all(checks.values())
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14CandidateReadinessGateAudit",
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "inputs": {
            "contract": _artifact(contract_file, contract_raw),
            "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
            "taxonomyV5MaterializationAudit": _artifact(audit_file, audit_raw),
            "mechanismContract": _artifact(mechanism_file, mechanism_raw),
            "sourceCatalog": _artifact(catalog_file, catalog_raw),
            "legacyCandidateProtocol": _artifact(protocol_file, protocol_raw),
            "legacyFoundationLock": _artifact(lock_file, lock_raw),
        },
        "inventory": {
            "requiredMechanismCount": len(required),
            "detectorCount": len(mechanism["detectors"]),
            "detectorFeatureProposalCount": len(features),
            "populatedManifestedFeatureCount": len(populated),
            "positiveEpisodeCount": taxonomy["coverage"]["combinedPositiveEpisodeCount"],
            "hardNegativeEpisodeCount": taxonomy["coverage"]["combinedHardNegativeEpisodeCount"],
            "sameMechanismMonthConflictCount": len(conflicts),
        },
        "checks": checks,
        "blockers": blockers,
        "legacyProtocolDiagnosis": {
            "protocolId": protocol["protocolId"],
            "taskIds": sorted(protocol["tasks"]),
            "foundationLockSha256": protocol["foundationLockSha256"],
            "taxonomyV5Sha256": taxonomy_sha,
            "legacyFoundationLockMatchesProtocol": hashlib.sha256(lock_raw).hexdigest()
            == protocol["foundationLockSha256"],
            "safeControlsReusable": checks["innerOnlyThresholdSelection"]
            and checks["causalTrainOnlyTransforms"] and checks["missingnessExplicit"]
            and checks["outerOosClosed"],
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "candidateGenerated": False,
            "taxonomyMutated": False,
            "promotionPerformed": False,
        },
        "decision": {
            "candidateReadinessSatisfied": ready,
            "candidateGenerationAuthorized": ready,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAfterBlocked"] if not ready else "Generate only preregistered inner-development candidates.",
        },
        "implementation": {
            "module": "regime_eval.e14_candidate_readiness",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new(output_path, payload)


def _validate_contract(
    contract: Any, taxonomy: Any, audit: Any, mechanism: Any, catalog: Any,
    protocol: Any, lock: Any, taxonomy_raw: bytes, audit_raw: bytes,
    mechanism_raw: bytes, catalog_raw: bytes, protocol_raw: bytes, lock_raw: bytes,
) -> None:
    actual_hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "taxonomyV5MaterializationAuditSha256": hashlib.sha256(audit_raw).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_raw).hexdigest(),
        "sourceCatalogSha256": hashlib.sha256(catalog_raw).hexdigest(),
        "legacyCandidateProtocolSha256": hashlib.sha256(protocol_raw).hexdigest(),
        "legacyFoundationLockSha256": hashlib.sha256(lock_raw).hexdigest(),
    }
    expected_readiness = {
        "taxonomyIntegrityRequired": True,
        "acceptedCoverageRequired": True,
        "zeroSameMechanismMonthConflictsRequired": True,
        "independentDetectorPerMechanismRequired": True,
        "materializedPointInTimeFeatureFoundationRequired": True,
        "allDetectorFeaturesPopulatedRequired": True,
        "generationProtocolBoundToTaxonomyV5Required": True,
        "generationProtocolMechanismSeparatedRequired": True,
        "innerOnlyThresholdSelectionRequired": True,
        "causalTrainOnlyTransformsRequired": True,
        "missingnessExplicitRequired": True,
    }
    expected_auth = {
        "readinessAuditAuthorized": True,
        "candidateGenerationAuthorizedOnlyOnPass": True,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
        "taxonomyMutationAuthorized": False,
    }
    if (
        contract.get("contractId") != "e14-candidate-readiness-gate-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("readinessPolicy") != expected_readiness
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedBlockedStatus") != BLOCKED_STATUS
        or taxonomy.get("groundTruthId") != contract.get("requiredGroundTruthId")
        or taxonomy.get("schemaVersion") != 5
        or audit.get("status") != contract.get("requiredTaxonomyStatus")
        or audit.get("output", {}).get("sha256") != actual_hashes["taxonomyV5Sha256"]
        or audit.get("decision", {}).get("candidateReadinessGateAuthorized") is not True
        or audit.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or mechanism.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or catalog.get("catalogId") != "e14-historical-source-catalog-v1"
        or protocol.get("protocolId") != "e13-candidate-generation-protocol-v1"
        or not isinstance(lock, dict)
    ):
        raise DatasetValidationError("E14 candidate-readiness inputs or contract are invalid.")


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(
            f"Immutable E14 candidate-readiness audit already exists: '{destination}'."
        ) from exc
    return destination
