from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_taxonomy_v4 import _coverage, _duplicates, _episode_key, _same_mechanism_conflicts


TAXONOMY_ID = "us-financial-stress-mechanism-aware-v5"
OUTPUT_STATUS = "TAXONOMY_V5_VERSIONED_CANDIDATE_READINESS_REQUIRED"


def write_e14_taxonomy_v5(
    contract_path: str | Path,
    taxonomy_v4_path: str | Path,
    coverage_gate_audit_path: str | Path,
    reviewed_queue_path: str | Path,
    taxonomy_v4_schema_path: str | Path,
    taxonomy_v5_schema_path: str | Path,
    label_audit_contract_path: str | Path,
    mechanism_contract_path: str | Path,
    taxonomy_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_raw, contract = _read_json(contract_path, "taxonomy v5 contract")
    v4_file, v4_raw, v4 = _read_json(taxonomy_v4_path, "taxonomy v4")
    gate_file, gate_raw, gate = _read_json(coverage_gate_audit_path, "coverage gate audit")
    queue_file, queue_raw, queue = _read_json(reviewed_queue_path, "reviewed queue v11")
    v4_schema_file, v4_schema_raw, v4_schema = _read_json(taxonomy_v4_schema_path, "taxonomy v4 schema")
    v5_schema_file, v5_schema_raw, v5_schema = _read_json(taxonomy_v5_schema_path, "taxonomy v5 schema")
    label_file, label_raw, label_contract = _read_json(label_audit_contract_path, "label contract")
    mechanism_file, mechanism_raw, mechanism_contract = _read_json(
        mechanism_contract_path, "mechanism contract"
    )
    _validate_inputs(
        contract, v4, gate, queue, v4_schema, v5_schema, label_contract,
        mechanism_contract, v4_raw, gate_raw, queue_raw, v4_schema_raw,
        v5_schema_raw, label_raw, mechanism_raw,
    )

    taxonomy_output = Path(taxonomy_output_path).resolve()
    audit_output = Path(audit_output_path).resolve()
    if taxonomy_output.exists() or audit_output.exists():
        raise DatasetValidationError("Immutable E14 taxonomy v5 output already exists.")

    taxonomy = _materialize(v4, gate, queue_raw, gate_raw, contract)
    coverage = _coverage(taxonomy, contract)
    conflicts = _same_mechanism_conflicts(taxonomy)
    duplicate_ids = _duplicates(
        item["id"] for item in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]
    )
    prior_preserved = _prior_episodes_preserved(v4, taxonomy)
    evidence_preserved = taxonomy["foundationEvidence"][: len(v4["foundationEvidence"])] == v4["foundationEvidence"]
    expected_coverage = gate["acceptedCoverageAfterExpansion"]
    if (
        coverage != expected_coverage
        or conflicts or duplicate_ids or not prior_preserved or not evidence_preserved
        or len(taxonomy["foundationEvidence"]) != contract["expectedFinalFoundationEvidenceCount"]
    ):
        raise DatasetValidationError("E14 taxonomy v5 materialization violates the accepted coverage gate.")

    taxonomy_raw = _json_bytes(taxonomy)
    report = {
        "schemaVersion": 1,
        "artifactType": "E14TaxonomyV5MaterializationAudit",
        "status": OUTPUT_STATUS,
        "inputs": {
            "materializationContract": _artifact(contract_file, contract_raw),
            "taxonomyV4": _artifact(v4_file, v4_raw),
            "acceptedCoverageGate": _artifact(gate_file, gate_raw),
            "reviewedQueueV11": _artifact(queue_file, queue_raw),
            "taxonomyV4Schema": _artifact(v4_schema_file, v4_schema_raw),
            "taxonomyV5Schema": _artifact(v5_schema_file, v5_schema_raw),
            "labelAuditContract": _artifact(label_file, label_raw),
            "mechanismContract": _artifact(mechanism_file, mechanism_raw),
        },
        "output": _artifact(taxonomy_output, taxonomy_raw),
        "inventory": {
            "priorEpisodeCount": len(v4["episodes"]),
            "priorHardNegativeEntryCount": len(v4["hardNegativeEpisodes"]),
            "addedHardNegativeEntryCount": contract["expectedAddedDossierCount"],
            "taxonomyEpisodeCount": len(taxonomy["episodes"]),
            "taxonomyHardNegativeEntryCount": len(taxonomy["hardNegativeEpisodes"]),
            "foundationEvidenceCount": len(taxonomy["foundationEvidence"]),
            "independentPositiveEpisodeCount": coverage["combinedPositiveEpisodeCount"],
            "independentHardNegativeEpisodeCount": coverage["combinedHardNegativeEpisodeCount"],
            "sameMechanismMonthConflictCount": len(conflicts),
        },
        "addedFoundationEvidence": copy.deepcopy(gate["newAcceptedHardNegativeEvidence"]),
        "coverage": coverage,
        "checks": {
            "taxonomyV4HashPreserved": hashlib.sha256(v4_file.read_bytes()).hexdigest()
            == contract["inputHashes"]["taxonomyV4Sha256"],
            "coverageGateAuthorizedMaterialization": True,
            "priorEpisodesPreserved": prior_preserved,
            "priorFoundationEvidencePreserved": evidence_preserved,
            "fourAcceptedExpansionEntriesAdded": True,
            "independentEventIdentityExplicit": all(
                item.get("independentEventId")
                for item in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]
            ),
            "episodeIdsUnique": not duplicate_ids,
            "sameMechanismMonthStatesConsistent": not conflicts,
            "crossMechanismMixedStatesPreserved": True,
            "acceptedCoveragePreserved": coverage == expected_coverage,
            "coverageThresholdsSatisfied": coverage["coverageThresholdsSatisfied"],
            "candidateGenerationClosed": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "existingTaxonomyMutated": False,
            "newTaxonomyVersionWritten": True,
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "candidateGenerated": False,
            "promotionPerformed": False,
        },
        "decision": {
            "taxonomyV5Ready": True,
            "positiveCoverageSufficient": coverage["positiveThresholdsSatisfied"],
            "hardNegativeCoverageSufficient": coverage["hardNegativeThresholdsSatisfied"],
            "candidateReadinessGateAuthorized": True,
            "candidateGenerationAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_taxonomy_v5",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    taxonomy_path = _write_new_bytes(taxonomy_output, taxonomy_raw, "E14 taxonomy v5")
    return taxonomy_path, _write_new_json(audit_output, report, "E14 taxonomy v5 audit")


def _validate_inputs(
    contract: Any, v4: Any, gate: Any, queue: Any, v4_schema: Any, v5_schema: Any,
    label_contract: Any, mechanism_contract: Any, v4_raw: bytes, gate_raw: bytes,
    queue_raw: bytes, v4_schema_raw: bytes, v5_schema_raw: bytes, label_raw: bytes,
    mechanism_raw: bytes,
) -> None:
    actual = {
        "taxonomyV4Sha256": hashlib.sha256(v4_raw).hexdigest(),
        "coverageGateAuditSha256": hashlib.sha256(gate_raw).hexdigest(),
        "reviewedQueueV11Sha256": hashlib.sha256(queue_raw).hexdigest(),
        "taxonomyV4SchemaSha256": hashlib.sha256(v4_schema_raw).hexdigest(),
        "taxonomyV5SchemaSha256": hashlib.sha256(v5_schema_raw).hexdigest(),
        "labelAuditContractSha256": hashlib.sha256(label_raw).hexdigest(),
        "mechanismContractSha256": hashlib.sha256(mechanism_raw).hexdigest(),
    }
    policy = {
        "versioningMode": "create-new-file-never-mutate-v4",
        "priorEpisodesPreservedByteStructurally": True,
        "priorFoundationEvidencePreserved": True,
        "oneEntryPerAcceptedExpansionDossier": True,
        "independentEventIdentityFromHypothesisId": True,
        "mechanismMonthStatesRemainIndependent": True,
        "crossMechanismMixedStatesAllowed": True,
        "sameMechanismMonthOpposingStatesForbidden": True,
        "aggregateMonthStateIsViewOnly": True,
        "coverageMustEqualAcceptedCoverageGate": True,
    }
    authorization = {
        "taxonomyV5MaterializationAuthorized": True,
        "taxonomyV4MutationAuthorized": False,
        "candidateReadinessGateAuthorized": True,
        "candidateGenerationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    evidence = gate.get("newAcceptedHardNegativeEvidence", []) if isinstance(gate, dict) else []
    queue_hashes = {item.get("dossierId"): item.get("sha256") for item in queue.get("dossiers", [])}
    if (
        contract.get("contractId") != "e14-taxonomy-v5-materialization-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("materializationPolicy") != policy
        or contract.get("authorizationPolicy") != authorization
        or contract.get("expectedStatus") != OUTPUT_STATUS
        or v4.get("schemaVersion") != 4
        or v4.get("groundTruthId") != contract.get("requiredGroundTruthId")
        or len(v4.get("foundationEvidence", [])) != contract.get("expectedPriorFoundationEvidenceCount")
        or gate.get("status") != contract.get("requiredCoverageGateStatus")
        or gate.get("decision", {}).get("taxonomyV5ProposalAuthorized") is not True
        or gate.get("decision", {}).get("candidateGenerationAuthorized") is not False
        or gate.get("acceptedCoverageAfterExpansion", {}).get("coverageThresholdsSatisfied") is not True
        or len(evidence) != contract.get("expectedAddedDossierCount")
        or len({item.get("dossierId") for item in evidence}) != len(evidence)
        or {item.get("mechanism") for item in evidence} != set(contract.get("requiredMechanisms", []))
        or any(queue_hashes.get(item.get("dossierId")) != item.get("dossierSha256") for item in evidence)
        or any(item.get("state") != "hard-negative" for item in evidence)
        or v4_schema.get("$id") != "https://macro-regime.local/schemas/e14-financial-stress-taxonomy-v4.json"
        or v5_schema.get("$id") != "https://macro-regime.local/schemas/e14-financial-stress-taxonomy-v5.json"
        or v5_schema.get("properties", {}).get("groundTruthId", {}).get("const") != TAXONOMY_ID
        or label_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
        or mechanism_contract.get("requiredMechanisms") != contract.get("requiredMechanisms")
    ):
        raise DatasetValidationError("E14 taxonomy v5 inputs or contract are invalid.")


def _materialize(v4: dict[str, Any], gate: dict[str, Any], queue_raw: bytes,
                 gate_raw: bytes, contract: dict[str, Any]) -> dict[str, Any]:
    evidence = sorted(gate["newAcceptedHardNegativeEvidence"], key=lambda item: item["dossierId"])
    additions = [_episode(item) for item in evidence]
    taxonomy = copy.deepcopy(v4)
    taxonomy.update({
        "schemaVersion": 5,
        "groundTruthId": TAXONOMY_ID,
        "label": "US-relevant mechanism-aware financial stress with accepted hard-negative expansion",
        "derivedFrom": v4["groundTruthId"],
        "acceptedExpansion": {
            "versionedAt": contract["frozenAt"],
            "coverageGateStatus": gate["status"],
            "coverageGateAuditSha256": hashlib.sha256(gate_raw).hexdigest(),
            "sourceQueueSha256": hashlib.sha256(queue_raw).hexdigest(),
            "addedDossierCount": len(evidence),
            "addedDossierIds": [item["dossierId"] for item in evidence],
        },
        "hardNegativeEpisodes": sorted([*v4["hardNegativeEpisodes"], *additions], key=_episode_key),
        "foundationEvidence": [*copy.deepcopy(v4["foundationEvidence"]), *copy.deepcopy(evidence)],
        "coverage": copy.deepcopy(gate["acceptedCoverageAfterExpansion"]),
        "governance": {
            **copy.deepcopy(v4["governance"]),
            "taxonomyV4MutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "outerOosAuthorized": False,
            "additionalHardNegativeResearchRequired": False,
            "candidateReadinessGateRequired": True,
        },
        "limitations": [
            item for item in v4["limitations"]
            if "Hard-negative coverage remains below" not in item
        ] + [
            "Hard-negative coverage meets the frozen threshold only after independent review and E14.4h acceptance.",
            "Coverage sufficiency does not authorize candidate generation; a separate readiness gate is required.",
        ],
    })
    return taxonomy


def _episode(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["dossierId"],
        "name": item["hypothesisId"],
        "firstMonth": item["firstMonth"],
        "lastMonth": item["lastMonth"],
        "financialState": "hard-negative",
        "mechanisms": [item["mechanism"]],
        "sourceIds": [],
        "validationRole": "foundation-v5",
        "independentEventId": item["hypothesisId"],
        "foundationOrigin": "accepted-e14-expansion-dossier",
        "foundationEvidence": {
            "dossierId": item["dossierId"],
            "dossierSha256": item["dossierSha256"],
        },
    }


def _prior_episodes_preserved(v4: dict[str, Any], v5: dict[str, Any]) -> bool:
    actual = {item["id"]: item for item in v5["episodes"] + v5["hardNegativeEpisodes"]}
    return all(actual.get(item["id"]) == item for item in v4["episodes"] + v4["hardNegativeEpisodes"])


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _write_new_bytes(path: Path, content: bytes, label: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable {label} exists: '{path}'.") from exc
    return path


def _write_new_json(path: Path, payload: dict[str, Any], label: str) -> Path:
    return _write_new_bytes(path, _json_bytes(payload), label)
