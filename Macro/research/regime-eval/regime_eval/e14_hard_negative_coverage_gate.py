from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .dataset import DatasetValidationError


ACCEPT_PREFIX = "accept-by-"


def write_e14_hard_negative_coverage_gate(
    contract_path: str | Path,
    reviewed_queue_path: str | Path,
    targeted_ingestion_audit_path: str | Path,
    taxonomy_path: str | Path,
    dossier_schema_path: str | Path,
    label_audit_contract_path: str | Path,
    mechanism_contract_path: str | Path,
    expansion_contract_path: str | Path,
    dossier_dirs: Iterable[str | Path],
    output_path: str | Path,
) -> Path:
    contract_file, contract_raw, contract = _read_json(contract_path, "coverage contract")
    queue_file, queue_raw, queue = _read_json(reviewed_queue_path, "reviewed queue v11")
    ingestion_file, ingestion_raw, ingestion = _read_json(
        targeted_ingestion_audit_path, "targeted ingestion audit v2"
    )
    taxonomy_file, taxonomy_raw, taxonomy = _read_json(taxonomy_path, "taxonomy v4")
    schema_file, schema_raw, schema = _read_json(dossier_schema_path, "dossier schema")
    label_file, label_raw, label_contract = _read_json(label_audit_contract_path, "label contract")
    mechanism_file, mechanism_raw, mechanism_contract = _read_json(
        mechanism_contract_path, "mechanism contract"
    )
    expansion_file, expansion_raw, expansion_contract = _read_json(
        expansion_contract_path, "expansion contract"
    )
    _validate_inputs(
        contract, queue, ingestion, taxonomy, schema, label_contract,
        mechanism_contract, expansion_contract, queue_raw, ingestion_raw,
        taxonomy_raw, schema_raw, label_raw, mechanism_raw, expansion_raw,
    )

    dossiers = _load_dossiers(queue, dossier_dirs)
    taxonomy_dossier_hashes = {
        item["dossierId"]: item["dossierSha256"] for item in taxonomy["foundationEvidence"]
    }
    queue_hashes = {item["dossierId"]: item["sha256"] for item in queue["dossiers"]}
    if any(queue_hashes.get(key) != value for key, value in taxonomy_dossier_hashes.items()):
        raise DatasetValidationError("E14.4h taxonomy foundation dossier hash changed.")

    new_dossiers = [
        dossier for dossier in dossiers.values()
        if dossier["dossierId"] not in taxonomy_dossier_hashes
    ]
    required = contract["requiredMechanisms"]
    if (
        len(new_dossiers) != contract["requiredNewHardNegativeDossierCount"]
        or any(item["proposedState"] != "hard-negative" for item in new_dossiers)
        or {item["mechanism"] for item in new_dossiers} != set(required)
        or len({item["hypothesisId"] for item in new_dossiers}) != len(new_dossiers)
    ):
        raise DatasetValidationError("E14.4h accepted expansion inventory is invalid.")

    conflicts = _same_mechanism_conflicts(taxonomy, new_dossiers)
    coverage = _coverage(taxonomy, new_dossiers, contract)
    passed = not conflicts and coverage["coverageThresholdsSatisfied"]
    status = contract["expectedPassStatus"] if passed else "ACCEPTED_HARD_NEGATIVE_COVERAGE_INSUFFICIENT"
    output = Path(output_path).resolve()
    if output.exists():
        raise DatasetValidationError("Immutable E14.4h coverage audit already exists.")

    new_artifacts = [
        {
            "dossierId": item["dossierId"],
            "dossierSha256": queue_hashes[item["dossierId"]],
            "hypothesisId": item["hypothesisId"],
            "mechanism": item["mechanism"],
            "firstMonth": item["firstMonth"],
            "lastMonth": item["lastMonth"],
            "state": item["proposedState"],
        }
        for item in sorted(new_dossiers, key=lambda value: value["dossierId"])
    ]
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14AcceptedHardNegativeCoverageGateAudit",
        "status": status,
        "inputs": {
            "coverageContract": _artifact(contract_file, contract_raw),
            "reviewedQueueV11": _artifact(queue_file, queue_raw),
            "targetedIngestionAuditV2": _artifact(ingestion_file, ingestion_raw),
            "taxonomyV4": _artifact(taxonomy_file, taxonomy_raw),
            "dossierSchema": _artifact(schema_file, schema_raw),
            "labelAuditContract": _artifact(label_file, label_raw),
            "mechanismContract": _artifact(mechanism_file, mechanism_raw),
            "expansionContract": _artifact(expansion_file, expansion_raw),
        },
        "inventory": {
            "acceptedQueueDossierCount": len(queue["dossiers"]),
            "taxonomyFoundationDossierCount": len(taxonomy_dossier_hashes),
            "newAcceptedHardNegativeDossierCount": len(new_dossiers),
            "newIndependentHardNegativeEventCount": len({item["hypothesisId"] for item in new_dossiers}),
            "sameMechanismMonthConflictCount": len(conflicts),
        },
        "newAcceptedHardNegativeEvidence": new_artifacts,
        "coverageBeforeExpansion": taxonomy["coverage"],
        "acceptedCoverageAfterExpansion": coverage,
        "conflicts": conflicts,
        "checks": {
            "allSixteenQueueDossiersAccepted": True,
            "allManifestHashesResolvedExactlyOnce": True,
            "taxonomyV4HashPreserved": hashlib.sha256(taxonomy_file.read_bytes()).hexdigest()
            == contract["inputHashes"]["taxonomyV4Sha256"],
            "twelveFoundationDossierHashesPreserved": True,
            "fourNewHardNegativesAccepted": len(new_dossiers) == 4,
            "fourNewIndependentEvents": len({item["hypothesisId"] for item in new_dossiers}) == 4,
            "oneNewEventPerMechanism": {item["mechanism"] for item in new_dossiers} == set(required),
            "sameMechanismMonthStatesConsistent": not conflicts,
            "crossMechanismMixedStatesPreserved": True,
            "positiveCoverageThresholdsSatisfied": coverage["positiveThresholdsSatisfied"],
            "hardNegativeCoverageThresholdsSatisfied": coverage["hardNegativeThresholdsSatisfied"],
            "coverageThresholdsSatisfied": coverage["coverageThresholdsSatisfied"],
            "outerOosClosed": True,
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "taxonomyMutated": False,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "promotionPerformed": False,
        },
        "decision": {
            "acceptedHardNegativeCoverageSufficient": passed,
            "taxonomyV5ProposalAuthorized": passed,
            "taxonomyMutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAfterPass"] if passed
            else "Acquire additional independently accepted hard-negative evidence",
        },
        "implementation": {
            "module": "regime_eval.e14_hard_negative_coverage_gate",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output, payload, "E14.4h coverage audit")


def _validate_inputs(
    contract: Any, queue: Any, ingestion: Any, taxonomy: Any, schema: Any,
    label_contract: Any, mechanism_contract: Any, expansion_contract: Any,
    queue_raw: bytes, ingestion_raw: bytes, taxonomy_raw: bytes, schema_raw: bytes,
    label_raw: bytes, mechanism_raw: bytes, expansion_raw: bytes,
) -> None:
    actual = {
        "reviewedQueueV11Sha256": hashlib.sha256(queue_raw).hexdigest(),
        "targetedIngestionAuditV2Sha256": hashlib.sha256(ingestion_raw).hexdigest(),
        "taxonomyV4Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "dossierSchemaSha256": hashlib.sha256(schema_raw).hexdigest(),
        "labelAuditContractSha256": hashlib.sha256(label_raw).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_raw).hexdigest(),
        "expansionContractSha256": hashlib.sha256(expansion_raw).hexdigest(),
    }
    required_policy = {
        "allQueueDossiersMustBeAccepted": True,
        "allManifestHashesMustResolveExactlyOnce": True,
        "taxonomyFoundationDossiersMustRemainUnchanged": True,
        "independentEventsCountByHypothesisId": True,
        "sameMechanismMonthOpposingStatesForbidden": True,
        "crossMechanismMixedStatesAllowed": True,
        "oneNewIndependentEventPerMechanismRequired": True,
        "taxonomyMutationForbiddenInGate": True,
        "candidateGenerationForbiddenInGate": True,
        "outerOosForbiddenInGate": True,
    }
    dossiers = queue.get("dossiers", []) if isinstance(queue, dict) else []
    if (
        contract.get("contractId") != "e14-hard-negative-coverage-gate-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("gatePolicy") != required_policy
        or queue.get("status") != contract.get("requiredQueueStatus")
        or len(dossiers) != contract.get("requiredAcceptedDossierCount")
        or any(not item.get("reviewStatus", "").startswith(ACCEPT_PREFIX) for item in dossiers)
        or len({item.get("dossierId") for item in dossiers}) != len(dossiers)
        or ingestion.get("status") != contract.get("requiredIngestionStatus")
        or ingestion.get("decision", {}).get("hardNegativeCoverageGateAuthorized") is not True
        or ingestion.get("decision", {}).get("taxonomyUpdateAuthorized") is not False
        or ingestion.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or taxonomy.get("groundTruthId") != contract.get("requiredTaxonomyId")
        or taxonomy.get("governance", {}).get("candidateGenerationAuthorized") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
        or label_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or mechanism_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or expansion_contract.get("coverageThresholds") != contract.get("coverageThresholds")
    ):
        raise DatasetValidationError("E14.4h coverage gate inputs or policy are invalid.")


def _load_dossiers(queue: dict[str, Any], directories: Iterable[str | Path]) -> dict[str, dict[str, Any]]:
    roots = [Path(item).resolve() for item in directories]
    if not roots or any(not root.is_dir() for root in roots):
        raise DatasetValidationError("E14.4h dossier directories are invalid.")
    result: dict[str, dict[str, Any]] = {}
    for manifest in queue["dossiers"]:
        matches: list[tuple[Path, bytes]] = []
        for root in roots:
            path = root / manifest["fileName"]
            if path.exists():
                raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() == manifest["sha256"] and len(raw) == manifest["sizeBytes"]:
                    matches.append((path, raw))
        if len(matches) != 1:
            raise DatasetValidationError("E14.4h manifest hash does not resolve exactly once.")
        try:
            dossier = json.loads(matches[0][1])
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise DatasetValidationError("E14.4h dossier JSON is invalid.") from exc
        if dossier.get("dossierId") != manifest["dossierId"] or dossier.get("adjudicationStatus") != "reviewed":
            raise DatasetValidationError("E14.4h dossier identity or status is invalid.")
        result[dossier["dossierId"]] = dossier
    return result


def _coverage(taxonomy: dict[str, Any], new_dossiers: list[dict[str, Any]],
              contract: dict[str, Any]) -> dict[str, Any]:
    required = contract["requiredMechanisms"]
    negative = {mechanism: set() for mechanism in required}
    all_negative: set[str] = set()
    for episode in taxonomy["hardNegativeEpisodes"]:
        event = episode["independentEventId"]
        all_negative.add(event)
        for mechanism in episode["mechanisms"]:
            negative[mechanism].add(event)
    for dossier in new_dossiers:
        event = dossier["hypothesisId"]
        all_negative.add(event)
        negative[dossier["mechanism"]].add(event)
    thresholds = contract["coverageThresholds"]
    positives = {item["mechanism"]: item["combinedPositiveEpisodeCount"]
                 for item in taxonomy["coverage"]["mechanismCoverage"]}
    mechanism_coverage = []
    for mechanism in required:
        mechanism_coverage.append({
            "mechanism": mechanism,
            "combinedPositiveEpisodeCount": positives[mechanism],
            "combinedHardNegativeEpisodeCount": len(negative[mechanism]),
            "positiveThresholdSatisfied": positives[mechanism]
            >= thresholds["minimumFullPositiveEpisodesPerMechanism"],
            "hardNegativeThresholdSatisfied": len(negative[mechanism])
            >= thresholds["minimumHardNegativeEpisodesPerMechanism"],
        })
    positive_ok = (
        taxonomy["coverage"]["combinedPositiveEpisodeCount"] >= thresholds["minimumFullPositiveEpisodes"]
        and all(item["positiveThresholdSatisfied"] for item in mechanism_coverage)
    )
    negative_ok = (
        len(all_negative) >= thresholds["minimumHardNegativeEpisodes"]
        and all(item["hardNegativeThresholdSatisfied"] for item in mechanism_coverage)
    )
    return {
        "combinedPositiveEpisodeCount": taxonomy["coverage"]["combinedPositiveEpisodeCount"],
        "combinedHardNegativeEpisodeCount": len(all_negative),
        "mechanismCoverage": mechanism_coverage,
        "positiveThresholdsSatisfied": positive_ok,
        "hardNegativeThresholdsSatisfied": negative_ok,
        "coverageThresholdsSatisfied": positive_ok and negative_ok,
    }


def _same_mechanism_conflicts(taxonomy: dict[str, Any], dossiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    states: dict[tuple[str, str], set[str]] = defaultdict(set)
    for episode in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]:
        if episode["financialState"] not in {"positive", "hard-negative"}:
            continue
        for month in _months(episode["firstMonth"], episode["lastMonth"]):
            for mechanism in episode["mechanisms"]:
                states[(month, mechanism)].add(episode["financialState"])
    for dossier in dossiers:
        for month in _months(dossier["firstMonth"], dossier["lastMonth"]):
            states[(month, dossier["mechanism"])].add("hard-negative")
    return [
        {"month": key[0], "mechanism": key[1], "states": sorted(values)}
        for key, values in sorted(states.items()) if len(values) > 1
    ]


def _months(first: str, last: str) -> list[str]:
    current, end = date.fromisoformat(first), date.fromisoformat(last)
    result = []
    while current <= end:
        result.append(current.isoformat())
        current = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
    return result


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _write_new_json(path: Path, payload: dict[str, Any], label: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{path}'.") from exc
    return path
