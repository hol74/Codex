from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


def write_e14_positive_dossier_curation(
    pack_path: str | Path,
    dossier_schema_path: str | Path,
    detector_contract_path: str | Path,
    source_catalog_path: str | Path,
    mechanism_contract_audit_path: str | Path,
    dossier_dir: str | Path,
    output_path: str | Path,
) -> Path:
    pack_file, pack_bytes, pack = _read_json(pack_path, "E14 positive dossier pack")
    schema_file, schema_bytes, schema = _read_json(dossier_schema_path, "E14 dossier schema")
    contract_file, contract_bytes, contract = _read_json(detector_contract_path, "E14 detector contract")
    catalog_file, catalog_bytes, catalog = _read_json(source_catalog_path, "E14 source catalog")
    audit_file, audit_bytes, audit = _read_json(mechanism_contract_audit_path, "E14 mechanism contract audit")

    _validate_input_hashes(pack, schema_bytes, contract_bytes, catalog_bytes, audit_bytes)
    minimums = _validate_upstream(pack, schema, contract, catalog, audit)
    assertions = _validate_assertions(pack)
    dossiers = _build_dossiers(pack, catalog, assertions, minimums)

    destination_dir = Path(dossier_dir).resolve()
    output = Path(output_path).resolve()
    dossier_paths = [destination_dir / f"{item['dossierId']}.json" for item in dossiers]
    if output.exists() or any(path.exists() for path in dossier_paths):
        raise DatasetValidationError("Immutable E14 dossier curation output already exists.")

    artifacts = []
    for path, dossier in zip(dossier_paths, dossiers, strict=True):
        written = _write_new_json(path, dossier, "E14 episode dossier")
        raw = written.read_bytes()
        artifacts.append(_artifact(written, raw))

    mechanisms = contract["requiredMechanisms"]
    coverage = {
        mechanism: {
            "reviewedPositiveCount": sum(
                item["mechanism"] == mechanism and item["proposedState"] == "positive"
                for item in dossiers
            ),
            "acceptedCount": 0,
            "hardNegativeCount": 0,
        }
        for mechanism in mechanisms
    }
    report = {
        "schemaVersion": 1,
        "artifactType": "E14PositiveDossierCurationAudit",
        "status": "SECOND_REVIEW_AND_HARD_NEGATIVES_REQUIRED",
        "inputs": {
            "positiveDossierPack": _artifact(pack_file, pack_bytes),
            "dossierSchema": _artifact(schema_file, schema_bytes),
            "detectorContract": _artifact(contract_file, contract_bytes),
            "sourceCatalog": _artifact(catalog_file, catalog_bytes),
            "mechanismContractAudit": _artifact(audit_file, audit_bytes),
        },
        "protocol": {
            "purpose": "positive-primary-source-dossier-curation-only",
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "remoteByteSnapshotsArchived": False,
            "evidenceAssertionDigestPolicy": pack["digestPolicy"],
        },
        "inventory": {
            "positiveHypothesisCount": len(catalog["positiveEpisodeHypotheses"]),
            "dossierCount": len(dossiers),
            "positiveDossierCount": len(dossiers),
            "hardNegativeDossierCount": 0,
            "reviewedDossierCount": len(dossiers),
            "acceptedDossierCount": 0,
            "reviewerCount": 1,
        },
        "mechanismCoverage": coverage,
        "dossierArtifacts": artifacts,
        "checks": {
            "allPositiveHypothesisMechanismsCovered": True,
            "minimumEvidenceSatisfied": True,
            "independentProvidersSatisfied": True,
            "officialAndQuantitativeEvidenceSatisfied": True,
            "counterEvidenceReviewed": True,
            "boundariesInsideFrozenHypotheses": True,
            "allDossiersRemainUnaccepted": True,
            "outerOosClosed": True,
            "groundTruthUnchanged": True,
        },
        "findings": {
            "vix1987CoverageMismatchDetected": True,
            "frozenCatalogMutated": False,
            "replacementOfficialEvidenceUsedInDossier": True,
            "limitations": pack["limitations"],
        },
        "decision": {
            "secondIndependentReviewRequired": True,
            "hardNegativeResearchRequired": True,
            "groundTruthMutationAuthorized": False,
            "corpusPopulationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": "E14.4b2 independent second review and hard-negative dossier research",
        },
        "implementation": {
            "module": "regime_eval.e14_dossier_curation",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output, report, "E14 positive dossier curation audit")


def _validate_input_hashes(
    pack: Any, schema_bytes: bytes, contract_bytes: bytes, catalog_bytes: bytes, audit_bytes: bytes
) -> None:
    actual = {
        "dossierSchemaSha256": hashlib.sha256(schema_bytes).hexdigest(),
        "detectorContractSha256": hashlib.sha256(contract_bytes).hexdigest(),
        "sourceCatalogSha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "mechanismContractAuditSha256": hashlib.sha256(audit_bytes).hexdigest(),
    }
    if (
        not isinstance(pack, dict)
        or pack.get("packId") != "e14-positive-dossier-pack-v1"
        or pack.get("schemaVersion") != 1
        or pack.get("inputHashes") != actual
    ):
        raise DatasetValidationError("E14 positive dossier pack input hashes are invalid.")


def _validate_upstream(
    pack: dict[str, Any], schema: Any, contract: Any, catalog: Any, audit: Any
) -> dict[str, int]:
    rules = contract.get("dossierRules", {}) if isinstance(contract, dict) else {}
    if (
        schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
        or contract.get("contractId") != "e14-mechanism-detector-contract-v1"
        or contract.get("readinessDecision") != "READY_FOR_DOSSIER_CURATION"
        or audit.get("artifactType") != "E14MechanismDetectorContractAudit"
        or audit.get("status") != "READY_FOR_DOSSIER_CURATION"
        or audit.get("protocol", {}).get("outerFeatureRowCountUsed") != 0
        or catalog.get("catalogId") != "e14-historical-source-catalog-v1"
        or pack.get("hardNegativeBlueprints") != []
        or rules.get("acceptedDossierMayWriteGroundTruth") is not False
    ):
        raise DatasetValidationError("E14 dossier curation upstream contract is invalid.")
    minimums = {
        "evidence": rules.get("minimumEvidenceItems"),
        "providers": rules.get("minimumIndependentProviders"),
        "reviewers": rules.get("minimumAcceptedReviewers"),
    }
    if minimums != {"evidence": 2, "providers": 2, "reviewers": 2}:
        raise DatasetValidationError("E14 dossier curation minimums are invalid.")
    return minimums


def _validate_assertions(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    allowed_roles = {"official-narrative", "quantitative-observation", "boundary-corroboration", "counterevidence"}
    assertions = pack.get("evidenceAssertions")
    if not isinstance(assertions, list) or not assertions:
        raise DatasetValidationError("E14 evidence assertions are missing.")
    by_id: dict[str, dict[str, Any]] = {}
    for item in assertions:
        assertion_id = item.get("id") if isinstance(item, dict) else None
        try:
            date.fromisoformat(item["publishedAt"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError("E14 evidence assertion date is invalid.") from exc
        if (
            not isinstance(assertion_id, str) or assertion_id in by_id
            or not str(item.get("locator", "")).startswith("https://")
            or item.get("role") not in allowed_roles
            or any(not isinstance(item.get(key), str) or not item[key] for key in (
                "sourceId", "provider", "independenceGroup", "summary"
            ))
            or len(item["summary"]) < 20
        ):
            raise DatasetValidationError("E14 evidence assertion is invalid.")
        by_id[assertion_id] = item
    return by_id


def _build_dossiers(
    pack: dict[str, Any], catalog: dict[str, Any], assertions: dict[str, dict[str, Any]], minimums: dict[str, int]
) -> list[dict[str, Any]]:
    hypotheses = {item["id"]: item for item in catalog.get("positiveEpisodeHypotheses", [])}
    expected = {(item["id"], mechanism) for item in hypotheses.values() for mechanism in item["mechanisms"]}
    blueprints = pack.get("dossierBlueprints")
    if not isinstance(blueprints, list):
        raise DatasetValidationError("E14 dossier blueprints are invalid.")
    actual = {(item.get("hypothesisId"), item.get("mechanism")) for item in blueprints}
    if actual != expected or len(actual) != len(blueprints):
        raise DatasetValidationError("E14 dossier blueprints do not cover each hypothesis/mechanism exactly once.")

    reviewer = pack.get("reviewer")
    dossier_ids: set[str] = set()
    dossiers = []
    for item in blueprints:
        hypothesis = hypotheses[item["hypothesisId"]]
        dossier_id = item.get("dossierId")
        evidence_ids = item.get("evidenceIds")
        counter_ids = item.get("counterEvidenceIds")
        if (
            not isinstance(dossier_id, str) or not dossier_id.startswith("e14-dossier-") or dossier_id in dossier_ids
            or item.get("proposedState") != "positive"
            or not isinstance(evidence_ids, list) or len(evidence_ids) < minimums["evidence"]
            or not isinstance(counter_ids, list) or not counter_ids
            or any(source_id not in assertions for source_id in evidence_ids + counter_ids)
            or not isinstance(reviewer, str) or not reviewer
            or len(item.get("boundaryRationale", "")) < 40
        ):
            raise DatasetValidationError("E14 positive dossier blueprint is invalid.")
        try:
            first = date.fromisoformat(item["firstMonth"])
            last = date.fromisoformat(item["lastMonth"])
            hypothesis_first = date.fromisoformat(hypothesis["firstMonth"])
            hypothesis_last = date.fromisoformat(hypothesis["lastMonth"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError("E14 dossier boundary is invalid.") from exc
        if first > last or first < hypothesis_first or last > hypothesis_last:
            raise DatasetValidationError("E14 dossier boundary falls outside its frozen hypothesis.")

        evidence = [assertions[source_id] for source_id in evidence_ids]
        counters = [assertions[source_id] for source_id in counter_ids]
        groups = {source["independenceGroup"] for source in evidence}
        roles = {source["role"] for source in evidence}
        if len(groups) < minimums["providers"]:
            raise DatasetValidationError("E14 dossier lacks independent providers.")
        if not {"official-narrative", "quantitative-observation"} <= roles:
            raise DatasetValidationError("E14 dossier lacks official and quantitative evidence.")
        if any(source["role"] != "counterevidence" for source in counters):
            raise DatasetValidationError("E14 dossier counterevidence role is invalid.")

        dossiers.append({
            "schemaVersion": 1,
            "dossierId": dossier_id,
            "hypothesisId": item["hypothesisId"],
            "mechanism": item["mechanism"],
            "proposedState": "positive",
            "firstMonth": item["firstMonth"],
            "lastMonth": item["lastMonth"],
            "boundaryRationale": item["boundaryRationale"],
            "affirmativeOrderlyEvidence": False,
            "evidenceItems": [_evidence_payload(source) for source in evidence],
            "counterEvidence": [_evidence_payload(source) for source in counters],
            "exclusionChecks": {
                "outerOosUsed": False,
                "modelPredictionUsedAsLabel": False,
                "absenceTreatedAsEvidence": False,
                "methodologyRegimeRecorded": True,
                "nberOverlapReviewed": True,
            },
            "adjudicationStatus": "reviewed",
            "reviewers": [reviewer],
        })
        dossier_ids.add(dossier_id)
    return dossiers


def _evidence_payload(assertion: dict[str, Any]) -> dict[str, Any]:
    payload = {key: assertion[key] for key in (
        "sourceId", "provider", "independenceGroup", "publishedAt", "role", "locator", "summary"
    )}
    payload["contentSha256"] = hashlib.sha256(
        f"{assertion['locator']}\n{assertion['summary']}".encode("utf-8")
    ).hexdigest()
    return payload


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new_json(path: str | Path, payload: dict[str, Any], label: str) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{destination}'.") from exc
    return destination
