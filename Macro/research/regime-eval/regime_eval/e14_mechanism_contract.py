from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


def write_e14_mechanism_contract_audit(
    detector_contract_path: str | Path,
    dossier_schema_path: str | Path,
    source_catalog_path: str | Path,
    feasibility_report_path: str | Path,
    taxonomy_path: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_bytes, contract = _read_json(detector_contract_path, "E14 detector contract")
    schema_file, schema_bytes, schema = _read_json(dossier_schema_path, "E14 dossier schema")
    catalog_file, catalog_bytes, catalog = _read_json(source_catalog_path, "E14 source catalog")
    feasibility_file, feasibility_bytes, feasibility = _read_json(feasibility_report_path, "E14 feasibility report")
    taxonomy_file, taxonomy_bytes, taxonomy = _read_json(taxonomy_path, "E14 taxonomy")

    _validate_input_hashes(contract, schema_bytes, catalog_bytes, feasibility_bytes, taxonomy_bytes)
    schema_checks = _validate_dossier_schema(schema)
    sources = _validate_upstream(catalog, feasibility, taxonomy, contract)
    detector_rows, contract_checks = _validate_detector_contract(contract, sources)
    checks = {**schema_checks, **contract_checks}
    passed = all(checks.values())
    if not passed:
        raise DatasetValidationError("E14 mechanism detector contract checks failed.")

    feature_count = sum(len(item["featureSourceIds"]) for item in detector_rows)
    diagnostic_ids = sorted({source for item in detector_rows for source in item["diagnosticBenchmarkSourceIds"]})
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14MechanismDetectorContractAudit",
        "status": contract["readinessDecision"],
        "inputs": {
            "detectorContract": _artifact(contract_file, contract_bytes),
            "dossierSchema": _artifact(schema_file, schema_bytes),
            "sourceCatalog": _artifact(catalog_file, catalog_bytes),
            "historicalFeasibility": _artifact(feasibility_file, feasibility_bytes),
            "taxonomyV3": _artifact(taxonomy_file, taxonomy_bytes),
        },
        "protocol": {
            "purpose": "mechanism-contract-and-dossier-schema-only",
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "dossierCountRead": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "compositionProduced": False,
            "promotionAuthorized": False,
        },
        "inventory": {
            "detectorCount": len(detector_rows),
            "featureProposalCount": feature_count,
            "diagnosticBenchmarkSourceCount": len(diagnostic_ids),
            "phaseCount": len(contract["phaseModel"]["states"]),
            "positiveHypothesisCountAvailableForDossiers": len(catalog["positiveEpisodeHypotheses"]),
            "hardNegativeHypothesisCountAvailableForDossiers": len(catalog["hardNegativeHypotheses"]),
        },
        "detectors": detector_rows,
        "checks": checks,
        "failedChecks": [],
        "decision": {
            "status": contract["readinessDecision"],
            "contractAuditPassed": True,
            "dossierCurationAuthorized": True,
            "groundTruthMutationAuthorized": False,
            "corpusPopulationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": "E14.4b curate and adjudicate mechanism-specific episode dossiers",
        },
        "implementation": {
            "module": "regime_eval.e14_mechanism_contract",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _validate_input_hashes(
    contract: Any,
    schema_bytes: bytes,
    catalog_bytes: bytes,
    feasibility_bytes: bytes,
    taxonomy_bytes: bytes,
) -> None:
    actual = {
        "dossierSchemaSha256": hashlib.sha256(schema_bytes).hexdigest(),
        "sourceCatalogSha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "historicalFeasibilitySha256": hashlib.sha256(feasibility_bytes).hexdigest(),
        "taxonomyV3Sha256": hashlib.sha256(taxonomy_bytes).hexdigest(),
    }
    if (
        not isinstance(contract, dict)
        or contract.get("contractId") != "e14-mechanism-detector-contract-v1"
        or contract.get("inputHashes") != actual
    ):
        raise DatasetValidationError("E14 mechanism detector input hashes are invalid.")


def _validate_dossier_schema(schema: Any) -> dict[str, bool]:
    try:
        required = set(schema["required"])
        hard_negative_then = schema["allOf"][0]["then"]["properties"]["affirmativeOrderlyEvidence"]
        accepted_reviewers = schema["allOf"][1]["then"]["properties"]["reviewers"]
        exclusions = schema["properties"]["exclusionChecks"]["properties"]
        evidence = schema["$defs"]["evidenceItem"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DatasetValidationError("E14 dossier schema is invalid.") from exc
    checks = {
        "dossierSchemaClosed": schema.get("additionalProperties") is False,
        "dossierSchemaRequiredFields": {
            "mechanism", "proposedState", "evidenceItems", "counterEvidence",
            "affirmativeOrderlyEvidence", "exclusionChecks", "reviewers",
        } <= required,
        "hardNegativeRequiresAffirmativeEvidence": hard_negative_then.get("const") is True,
        "acceptedDossierRequiresTwoReviewers": accepted_reviewers.get("minItems") == 2,
        "dossierForbidsOuterAndModelLabels": (
            exclusions["outerOosUsed"].get("const") is False
            and exclusions["modelPredictionUsedAsLabel"].get("const") is False
            and exclusions["absenceTreatedAsEvidence"].get("const") is False
        ),
        "dossierEvidenceIsHashBound": "contentSha256" in evidence.get("required", []),
    }
    if not all(checks.values()):
        raise DatasetValidationError("E14 dossier schema is unsafe.")
    return checks


def _validate_upstream(
    catalog: Any,
    feasibility: Any,
    taxonomy: Any,
    contract: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if (
        catalog.get("catalogId") != "e14-historical-source-catalog-v1"
        or feasibility.get("artifactType") != "E14HistoricalFoundationFeasibility"
        or feasibility.get("status") != "GO_FOR_EPISODE_DOSSIERS_ONLY"
        or feasibility.get("decision", {}).get("episodeDossierCurationAuthorized") is not True
        or feasibility.get("decision", {}).get("fullCorpusPopulationAuthorized") is not False
        or feasibility.get("protocol", {}).get("outerFeatureRowCountUsed") != 0
        or taxonomy.get("groundTruthId") != "us-financial-stress-tristate-v3"
        or set(taxonomy.get("mechanisms", {})) != set(contract.get("requiredMechanisms", []))
    ):
        raise DatasetValidationError("E14 mechanism detector upstream inputs are invalid.")
    sources = catalog.get("sources", [])
    by_id = {item.get("id"): item for item in sources}
    if None in by_id or len(by_id) != len(sources):
        raise DatasetValidationError("E14 source catalog ids are invalid.")
    return by_id


def _validate_detector_contract(
    contract: dict[str, Any], sources: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    required = contract.get("requiredMechanisms", [])
    detectors = contract.get("detectors", [])
    policies = contract.get("globalPolicies", {})
    phase = contract.get("phaseModel", {})
    evaluation = contract.get("evaluationContract", {})
    dossier_rules = contract.get("dossierRules", {})
    if not isinstance(detectors, list):
        raise DatasetValidationError("E14 detector collection is invalid.")

    allowed_transforms = set(policies.get("transformPolicy", {}).get("allowed", []))
    rows = []
    detector_ids: set[str] = set()
    mechanisms: set[str] = set()
    for detector in detectors:
        detector_id = detector.get("detectorId")
        mechanism = detector.get("mechanism")
        proposals = detector.get("featureProposals")
        diagnostic_ids = detector.get("diagnosticBenchmarkSourceIds")
        if (
            not isinstance(detector_id, str) or detector_id in detector_ids
            or mechanism not in required or mechanism in mechanisms
            or not isinstance(proposals, list) or not proposals
            or not isinstance(diagnostic_ids, list)
            or "affirm" not in detector.get("hardNegativeDefinition", "").lower()
            or len(detector.get("positiveDefinition", "")) < 40
        ):
            raise DatasetValidationError("E14 mechanism detector definition is invalid.")
        feature_ids = []
        for proposal in proposals:
            source = sources.get(proposal.get("sourceId"))
            if (
                source is None or source.get("sourceType") != "feature"
                or source.get("eligibility") in {"diagnostic-only", "label-only"}
                or proposal.get("transform") not in allowed_transforms
                or proposal.get("status") != "proposal-not-populated"
                or mechanism not in source.get("mechanisms", [])
            ):
                raise DatasetValidationError("E14 detector feature proposal is not eligible.")
            feature_ids.append(proposal["sourceId"])
        for source_id in diagnostic_ids:
            source = sources.get(source_id)
            if source is None or source.get("eligibility") != "diagnostic-only":
                raise DatasetValidationError("E14 diagnostic benchmark is not diagnostic-only.")
        rows.append({
            "detectorId": detector_id,
            "mechanism": mechanism,
            "featureSourceIds": feature_ids,
            "diagnosticBenchmarkSourceIds": diagnostic_ids,
            "phaseStates": phase.get("states"),
            "status": "contract-only-not-fitted",
        })
        detector_ids.add(detector_id)
        mechanisms.add(mechanism)

    hard_rules = " ".join(dossier_rules.get("hardNegativeRequirements", []))
    checks = {
        "oneIndependentDetectorPerMechanism": mechanisms == set(required) and len(rows) == len(required),
        "compositionClosed": policies.get("compositionAuthorized") is False and evaluation.get("crossMechanismScore") is False,
        "candidateGenerationClosed": policies.get("candidateGenerationAuthorized") is False,
        "corpusPopulationClosed": policies.get("corpusPopulationAuthorized") is False,
        "outerOosClosed": "forbidden" in str(policies.get("outerOosPolicy")) and evaluation.get("outerOosOpened") is False,
        "causalTransformsOnly": (
            policies.get("transformPolicy", {}).get("historyDirection") == "strictly-prior-and-current-only"
            and policies.get("transformPolicy", {}).get("fitScope") == "inner-only"
        ),
        "missingnessAndRegimesExplicit": "splicing" in str(policies.get("missingnessPolicy")),
        "onsetActiveRecoverySeparated": phase.get("states") == ["calm", "onset", "active", "recovery"] and phase.get("hysteresisRequired") is True,
        "hardNegativeEvidenceAffirmative": "affirmatively" in hard_rules and "never evidence" in hard_rules,
        "dossierCannotDirectlyMutateTruth": dossier_rules.get("acceptedDossierMayWriteGroundTruth") is False,
        "futureThresholdSelectionInnerOnly": "inner" in str(policies.get("thresholdPolicy")) and evaluation.get("selectionScope") == "inner-leave-one-episode-out-only",
        "contractReadyForDossiersOnly": contract.get("readinessDecision") == "READY_FOR_DOSSIER_CURATION",
    }
    if not all(checks.values()):
        raise DatasetValidationError("E14 mechanism detector contract is unsafe.")
    return rows, checks


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E14 mechanism contract audit exists: '{destination}'.") from exc
    return destination
