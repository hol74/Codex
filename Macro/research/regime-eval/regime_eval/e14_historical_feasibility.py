from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


ELIGIBILITIES = {
    "strict-point-in-time",
    "pilot-with-snapshot",
    "pilot-with-release-calendar",
    "diagnostic-only",
    "label-only",
}


def write_e14_historical_feasibility(
    catalog_path: str | Path,
    taxonomy_path: str | Path,
    label_audit_path: str | Path,
    contract_path: str | Path,
    output_path: str | Path,
) -> Path:
    catalog_file, catalog_bytes, catalog = _read_json(catalog_path, "E14 source catalog")
    taxonomy_file, taxonomy_bytes, taxonomy = _read_json(taxonomy_path, "E14 taxonomy")
    label_file, label_bytes, label_audit = _read_json(label_audit_path, "E14 label audit")
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 feasibility contract")
    _validate_contract(catalog_bytes, taxonomy_bytes, label_bytes, label_audit, contract)
    sources, positive_hypotheses, negative_hypotheses = _validate_catalog(catalog, contract)
    existing_positive = _validate_taxonomy(taxonomy, contract)

    requirements = contract["requirements"]
    feature_eligible = set(contract["featureEligibleClasses"])
    mechanism_rows = []
    for mechanism in contract["requiredMechanisms"]:
        feature_sources = [
            item for item in sources
            if item["sourceType"] == "feature"
            and item["eligibility"] in feature_eligible
            and mechanism in item["mechanisms"]
        ]
        label_sources = [
            item for item in sources
            if item["sourceType"] == "label-evidence" and mechanism in item["mechanisms"]
        ]
        current_count = sum(mechanism in item["mechanisms"] for item in existing_positive)
        hypothesis_count = sum(mechanism in item["mechanisms"] for item in positive_hypotheses)
        negative_count = sum(mechanism in item["mechanisms"] for item in negative_hypotheses)
        mechanism_rows.append({
            "mechanism": mechanism,
            "eligibleFeatureSourceIds": [item["id"] for item in feature_sources],
            "labelEvidenceSourceIds": [item["id"] for item in label_sources],
            "existingPositiveEpisodeCount": current_count,
            "positiveHypothesisCount": hypothesis_count,
            "projectedPositiveEpisodeCount": current_count + hypothesis_count,
            "hardNegativeHypothesisCount": negative_count,
            "additionalPositiveHypothesesNeeded": max(
                0, int(requirements["minimumProjectedPositiveEpisodesPerMechanism"])
                - current_count - hypothesis_count,
            ),
            "additionalHardNegativeHypothesesNeeded": max(
                0, int(requirements["minimumHardNegativeHypothesesPerMechanism"]) - negative_count,
            ),
        })

    checks = {
        "inputIntegrity": True,
        "noOuterOosRead": True,
        "hypothesesRemainUnlabeled": all(
            item["curationStatus"] == "hypothesis-only"
            for item in [*positive_hypotheses, *negative_hypotheses]
        ),
        "compositeIndexesDiagnosticOnly": all(
            item["eligibility"] == "diagnostic-only"
            for item in sources if item["asOfClass"] == "reconstructed-current-history"
        ),
        "pre2008ExtensionCandidates": all(
            date.fromisoformat(item["firstMonth"])
            < date.fromisoformat(requirements["extensionCutoff"])
            for item in [*positive_hypotheses, *negative_hypotheses]
        ),
        "minimumFeatureSourcesPerMechanism": all(
            len(item["eligibleFeatureSourceIds"])
            >= int(requirements["minimumFeatureSourcesPerMechanism"])
            for item in mechanism_rows
        ),
        "minimumLabelSourcesPerMechanism": all(
            len(item["labelEvidenceSourceIds"])
            >= int(requirements["minimumLabelSourcesPerMechanism"])
            for item in mechanism_rows
        ),
        "minimumProjectedPositiveEpisodesPerMechanism": all(
            item["projectedPositiveEpisodeCount"]
            >= int(requirements["minimumProjectedPositiveEpisodesPerMechanism"])
            for item in mechanism_rows
        ),
        "minimumHardNegativeHypothesesPerMechanism": all(
            item["hardNegativeHypothesisCount"]
            >= int(requirements["minimumHardNegativeHypothesesPerMechanism"])
            for item in mechanism_rows
        ),
    }
    full_ready = all(checks.values())
    curation_checks = [
        "inputIntegrity",
        "noOuterOosRead",
        "hypothesesRemainUnlabeled",
        "compositeIndexesDiagnosticOnly",
        "pre2008ExtensionCandidates",
        "minimumFeatureSourcesPerMechanism",
        "minimumLabelSourcesPerMechanism",
        "minimumProjectedPositiveEpisodesPerMechanism",
    ]
    curation_ready = all(checks[key] for key in curation_checks)
    decisions = contract["decisions"]
    status = (
        decisions["fullPassing"] if full_ready
        else decisions["curationOnly"] if curation_ready
        else decisions["failing"]
    )

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14HistoricalFoundationFeasibility",
        "status": status,
        "inputs": {
            "sourceCatalog": _artifact(catalog_file, catalog_bytes),
            "taxonomyV3": _artifact(taxonomy_file, taxonomy_bytes),
            "labelAudit": _artifact(label_file, label_bytes),
            "contract": _artifact(contract_file, contract_bytes),
        },
        "protocol": {
            "purpose": "historical-source-and-label-feasibility-only",
            "datasetRead": False,
            "outerFeatureRowCountUsed": 0,
            "labelsWritten": 0,
            "candidateGenerated": False,
            "rankingProduced": False,
            "promotionAuthorized": False,
        },
        "inventory": {
            "sourceCount": len(sources),
            "sourceCountByEligibility": {
                value: sum(item["eligibility"] == value for item in sources)
                for value in sorted(ELIGIBILITIES)
            },
            "positiveHypothesisCount": len(positive_hypotheses),
            "hardNegativeHypothesisCount": len(negative_hypotheses),
        },
        "mechanismFeasibility": mechanism_rows,
        "checks": checks,
        "failedChecks": sorted(key for key, value in checks.items() if not value),
        "decision": {
            "status": status,
            "episodeDossierCurationAuthorized": curation_ready,
            "fullCorpusPopulationAuthorized": full_ready,
            "candidateGenerationAuthorized": False,
            "nextAllowedAction": (
                "E14.4 mechanism-specific detector and evidence contract"
                if curation_ready else "repair E14.3 source catalog"
            ),
        },
        "implementation": {
            "module": "regime_eval.e14_historical_feasibility",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _validate_contract(
    catalog_bytes: bytes,
    taxonomy_bytes: bytes,
    label_bytes: bytes,
    label_audit: Any,
    contract: Any,
) -> None:
    actual = {
        "sourceCatalogSha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "taxonomyV3Sha256": hashlib.sha256(taxonomy_bytes).hexdigest(),
        "labelAuditSha256": hashlib.sha256(label_bytes).hexdigest(),
    }
    policies = contract.get("policies", {}) if isinstance(contract, dict) else {}
    if (
        not isinstance(contract, dict)
        or contract.get("contractId") != "e14-historical-feasibility-contract-v1"
        or contract.get("inputHashes") != actual
        or set(contract.get("featureEligibleClasses", []))
        != {"strict-point-in-time", "pilot-with-snapshot", "pilot-with-release-calendar"}
        or "diagnostic-only" not in str(policies.get("compositeIndexPolicy"))
        or "affirmative" not in str(policies.get("hardNegativePolicy"))
        or "No outer" not in str(policies.get("outerOosPolicy"))
        or contract.get("candidateGenerationAuthorized") is not False
    ):
        raise DatasetValidationError("E14 historical feasibility contract is invalid.")
    if (
        label_audit.get("artifactType") != "E14TriStateLabelAudit"
        or label_audit.get("protocol", {}).get("outerFeatureRowCountUsed") != 0
        or label_audit.get("decision", {}).get("candidateGenerationAuthorized") is not False
    ):
        raise DatasetValidationError("E14 label audit input is invalid.")


def _validate_catalog(
    catalog: Any, contract: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if (
        not isinstance(catalog, dict)
        or catalog.get("catalogId") != "e14-historical-source-catalog-v1"
        or catalog.get("schemaVersion") != 1
    ):
        raise DatasetValidationError("E14 historical source catalog is invalid.")
    sources = catalog.get("sources")
    positives = catalog.get("positiveEpisodeHypotheses")
    negatives = catalog.get("hardNegativeHypotheses")
    if not isinstance(sources, list) or not isinstance(positives, list) or not isinstance(negatives, list):
        raise DatasetValidationError("E14 historical source catalog collections are invalid.")
    required = set(contract["requiredMechanisms"])
    source_ids: set[str] = set()
    for source in sources:
        source_id = source.get("id")
        if (
            not isinstance(source_id, str) or source_id in source_ids
            or not str(source.get("url", "")).startswith("https://")
            or source.get("eligibility") not in ELIGIBILITIES
            or not set(source.get("mechanisms", [])) <= required
            or source.get("sourceType") not in {
                "feature", "feature-infrastructure", "diagnostic-index", "label-evidence"
            }
            or date.fromisoformat(source["coverageFrom"]) > date.fromisoformat(source.get("coverageTo", "9999-12-31"))
        ):
            raise DatasetValidationError("E14 historical source entry is invalid.")
        if source["asOfClass"] == "reconstructed-current-history" and source["eligibility"] != "diagnostic-only":
            raise DatasetValidationError("Reconstructed E14 history must remain diagnostic-only.")
        source_ids.add(source_id)

    episode_ids: set[str] = set()
    for episode in [*positives, *negatives]:
        episode_id = episode.get("id")
        if (
            not isinstance(episode_id, str) or episode_id in episode_ids
            or episode.get("curationStatus") != "hypothesis-only"
            or not episode.get("mechanisms")
            or not set(episode["mechanisms"]) <= required
            or not set(episode.get("sourceIds", [])) <= source_ids
            or date.fromisoformat(episode["firstMonth"]) > date.fromisoformat(episode["lastMonth"])
        ):
            raise DatasetValidationError("E14 historical episode hypothesis is invalid.")
        episode_ids.add(episode_id)
    return sources, positives, negatives


def _validate_taxonomy(taxonomy: Any, contract: dict[str, Any]) -> list[dict[str, Any]]:
    if (
        not isinstance(taxonomy, dict)
        or taxonomy.get("groundTruthId") != "us-financial-stress-tristate-v3"
        or set(taxonomy.get("mechanisms", {})) != set(contract["requiredMechanisms"])
    ):
        raise DatasetValidationError("E14 taxonomy is incompatible with historical feasibility.")
    return [item for item in taxonomy.get("episodes", []) if item.get("financialState") == "positive"]


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
        raise DatasetValidationError(f"Immutable E14 feasibility report exists: '{destination}'.") from exc
    return destination
