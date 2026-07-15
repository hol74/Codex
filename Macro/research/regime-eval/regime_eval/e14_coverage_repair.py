from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "STRUCTURAL_COVERAGE_REPAIR_PREREGISTERED_MATERIALIZATION_REQUIRED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]


def write_e14_coverage_repair_audit(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    foundation_path: str | Path,
    preregistration_path: str | Path,
    loeo_audit_path: str | Path,
    repair_plan_path: str | Path,
    repair_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_raw, contract = _read(contract_path, "repair contract")
    taxonomy_file, taxonomy_raw, taxonomy = _read(taxonomy_path, "taxonomy v5")
    foundation_file, foundation_raw, foundation = _read(foundation_path, "feature foundation v1")
    prereg_file, prereg_raw, prereg = _read(preregistration_path, "LOEO preregistration")
    loeo_file, loeo_raw, loeo = _read(loeo_audit_path, "LOEO structural audit")
    plan_file, plan_raw, plan = _read(repair_plan_path, "coverage repair plan")
    schema_file, schema_raw, schema = _read(repair_schema_path, "coverage repair schema")
    _validate_inputs(
        contract, taxonomy, foundation, prereg, loeo, plan, schema,
        taxonomy_raw, foundation_raw, prereg_raw, loeo_raw, plan_raw, schema_raw,
    )

    positive = _episodes_by_mechanism(taxonomy["episodes"], "positive")
    negative = _episodes_by_mechanism(taxonomy["hardNegativeEpisodes"], "hard-negative")
    minimum_history = plan["historyPolicy"]["minimumHistoryMonths"]
    projections = []
    for source in sorted(plan["replacementSources"], key=lambda item: item["mechanism"]):
        mechanism = source["mechanism"]
        mature = _add_months(date.fromisoformat(source["projectedCoverageFrom"]), minimum_history)
        coverage_end = date.fromisoformat(source["projectedCoverageTo"])
        observable_positive = _observable_ids(positive[mechanism], mature, coverage_end)
        observable_negative = _observable_ids(negative[mechanism], mature, coverage_end)
        ready = (
            len(observable_positive) >= plan["historyPolicy"]["minimumObservablePositiveEpisodes"]
            and len(observable_negative) >= plan["historyPolicy"]["minimumObservableHardNegativeEpisodes"]
        )
        projections.append({
            "mechanism": mechanism,
            "sourceId": source["sourceId"],
            "seriesId": source["seriesId"],
            "projectedMatureFrom": mature.isoformat(),
            "projectedCoverageTo": coverage_end.isoformat(),
            "observablePositiveEpisodeIds": observable_positive,
            "observablePositiveEpisodeCount": len(observable_positive),
            "observableHardNegativeEpisodeIds": observable_negative,
            "observableHardNegativeEpisodeCount": len(observable_negative),
            "projectedStructurallyReady": ready,
        })
    if not all(item["projectedStructurallyReady"] for item in projections):
        raise DatasetValidationError("E14.6a proposed replacement sources do not repair projected structural coverage.")

    projected_counts = {
        "banking-credit": 4,
        "broad-market-repricing": loeo["inventory"]["eligibleCandidateCountByMechanism"]["broad-market-repricing"],
        "cross-border-growth": 4,
        "funding-liquidity": 4,
    }
    if projected_counts != contract["expectedProjectedEligibleCandidateCounts"]:
        raise DatasetValidationError("E14.6a projected candidate transition differs from the frozen contract.")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14StructuralCoverageRepairAudit",
        "status": STATUS,
        "inputs": {
            "repairContract": _artifact(contract_file, contract_raw),
            "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
            "featureFoundationV1": _artifact(foundation_file, foundation_raw),
            "loeoPreregistration": _artifact(prereg_file, prereg_raw),
            "loeoStructuralAudit": _artifact(loeo_file, loeo_raw),
            "repairPlan": _artifact(plan_file, plan_raw),
            "repairPlanSchema": _artifact(schema_file, schema_raw),
        },
        "decision": {
            "repairPathPreregistered": True,
            "minimumHistoryMonthsPreserved": minimum_history,
            "replacementSourceCount": len(projections),
            "projectedAllMechanismsStructurallyReady": True,
            "projectedEligibleCandidateCount": sum(projected_counts.values()),
            "projectedEligibleCandidateCountByMechanism": projected_counts,
            "sourceMaterializationAuthorized": True,
            "foundationV1MutationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "candidateFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "replacementSourceProjections": projections,
        "governance": {
            "rejectedAlternativeCount": len(plan["rejectedAlternatives"]),
            "nfciSubindexesPrimaryDetectorUse": "diagnostic-only",
            "lowerMinimumHistoryRejected": True,
            "crossMethodologySplicingRejected": True,
            "partialBroadFittingRejected": True,
            "strictVintageReady": False,
            "revisionSensitivityRequiredBeforeFitting": True,
            "methodologyBoundarySensitivityRequiredBeforeFitting": True,
        },
        "protocol": {
            "sourceDownloaded": False,
            "foundationV2Materialized": False,
            "candidateGenerated": False,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "outerFeatureRowCountUsed": 0,
        },
        "implementation": {
            "module": "regime_eval.e14_coverage_repair",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new(output_path, payload)


def _validate_inputs(
    contract: Any, taxonomy: Any, foundation: Any, prereg: Any, loeo: Any,
    plan: Any, schema: Any, taxonomy_raw: bytes, foundation_raw: bytes,
    prereg_raw: bytes, loeo_raw: bytes, plan_raw: bytes, schema_raw: bytes,
) -> None:
    hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "featureFoundationV1Sha256": hashlib.sha256(foundation_raw).hexdigest(),
        "loeoPreregistrationSha256": hashlib.sha256(prereg_raw).hexdigest(),
        "loeoAuditSha256": hashlib.sha256(loeo_raw).hexdigest(),
        "repairPlanSha256": hashlib.sha256(plan_raw).hexdigest(),
        "repairPlanSchemaSha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    auth = {
        "repairDecisionAuditAuthorized": True,
        "sourceMaterializationAuthorizedOnPass": True,
        "foundationV1MutationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "candidateFittingAuthorized": False,
        "candidateEvaluationAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    if (
        contract.get("contractId") != "e14-structural-coverage-repair-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("authorizationPolicy") != auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v1"
        or prereg.get("preregistrationId") != "e14-four-detector-loeo-preregistration-v1"
        or loeo.get("status") != "INNER_LOEO_PREREGISTERED_STRUCTURAL_COVERAGE_BLOCKED"
        or loeo.get("decision", {}).get("candidateFittingAuthorized") is not False
        or plan.get("planId") != "e14-structural-coverage-repair-plan-v1"
        or plan.get("inputHashes") != {key: hashes[key] for key in plan["inputHashes"]}
        or plan.get("decision") != "version-foundation-and-protocol-with-three-standalone-replacement-series"
        or len(plan.get("replacementSources", [])) != 3
        or {item.get("mechanism") for item in plan["replacementSources"]}
        != {"banking-credit", "cross-border-growth", "funding-liquidity"}
        or plan.get("historyPolicy", {}).get("minimumHistoryMonths") != 60
        or plan.get("candidateTransitionPolicy", {}).get("projectedCandidateBudget") != 28
        or plan.get("authorizationPolicy", {}).get("sourceMaterializationAuthorized") is not True
        or any(plan.get("authorizationPolicy", {}).get(key) is not False for key in (
            "foundationV1MutationAuthorized", "candidateGenerationAuthorized",
            "candidateFittingAuthorized", "candidateEvaluationAuthorized",
            "partialBroadFittingAuthorized", "crossMechanismCompositionAuthorized",
            "outerOosAuthorized", "promotionAuthorized",
        ))
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-structural-coverage-repair-plan-v1.json"
    ):
        raise DatasetValidationError("E14.6a coverage-repair inputs or governance are invalid.")


def _episodes_by_mechanism(episodes: list[dict[str, Any]], state: str) -> dict[str, list[dict[str, Any]]]:
    output = {mechanism: [] for mechanism in MECHANISMS}
    for episode in episodes:
        if episode.get("financialState") == state:
            for mechanism in episode.get("mechanisms", []):
                if mechanism in output:
                    output[mechanism].append(episode)
    return output


def _observable_ids(episodes: list[dict[str, Any]], mature: date, coverage_end: date) -> list[str]:
    return sorted({
        item["independentEventId"] for item in episodes
        if max(date.fromisoformat(item["firstMonth"]), mature)
        <= min(date.fromisoformat(item["lastMonth"]), coverage_end)
    })


def _add_months(value: date, months: int) -> date:
    offset = value.year * 12 + value.month - 1 + months
    return date(offset // 12, offset % 12 + 1, 1)


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid E14.6a {label} JSON '{source}'.") from exc


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
        raise DatasetValidationError(f"Immutable E14.6a coverage-repair audit already exists: '{destination}'.") from exc
    return destination
