from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "INDEPENDENT_REVIEW_REQUIRED"
ACCEPTED_STATUSES = {
    "accept-by-independent-receipt",
    "accept-by-targeted-independent-receipt",
}


def write_e14_hard_negative_expansion(
    contract_path: str | Path,
    pack_path: str | Path,
    taxonomy_path: str | Path,
    materialization_audit_path: str | Path,
    reviewed_queue_path: str | Path,
    dossier_schema_path: str | Path,
    review_schema_path: str | Path,
    label_audit_contract_path: str | Path,
    mechanism_contract_path: str | Path,
    dossier_output_dir: str | Path,
    queue_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14.4e expansion contract")
    pack_file, pack_bytes, pack = _read_json(pack_path, "E14.4e expansion pack")
    taxonomy_file, taxonomy_bytes, taxonomy = _read_json(taxonomy_path, "E14 taxonomy v4")
    upstream_file, upstream_bytes, upstream = _read_json(
        materialization_audit_path, "E14 taxonomy materialization audit"
    )
    base_queue_file, base_queue_bytes, base_queue = _read_json(
        reviewed_queue_path, "E14 reviewed queue v5"
    )
    dossier_schema_file, dossier_schema_bytes, dossier_schema = _read_json(
        dossier_schema_path, "E14 dossier schema"
    )
    review_schema_file, review_schema_bytes, review_schema = _read_json(
        review_schema_path, "E14 review schema v2"
    )
    label_contract_file, label_contract_bytes, label_contract = _read_json(
        label_audit_contract_path, "E14 label audit contract"
    )
    mechanism_file, mechanism_bytes, mechanism_contract = _read_json(
        mechanism_contract_path, "E14 mechanism contract"
    )
    _validate_inputs(
        contract,
        pack,
        taxonomy,
        upstream,
        base_queue,
        dossier_schema,
        review_schema,
        label_contract,
        mechanism_contract,
        pack_bytes,
        taxonomy_bytes,
        upstream_bytes,
        base_queue_bytes,
        dossier_schema_bytes,
        review_schema_bytes,
        label_contract_bytes,
        mechanism_bytes,
    )
    assertions = _assertions(pack)
    dossiers = _build_dossiers(pack, assertions, contract)
    conflicts = _same_mechanism_conflicts(taxonomy, dossiers)
    if conflicts:
        raise DatasetValidationError("E14.4e expansion creates a same-mechanism month conflict.")
    potential_coverage = _potential_coverage(taxonomy, dossiers, contract)
    expected = contract["expectedPotentialCoverage"]
    if (
        potential_coverage["combinedHardNegativeEpisodeCount"]
        != expected["independentHardNegativeEpisodeCount"]
        or any(
            item["combinedHardNegativeEpisodeCount"]
            != expected["hardNegativeEpisodesPerMechanism"]
            for item in potential_coverage["mechanismCoverage"]
        )
        or not potential_coverage["coverageThresholdsSatisfied"]
    ):
        raise DatasetValidationError("E14.4e potential coverage does not meet the frozen target.")

    dossier_dir = Path(dossier_output_dir).resolve()
    dossier_paths = [dossier_dir / f"{item['dossierId']}.json" for item in dossiers]
    queue_output = Path(queue_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    if queue_output.exists() or audit_output.exists() or any(path.exists() for path in dossier_paths):
        raise DatasetValidationError("Immutable E14.4e hard-negative expansion output already exists.")

    dossier_raw = [_json_bytes(item) for item in dossiers]
    artifacts = [_artifact(path, raw) for path, raw in zip(dossier_paths, dossier_raw, strict=True)]
    queue = {
        "schemaVersion": 1,
        "artifactType": "E14HardNegativeExpansionReviewQueue",
        "status": "EXPANSION_AWAITING_INDEPENDENT_REVIEW",
        "reviewSchema": _artifact(review_schema_file, review_schema_bytes),
        "baseQueue": _artifact(base_queue_file, base_queue_bytes),
        "dossierAuthor": pack["reviewer"],
        "requirements": pack["independencePolicy"],
        "preservedAcceptedDossierCount": len(base_queue["dossiers"]),
        "newDossierCount": len(dossiers),
        "expansionDossierIds": sorted(item["dossierId"] for item in dossiers),
        "dossiers": [
            *base_queue["dossiers"],
            *[
                {**artifact, "reviewStatus": "awaiting-expansion-independent-review"}
                for artifact in artifacts
            ],
        ],
    }
    queue_raw = _json_bytes(queue)
    report = {
        "schemaVersion": 1,
        "artifactType": "E14HardNegativeExpansionCurationAudit",
        "status": STATUS,
        "inputs": {
            "expansionContract": _artifact(contract_file, contract_bytes),
            "expansionPack": _artifact(pack_file, pack_bytes),
            "taxonomyV4": _artifact(taxonomy_file, taxonomy_bytes),
            "taxonomyMaterializationAudit": _artifact(upstream_file, upstream_bytes),
            "reviewedQueueV5": _artifact(base_queue_file, base_queue_bytes),
            "dossierSchema": _artifact(dossier_schema_file, dossier_schema_bytes),
            "reviewSchemaV2": _artifact(review_schema_file, review_schema_bytes),
            "labelAuditContract": _artifact(label_contract_file, label_contract_bytes),
            "mechanismContract": _artifact(mechanism_file, mechanism_bytes),
            "reviewQueueV6": _artifact(queue_output, queue_raw),
        },
        "inventory": {
            "preservedAcceptedDossierCount": len(base_queue["dossiers"]),
            "newReviewedDossierCount": len(dossiers),
            "newIndependentEventCount": len({item["hypothesisId"] for item in dossiers}),
            "queuedDossierCount": len(queue["dossiers"]),
            "newIndependentReviewReceiptCount": 0,
            "sameMechanismMonthConflictCount": len(conflicts),
        },
        "newDossierArtifacts": artifacts,
        "currentCoverage": taxonomy["coverage"],
        "potentialCoverageIfAllAccepted": potential_coverage,
        "checks": {
            "priorTwelveAcceptedManifestsPreserved": queue["dossiers"][:12] == base_queue["dossiers"],
            "fourDistinctIndependentEvents": len({item["hypothesisId"] for item in dossiers}) == 4,
            "oneNewDossierPerMechanism": {
                item["mechanism"] for item in dossiers
            } == set(contract["requiredMechanisms"]),
            "twoIndependentEvidenceProvidersPerDossier": True,
            "affirmativeOrderlyEvidencePerDossier": True,
            "counterEvidencePerDossier": True,
            "sameMechanismMonthStatesConsistent": not conflicts,
            "crossMechanismMixedStatesPreserved": True,
            "potentialCoverageThresholdsSatisfied": potential_coverage["coverageThresholdsSatisfied"],
            "selfAcceptancePrevented": True,
            "taxonomyV4Unchanged": hashlib.sha256(taxonomy_file.read_bytes()).hexdigest()
            == contract["inputHashes"]["taxonomyV4Sha256"],
            "outerOosClosed": True,
        },
        "protocol": {
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "taxonomyMutated": False,
            "labelsAccepted": 0,
            "candidateGenerated": False,
            "promotionPerformed": False,
            "remoteByteSnapshotsArchived": False,
        },
        "limitations": pack["limitations"],
        "decision": {
            "potentialCoverageSufficientIfAllAccepted": True,
            "independentReviewComplete": False,
            "taxonomyUpdateAuthorized": False,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_hard_negative_expansion",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    for path, raw in zip(dossier_paths, dossier_raw, strict=True):
        _write_new_bytes(path, raw, "E14.4e hard-negative dossier")
    queue_written = _write_new_bytes(queue_output, queue_raw, "E14.4e review queue")
    return queue_written, _write_new_json(audit_output, report, "E14.4e curation audit")


def _validate_inputs(
    contract: Any,
    pack: Any,
    taxonomy: Any,
    upstream: Any,
    base_queue: Any,
    dossier_schema: Any,
    review_schema: Any,
    label_contract: Any,
    mechanism_contract: Any,
    pack_bytes: bytes,
    taxonomy_bytes: bytes,
    upstream_bytes: bytes,
    base_queue_bytes: bytes,
    dossier_schema_bytes: bytes,
    review_schema_bytes: bytes,
    label_contract_bytes: bytes,
    mechanism_bytes: bytes,
) -> None:
    actual_hashes = {
        "expansionPackSha256": hashlib.sha256(pack_bytes).hexdigest(),
        "taxonomyV4Sha256": hashlib.sha256(taxonomy_bytes).hexdigest(),
        "taxonomyMaterializationAuditSha256": hashlib.sha256(upstream_bytes).hexdigest(),
        "reviewedQueueV5Sha256": hashlib.sha256(base_queue_bytes).hexdigest(),
        "dossierSchemaSha256": hashlib.sha256(dossier_schema_bytes).hexdigest(),
        "reviewSchemaV2Sha256": hashlib.sha256(review_schema_bytes).hexdigest(),
        "labelAuditContractSha256": hashlib.sha256(label_contract_bytes).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_bytes).hexdigest(),
    }
    required_curation = {
        "oneNewIndependentEventPerMechanism": True,
        "sameMechanismMonthOpposingStatesForbidden": True,
        "crossMechanismMixedStatesAllowed": True,
        "affirmativeOrderlyEvidenceRequired": True,
        "twoIndependentEvidenceProvidersRequired": True,
        "counterEvidenceRequired": True,
        "priorAcceptedHashesMustRemainUnchanged": True,
        "newDossiersRemainReviewedUntilReceipt": True,
        "selfAcceptanceForbidden": True,
    }
    required_authorization = {
        "dossierCurationAuthorized": True,
        "reviewQueueWriteAuthorized": True,
        "taxonomyMutationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    statuses = [item.get("reviewStatus") for item in base_queue.get("dossiers", [])]
    if (
        contract.get("contractId") != "e14-hard-negative-expansion-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("curationPolicy") != required_curation
        or contract.get("authorizationPolicy") != required_authorization
        or contract.get("expectedStatus") != STATUS
        or contract.get("expectedPreservedAcceptedDossierCount") != 12
        or contract.get("expectedNewDossierCount") != 4
        or pack.get("packId") != "e14-hard-negative-expansion-pack-v1"
        or pack.get("reviewer") != "codex-primary-source-review-2026-07-15"
        or pack.get("independencePolicy", {}).get("selfAcceptanceForbidden") is not True
        or pack.get("independencePolicy", {}).get("minimumTotalReviewersAfterReceipt") != 2
        or taxonomy.get("groundTruthId") != contract.get("requiredTaxonomyId")
        or taxonomy.get("governance", {}).get("candidateGenerationAuthorized") is not False
        or upstream.get("status") != contract.get("requiredUpstreamStatus")
        or upstream.get("decision", {}).get("taxonomyV4Ready") is not True
        or upstream.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or base_queue.get("status") != "REVIEW_COMPLETE_ALL_ACCEPTED"
        or len(statuses) != 12
        or any(status not in ACCEPTED_STATUSES for status in statuses)
        or dossier_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-episode-dossier-v1.json"
        or review_schema.get("$id")
        != "https://macro-regime.local/schemas/e14-independent-review-v2.json"
        or label_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or mechanism_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or any(
            label_contract.get("requirements", {}).get(key) != value
            for key, value in contract.get("coverageThresholds", {}).items()
        )
    ):
        raise DatasetValidationError("E14.4e hard-negative expansion inputs or contract are invalid.")


def _assertions(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in pack.get("evidenceAssertions", []):
        try:
            date.fromisoformat(item["publishedAt"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError("E14.4e evidence date is invalid.") from exc
        if (
            item.get("id") in result
            or item.get("role") not in {"official-narrative", "quantitative-observation", "counterevidence"}
            or not str(item.get("locator", "")).startswith("https://")
            or len(item.get("summary", "")) < 40
        ):
            raise DatasetValidationError("E14.4e evidence assertion is invalid.")
        result[item["id"]] = item
    if len(result) < 12:
        raise DatasetValidationError("E14.4e evidence inventory is incomplete.")
    return result


def _build_dossiers(
    pack: dict[str, Any], assertions: dict[str, dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    blueprints = pack.get("hardNegativeBlueprints", [])
    if (
        len(blueprints) != contract["expectedNewDossierCount"]
        or {item.get("mechanism") for item in blueprints} != set(contract["requiredMechanisms"])
        or len({item.get("hypothesisId") for item in blueprints}) != len(blueprints)
        or len({item.get("dossierId") for item in blueprints}) != len(blueprints)
    ):
        raise DatasetValidationError("E14.4e blueprints do not provide four independent mechanisms.")
    dossiers = []
    for blueprint in blueprints:
        evidence_ids = blueprint.get("evidenceIds", [])
        counter_ids = blueprint.get("counterEvidenceIds", [])
        if (
            blueprint.get("proposedState") != "hard-negative"
            or not str(blueprint.get("dossierId", "")).startswith("e14-dossier-")
            or len(evidence_ids) < 2
            or not counter_ids
            or any(item not in assertions for item in evidence_ids + counter_ids)
            or len(blueprint.get("boundaryRationale", "")) < 80
        ):
            raise DatasetValidationError("E14.4e hard-negative blueprint is invalid.")
        first = date.fromisoformat(blueprint["firstMonth"])
        last = date.fromisoformat(blueprint["lastMonth"])
        evidence = [assertions[item] for item in evidence_ids]
        counters = [assertions[item] for item in counter_ids]
        if (
            first.day != 1
            or last.day != 1
            or first > last
            or len({item["independenceGroup"] for item in evidence}) < 2
            or not {"official-narrative", "quantitative-observation"}
            <= {item["role"] for item in evidence}
            or any(item["role"] != "counterevidence" for item in counters)
        ):
            raise DatasetValidationError("E14.4e evidence or boundary requirements are not met.")
        dossiers.append({
            "schemaVersion": 1,
            "dossierId": blueprint["dossierId"],
            "hypothesisId": blueprint["hypothesisId"],
            "mechanism": blueprint["mechanism"],
            "proposedState": "hard-negative",
            "firstMonth": blueprint["firstMonth"],
            "lastMonth": blueprint["lastMonth"],
            "boundaryRationale": blueprint["boundaryRationale"],
            "affirmativeOrderlyEvidence": True,
            "evidenceItems": [_evidence_payload(item) for item in evidence],
            "counterEvidence": [_evidence_payload(item) for item in counters],
            "exclusionChecks": {
                "outerOosUsed": False,
                "modelPredictionUsedAsLabel": False,
                "absenceTreatedAsEvidence": False,
                "methodologyRegimeRecorded": True,
                "nberOverlapReviewed": True,
            },
            "adjudicationStatus": "reviewed",
            "reviewers": [pack["reviewer"]],
        })
    return sorted(dossiers, key=lambda item: item["dossierId"])


def _same_mechanism_conflicts(
    taxonomy: dict[str, Any], dossiers: list[dict[str, Any]]
) -> list[dict[str, Any]]:
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
        for key, values in sorted(states.items())
        if len(values) > 1
    ]


def _potential_coverage(
    taxonomy: dict[str, Any], dossiers: list[dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any]:
    required = contract["requiredMechanisms"]
    negative = {mechanism: set() for mechanism in required}
    all_negative: set[str] = set()
    for episode in taxonomy["hardNegativeEpisodes"]:
        event_id = episode["independentEventId"]
        all_negative.add(event_id)
        for mechanism in episode["mechanisms"]:
            negative[mechanism].add(event_id)
    for dossier in dossiers:
        all_negative.add(dossier["hypothesisId"])
        negative[dossier["mechanism"]].add(dossier["hypothesisId"])
    thresholds = contract["coverageThresholds"]
    mechanism_coverage = []
    current_positive = {
        item["mechanism"]: item["combinedPositiveEpisodeCount"]
        for item in taxonomy["coverage"]["mechanismCoverage"]
    }
    for mechanism in required:
        mechanism_coverage.append({
            "mechanism": mechanism,
            "combinedPositiveEpisodeCount": current_positive[mechanism],
            "combinedHardNegativeEpisodeCount": len(negative[mechanism]),
            "positiveThresholdSatisfied": current_positive[mechanism]
            >= thresholds["minimumFullPositiveEpisodesPerMechanism"],
            "hardNegativeThresholdSatisfied": len(negative[mechanism])
            >= thresholds["minimumHardNegativeEpisodesPerMechanism"],
        })
    positive_ok = taxonomy["coverage"]["positiveThresholdsSatisfied"]
    negative_ok = len(all_negative) >= thresholds["minimumHardNegativeEpisodes"] and all(
        item["hardNegativeThresholdSatisfied"] for item in mechanism_coverage
    )
    return {
        "combinedPositiveEpisodeCount": taxonomy["coverage"]["combinedPositiveEpisodeCount"],
        "combinedHardNegativeEpisodeCount": len(all_negative),
        "mechanismCoverage": mechanism_coverage,
        "positiveThresholdsSatisfied": positive_ok,
        "hardNegativeThresholdsSatisfied": negative_ok,
        "coverageThresholdsSatisfied": positive_ok and negative_ok,
    }


def _months(first: str, last: str) -> list[str]:
    start, end = date.fromisoformat(first), date.fromisoformat(last)
    values = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
    return values


def _evidence_payload(assertion: dict[str, Any]) -> dict[str, Any]:
    payload = {
        key: assertion[key]
        for key in (
            "sourceId", "provider", "independenceGroup", "publishedAt", "role", "locator", "summary"
        )
    }
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
    result = {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}
    try:
        content = json.loads(raw)
        if isinstance(content, dict) and "dossierId" in content:
            result["dossierId"] = content["dossierId"]
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return result


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_new_bytes(path: Path, payload: bytes, label: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{path}'.") from exc
    return path


def _write_new_json(path: Path, payload: dict[str, Any], label: str) -> Path:
    return _write_new_bytes(path, _json_bytes(payload), label)
