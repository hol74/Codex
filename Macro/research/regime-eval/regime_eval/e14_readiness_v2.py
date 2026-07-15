from __future__ import annotations

import calendar
import hashlib
import itertools
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "FOUR_DETECTOR_READINESS_V2_PASSED_PROTOCOL_V2_DESIGN_AUTHORIZED_FITTING_CLOSED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]
NEW_PROFILES = {
    "banking-credit": {
        "profileId": "fdic-failed-assisted-assets-only",
        "seriesIds": ["e14-fdic-failed-assisted-assets-monthly"],
        "aggregator": "identity",
    },
    "cross-border-growth": {
        "profileId": "twexbmth-absolute-change-only",
        "seriesIds": ["e14-twexbmth-monthly-absolute-change"],
        "aggregator": "identity",
    },
    "funding-liquidity": {
        "profileId": "fedfunds-minus-tbill-only",
        "seriesIds": ["e14-fedfunds-minus-tbill-monthly"],
        "aggregator": "identity",
    },
}


def write_e14_readiness_v2(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    foundation_v2_path: str | Path,
    foundation_lock_v2_path: str | Path,
    foundation_audit_v2_path: str | Path,
    candidate_manifest_v1_path: str | Path,
    repair_plan_path: str | Path,
    readiness_policy_path: str | Path,
    readiness_policy_schema_path: str | Path,
    roster_schema_path: str | Path,
    roster_output_path: str | Path,
    audit_output_path: str | Path,
) -> tuple[Path, Path]:
    contract_file, contract_raw, contract = _read(contract_path, "readiness contract v2")
    taxonomy_file, taxonomy_raw, taxonomy = _read(taxonomy_path, "taxonomy v5")
    foundation_file, foundation_raw, foundation = _read(foundation_v2_path, "foundation v2")
    lock_file, lock_raw, lock = _read(foundation_lock_v2_path, "foundation lock v2")
    foundation_audit_file, foundation_audit_raw, foundation_audit = _read(
        foundation_audit_v2_path, "foundation audit v2"
    )
    manifest_file, manifest_raw, manifest = _read(candidate_manifest_v1_path, "candidate manifest v1")
    plan_file, plan_raw, plan = _read(repair_plan_path, "coverage repair plan")
    policy_file, policy_raw, policy = _read(readiness_policy_path, "readiness policy v2")
    policy_schema_file, policy_schema_raw, policy_schema = _read(
        readiness_policy_schema_path, "readiness policy schema v2"
    )
    roster_schema_file, roster_schema_raw, roster_schema = _read(
        roster_schema_path, "readiness roster schema v2"
    )
    _validate_inputs(
        contract, taxonomy, foundation, lock, foundation_audit, manifest,
        plan, policy, policy_schema, roster_schema, taxonomy_raw,
        foundation_raw, lock_raw, foundation_audit_raw, manifest_raw,
        plan_raw, policy_raw, policy_schema_raw, roster_schema_raw,
    )

    outputs = [Path(roster_output_path).resolve(), Path(audit_output_path).resolve()]
    if any(path.exists() for path in outputs):
        raise DatasetValidationError("Immutable E14 readiness-v2 output already exists.")

    series = {item["seriesId"]: item for item in foundation["series"]}
    availability = {
        series_id: _availability_descriptor(item, policy["eligibilityPolicy"]["minimumHistoryObservations"])
        for series_id, item in series.items()
    }
    bindings = {
        (item["mechanism"], item["seriesId"]): item
        for item in foundation["detectorBindings"]
    }

    candidates: list[dict[str, Any]] = []
    broad_v1 = [
        item for item in manifest["candidates"]
        if item["mechanism"] == "broad-market-repricing"
    ]
    for item in broad_v1:
        eligibility = _eligibility(
            taxonomy, item["mechanism"], item["profile"]["seriesIds"],
            series, availability, policy["eligibilityPolicy"],
        )
        candidates.append({
            "candidateId": item["candidateId"],
            "mechanism": item["mechanism"],
            "detectorId": item["detectorId"],
            "profile": item["profile"],
            "featureBindings": item["featureBindings"],
            "persistence": {
                "entryPersistenceMonths": item["parameters"]["entryPersistenceMonths"],
                "recoveryPersistenceMonths": item["parameters"]["recoveryPersistenceMonths"],
                "hysteresisRequired": item["parameters"]["hysteresisRequired"],
            },
            "identityPolicy": "preserved-exactly-from-candidate-manifest-v1",
            "lifecycleStatus": "readiness-planned-not-generated-not-fit",
            "eligibility": eligibility,
        })

    for mechanism in sorted(NEW_PROFILES):
        profile = NEW_PROFILES[mechanism]
        binding = bindings[(mechanism, profile["seriesIds"][0])]
        feature_bindings = [{
            "seriesId": binding["seriesId"],
            "sourceId": binding["sourceId"],
            "transform": binding["transform"],
            "fitScope": binding["fitScope"],
        }]
        eligibility = _eligibility(
            taxonomy, mechanism, profile["seriesIds"], series, availability,
            policy["eligibilityPolicy"],
        )
        for entry, recovery in itertools.product((1, 2), (1, 2)):
            identity = {
                "rosterId": "e14-four-detector-readiness-roster-v2",
                "mechanism": mechanism,
                "detectorId": binding["detectorId"],
                "profile": profile,
                "featureBindings": feature_bindings,
                "entryPersistenceMonths": entry,
                "recoveryPersistenceMonths": recovery,
                "hysteresisRequired": True,
            }
            suffix = hashlib.sha256(_canonical_bytes(identity)).hexdigest()[:12]
            candidates.append({
                "candidateId": f"e14-{_slug(mechanism)}-v2-{suffix}",
                "mechanism": mechanism,
                "detectorId": binding["detectorId"],
                "profile": profile,
                "featureBindings": feature_bindings,
                "persistence": {
                    "entryPersistenceMonths": entry,
                    "recoveryPersistenceMonths": recovery,
                    "hysteresisRequired": True,
                },
                "identityPolicy": "new-v2-readiness-namespace-not-yet-generated",
                "lifecycleStatus": "readiness-planned-not-generated-not-fit",
                "eligibility": eligibility,
            })

    retired = [
        item["candidateId"] for item in manifest["candidates"]
        if item["mechanism"] != "broad-market-repricing"
    ]
    counts = {mechanism: 0 for mechanism in MECHANISMS}
    counts.update(Counter(item["mechanism"] for item in candidates))
    eligible_counts = {mechanism: 0 for mechanism in MECHANISMS}
    eligible_counts.update(Counter(
        item["mechanism"] for item in candidates if item["eligibility"]["structurallyEligible"]
    ))
    ids = [item["candidateId"] for item in candidates]
    preserved_ids = [item["candidateId"] for item in broad_v1]
    new_ids = [item for item in ids if item not in preserved_ids]
    if (
        counts != contract["expectedCandidateCounts"]
        or eligible_counts != contract["expectedEligibleCandidateCounts"]
        or len(ids) != len(set(ids))
        or len(preserved_ids) != contract["transitionPolicy"]["preservedV1CandidateIdCount"]
        or len(retired) != contract["transitionPolicy"]["retiredV1CandidateIdCount"]
        or len(new_ids) != contract["transitionPolicy"]["newV2CandidateIdCount"]
        or any("-v2-" not in item for item in new_ids)
        or set(ids) & set(retired)
    ):
        raise DatasetValidationError("E14 readiness-v2 candidate transition is invalid.")

    episode_coverage = {}
    for mechanism in MECHANISMS:
        values = [item["eligibility"] for item in candidates if item["mechanism"] == mechanism]
        positive_counts = {item["observablePositiveEpisodeCount"] for item in values}
        negative_counts = {item["observableHardNegativeEpisodeCount"] for item in values}
        if len(positive_counts) != 1 or len(negative_counts) != 1:
            raise DatasetValidationError("E14 readiness-v2 profiles disagree on mechanism coverage.")
        episode_coverage[mechanism] = {
            "positive": next(iter(positive_counts)),
            "hardNegative": next(iter(negative_counts)),
        }
    if episode_coverage != contract["expectedEpisodeCoverage"]:
        raise DatasetValidationError("E14 readiness-v2 episode coverage differs from contract.")

    input_artifacts = {
        "readinessContractV2": _artifact(contract_file, contract_raw),
        "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
        "featureFoundationV2": _artifact(foundation_file, foundation_raw),
        "featureFoundationLockV2": _artifact(lock_file, lock_raw),
        "featureFoundationAuditV2": _artifact(foundation_audit_file, foundation_audit_raw),
        "candidateManifestV1": _artifact(manifest_file, manifest_raw),
        "coverageRepairPlan": _artifact(plan_file, plan_raw),
        "readinessPolicyV2": _artifact(policy_file, policy_raw),
        "readinessPolicySchemaV2": _artifact(policy_schema_file, policy_schema_raw),
        "readinessRosterSchemaV2": _artifact(roster_schema_file, roster_schema_raw),
    }
    roster = {
        "schemaVersion": 2,
        "artifactType": "E14FourDetectorReadinessRoster",
        "rosterId": "e14-four-detector-readiness-roster-v2",
        "status": "readiness-planned-not-generated-not-fit",
        "immutable": True,
        "inputs": input_artifacts,
        "candidateCount": len(candidates),
        "candidateCountByMechanism": counts,
        "candidates": candidates,
        "retiredCandidateIds": retired,
        "authorizations": policy["authorizationPolicy"],
    }
    roster_raw = _json_bytes(roster)
    audit = {
        "schemaVersion": 2,
        "artifactType": "E14FourDetectorReadinessAudit",
        "status": STATUS,
        "inputs": input_artifacts,
        "outputs": {"readinessRosterV2": _artifact(outputs[0], roster_raw)},
        "inventory": {
            "plannedCandidateCount": len(candidates),
            "plannedCandidateCountByMechanism": counts,
            "eligibleCandidateCount": sum(eligible_counts.values()),
            "eligibleCandidateCountByMechanism": eligible_counts,
            "preservedV1CandidateIdCount": len(preserved_ids),
            "retiredV1CandidateIdCount": len(retired),
            "newV2CandidateIdCount": len(new_ids),
            "availabilityLagMonthsBySeries": {
                key: value["availabilityLagMonths"] for key, value in availability.items()
            },
            "matureScoringMonthBySeries": {
                key: value["matureScoringMonth"] for key, value in availability.items()
            },
        },
        "episodeCoverage": episode_coverage,
        "sensitivityPolicy": policy["fundingBoundarySensitivity"],
        "revisionRiskPolicy": policy["revisionRiskPolicy"],
        "checks": {
            "allInputHashesExact": True,
            "foundationV2AndLockConsistent": True,
            "foundationV1NotMutated": True,
            "availabilityLagApplied": True,
            "internalMissingnessAppliedWithoutCarry": True,
            "minimumSixtyNonmissingObservationsApplied": True,
            "sixteenBroadIdsPreservedExactly": len(preserved_ids) == 16,
            "twentyFourV1IdsRetired": len(retired) == 24,
            "twelveNewV2IdsUnique": len(new_ids) == len(set(new_ids)) == 12,
            "allTwentyEightCandidatesStructurallyEligible": sum(eligible_counts.values()) == 28,
            "fundingBoundarySensitivityFrozen": policy["fundingBoundarySensitivity"]["boundaryMonth"] == "2019-01-01",
            "pre2019WindowNotUsedAsAlternativeEligibilityGate": policy["fundingBoundarySensitivity"]["pre2019WindowIsNotAnAlternativeEligibilityGate"],
            "strictVintageReady": False,
            "candidateManifestGenerationClosed": True,
            "candidateFittingClosed": True,
            "outerOosClosed": True,
        },
        "protocol": {
            "readinessRosterMaterialized": True,
            "candidateManifestGenerated": False,
            "candidateFitted": False,
            "candidateEvaluated": False,
            "candidateRanked": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "decision": {
            "fullFourMechanismReadiness": True,
            "protocolV2DesignAuthorized": True,
            "candidateManifestGenerationAuthorized": False,
            "candidateFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "candidateRankingAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_readiness_v2",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return (
        _write_new_bytes(outputs[0], roster_raw, "readiness roster v2"),
        _write_new_bytes(outputs[1], _json_bytes(audit), "readiness audit v2"),
    )


def _validate_inputs(
    contract: dict[str, Any], taxonomy: dict[str, Any], foundation: dict[str, Any],
    lock: dict[str, Any], foundation_audit: dict[str, Any], manifest: dict[str, Any],
    plan: dict[str, Any], policy: dict[str, Any], policy_schema: dict[str, Any],
    roster_schema: dict[str, Any], taxonomy_raw: bytes, foundation_raw: bytes,
    lock_raw: bytes, foundation_audit_raw: bytes, manifest_raw: bytes,
    plan_raw: bytes, policy_raw: bytes, policy_schema_raw: bytes,
    roster_schema_raw: bytes,
) -> None:
    hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "featureFoundationV2Sha256": hashlib.sha256(foundation_raw).hexdigest(),
        "featureFoundationLockV2Sha256": hashlib.sha256(lock_raw).hexdigest(),
        "featureFoundationAuditV2Sha256": hashlib.sha256(foundation_audit_raw).hexdigest(),
        "candidateManifestV1Sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "coverageRepairPlanSha256": hashlib.sha256(plan_raw).hexdigest(),
        "readinessPolicyV2Sha256": hashlib.sha256(policy_raw).hexdigest(),
        "readinessPolicySchemaV2Sha256": hashlib.sha256(policy_schema_raw).hexdigest(),
        "readinessRosterSchemaV2Sha256": hashlib.sha256(roster_schema_raw).hexdigest(),
    }
    expected_auth = {
        "readinessRosterMaterializationAuthorized": True,
        "protocolV2DesignAuthorizedOnPass": True,
        "candidateManifestGenerationAuthorized": False,
        "candidateFittingAuthorized": False,
        "candidateEvaluationAuthorized": False,
        "candidateRankingAuthorized": False,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    transition = {
        "preservedV1CandidateIdCount": 16,
        "retiredV1CandidateIdCount": 24,
        "newV2CandidateIdCount": 12,
        "plannedCandidateCount": 28,
        "newIdsMustContainV2Namespace": True,
        "retiredIdReuseForbidden": True,
        "rosterIsNotCandidateManifest": True,
    }
    if (
        contract.get("contractId") != "e14-four-detector-readiness-contract-v2"
        or contract.get("inputHashes") != hashes
        or contract.get("transitionPolicy") != transition
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v2"
        or lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v2"
        or lock.get("foundation", {}).get("sha256") != hashes["featureFoundationV2Sha256"]
        or lock.get("structuralCoverageReady") is not True
        or lock.get("candidateGenerationAuthorized") is not False
        or foundation_audit.get("status") != "FEATURE_FOUNDATION_V2_MATERIALIZED_RESEARCH_ONLY_REVISION_LIMITATIONS_CANDIDATE_GENERATION_CLOSED"
        or foundation_audit.get("decision", {}).get("structuralCoverageRepaired") is not True
        or foundation_audit.get("decision", {}).get("candidateFittingAuthorized") is not False
        or manifest.get("status") != "GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED"
        or manifest.get("candidateCount") != 40
        or plan.get("candidateTransitionPolicy", {}).get("projectedCandidateBudget") != 28
        or policy.get("policyId") != "e14-four-detector-readiness-policy-v2"
        or policy.get("authorizationPolicy") != expected_auth
        or policy.get("candidateTransitionPolicy", {}).get("plannedCandidateCount") != 28
        or policy.get("eligibilityPolicy", {}).get("minimumHistoryObservations") != 60
        or policy.get("fundingBoundarySensitivity", {}).get("boundaryMonth") != "2019-01-01"
        or policy.get("revisionRiskPolicy", {}).get("strictVintageReady") is not False
        or policy_schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-readiness-policy-v2.json"
        or roster_schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-readiness-roster-v2.json"
    ):
        raise DatasetValidationError("E14 readiness-v2 inputs or governance are invalid.")


def _availability_descriptor(series: dict[str, Any], minimum_history: int) -> dict[str, Any]:
    nonmissing = [item for item in series["observations"] if item.get("value") is not None]
    if len(nonmissing) < minimum_history:
        raise DatasetValidationError("E14 readiness-v2 series has insufficient nonmissing history.")
    lags = {
        _month_difference(_period_month(item["period"]), _period_month(item["availableOn"]))
        for item in nonmissing
    }
    if len(lags) != 1 or next(iter(lags)) < 0:
        raise DatasetValidationError("E14 readiness-v2 series availability lag is inconsistent.")
    lag = next(iter(lags))
    mature = _period_month(nonmissing[minimum_history - 1]["availableOn"])
    return {
        "availabilityLagMonths": lag,
        "matureScoringMonth": mature.isoformat(),
        "nonmissingObservationCount": len(nonmissing),
    }


def _eligibility(
    taxonomy: dict[str, Any], mechanism: str, series_ids: list[str],
    series: dict[str, dict[str, Any]], availability: dict[str, dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    mature = max(date.fromisoformat(availability[item]["matureScoringMonth"]) for item in series_ids)
    positive = _observable_ids(
        taxonomy["episodes"], mechanism, "positive", series_ids, series,
        availability, mature,
    )
    negative = _observable_ids(
        taxonomy["hardNegativeEpisodes"], mechanism, "hard-negative", series_ids,
        series, availability, mature,
    )
    ready = (
        len(positive) >= policy["minimumObservablePositiveEpisodes"]
        and len(negative) >= policy["minimumObservableHardNegativeEpisodes"]
    )
    return {
        "matureScoringMonth": mature.isoformat(),
        "observablePositiveEpisodeIds": positive,
        "observablePositiveEpisodeCount": len(positive),
        "observableHardNegativeEpisodeIds": negative,
        "observableHardNegativeEpisodeCount": len(negative),
        "plannedLeaveOneOutFoldCount": len(positive) if ready else 0,
        "structurallyEligible": ready,
    }


def _observable_ids(
    episodes: list[dict[str, Any]], mechanism: str, state: str,
    series_ids: list[str], series: dict[str, dict[str, Any]],
    availability: dict[str, dict[str, Any]], mature: date,
) -> list[str]:
    maps = {
        series_id: {
            _period_month(item["period"]): item
            for item in series[series_id]["observations"]
        }
        for series_id in series_ids
    }
    output = []
    for episode in episodes:
        if episode.get("financialState") != state or mechanism not in episode.get("mechanisms", []):
            continue
        current = max(date.fromisoformat(episode["firstMonth"]), mature)
        stop = date.fromisoformat(episode["lastMonth"])
        observable = False
        while current <= stop and not observable:
            month_end = date(current.year, current.month, calendar.monthrange(current.year, current.month)[1])
            valid = True
            for series_id in series_ids:
                required_period = _add_months(current, -availability[series_id]["availabilityLagMonths"])
                item = maps[series_id].get(required_period)
                if (
                    item is None
                    or item.get("value") is None
                    or date.fromisoformat(item["availableOn"]) > month_end
                ):
                    valid = False
                    break
            observable = valid
            current = _add_months(current, 1)
        if observable:
            output.append(episode["independentEventId"])
    return sorted(set(output))


def _month_difference(left: date, right: date) -> int:
    return (right.year - left.year) * 12 + right.month - left.month


def _period_month(value: str) -> date:
    if "Q" in value:
        year, quarter = value.split("Q", 1)
        return date(int(year), (int(quarter) - 1) * 3 + 1, 1)
    return date.fromisoformat(value).replace(day=1)


def _add_months(value: date, months: int) -> date:
    offset = value.year * 12 + value.month - 1 + months
    return date(offset // 12, offset % 12 + 1, 1)


def _slug(mechanism: str) -> str:
    return {
        "banking-credit": "banking",
        "cross-border-growth": "cross-border",
        "funding-liquidity": "funding",
    }[mechanism]


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid E14 {label} JSON '{source}'.") from exc


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "sizeBytes": len(raw)}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _write_new_bytes(path: Path, raw: bytes, label: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E14 {label} already exists: '{path}'.") from exc
    return path
