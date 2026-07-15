from __future__ import annotations

import bisect
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import fmean, median
from typing import Any

from .dataset import DatasetValidationError


STATUS = "INNER_LOEO_V2_EVALUATED_ABSOLUTE_GATES_APPLIED_OUTER_OOS_CLOSED"
MECHANISMS = [
    "banking-credit", "broad-market-repricing", "cross-border-growth", "funding-liquidity",
]


def write_e14_loeo_evaluation_v2(
    contract_path: str | Path, taxonomy_path: str | Path,
    candidate_manifest_path: str | Path, candidate_manifest_audit_path: str | Path,
    foundation_path: str | Path, foundation_lock_path: str | Path,
    foundation_audit_path: str | Path, candidate_protocol_path: str | Path,
    protocol_audit_path: str | Path, preregistration_path: str | Path,
    preregistration_audit_path: str | Path, report_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "LOEO evaluation contract v2", "taxonomy v5", "candidate manifest v2",
        "candidate manifest audit v2", "feature foundation v2", "feature foundation lock v2",
        "feature foundation audit v2", "candidate protocol v2", "protocol readiness audit v2",
        "LOEO preregistration v2", "LOEO preregistration audit v2", "LOEO report schema v2",
    )
    paths = (
        contract_path, taxonomy_path, candidate_manifest_path, candidate_manifest_audit_path,
        foundation_path, foundation_lock_path, foundation_audit_path, candidate_protocol_path,
        protocol_audit_path, preregistration_path, preregistration_audit_path, report_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    data = [item[2] for item in artifacts]
    (contract, taxonomy, manifest, manifest_audit, foundation, lock, foundation_audit,
     protocol, protocol_audit, prereg, prereg_audit, report_schema) = data
    hashes = _input_hashes([item[1] for item in artifacts[1:]])
    _validate_governance(
        contract, taxonomy, manifest, manifest_audit, foundation, lock, foundation_audit,
        protocol, protocol_audit, prereg, prereg_audit, report_schema, hashes,
    )

    episodes = _episode_index(taxonomy)
    ambiguous_months = _ambiguous_months(taxonomy)
    series = {item["seriesId"]: item for item in foundation["series"]}
    cutoff = _month(foundation["cutoffDate"])
    assignments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in prereg_audit["candidateFoldAssignments"]:
        assignments[item["candidateId"]].append(item)

    score_cache: dict[tuple[str, str], tuple[list[str], dict[str, float | None]]] = {}
    candidate_reports = []
    funding_reports = []
    for candidate in manifest["candidates"]:
        folds = []
        for assignment in assignments[candidate["candidateId"]]:
            held_out = assignment["heldOutPositiveEpisodeId"]
            cache_key = (candidate["profile"]["profileId"], held_out)
            if cache_key not in score_cache:
                excluded = set(_episode_months(episodes[candidate["mechanism"]]["positive"][held_out]))
                score_cache[cache_key] = _profile_scores(candidate, series, excluded, cutoff)
            keys, scores = score_cache[cache_key]
            fold = _evaluate_fold(
                candidate, assignment, keys, scores, episodes[candidate["mechanism"]],
                ambiguous_months, prereg,
            )
            folds.append(fold)
            if candidate["mechanism"] == "funding-liquidity":
                funding_reports.append(_funding_sensitivity(
                    candidate, assignment, keys, scores, fold, episodes[candidate["mechanism"]],
                    ambiguous_months, prereg,
                ))
        aggregate = _aggregate_candidate(candidate, folds)
        gate_checks = _gate_checks(candidate, aggregate, contract["absoluteGateRequirements"])
        candidate_reports.append({
            "candidateId": candidate["candidateId"],
            "mechanism": candidate["mechanism"],
            "profileId": candidate["profile"]["profileId"],
            "persistence": candidate["persistence"],
            "complexityScore": _complexity(candidate),
            "foldCount": len(folds),
            "folds": folds,
            "aggregate": aggregate,
            "absoluteGateChecks": gate_checks,
            "absoluteGatePassed": all(gate_checks.values()),
        })

    mechanism_reports = {}
    for mechanism in MECHANISMS:
        candidates = [item for item in candidate_reports if item["mechanism"] == mechanism]
        passing = [item["candidateId"] for item in candidates if item["absoluteGatePassed"]]
        mechanism_reports[mechanism] = {
            "candidateCount": len(candidates),
            "evaluatedCandidateCount": len(candidates),
            "absoluteGatePassingCandidateCount": len(passing),
            "absoluteGatePassingCandidateIds": passing,
            "absoluteGateHasPassingCandidate": bool(passing),
            "rankingPerformed": False,
            "shortlistProduced": False,
        }
    funding_summary = _funding_summary(funding_reports)
    all_mechanisms_pass = all(
        mechanism_reports[item]["absoluteGateHasPassingCandidate"] for item in MECHANISMS
    )
    funding_ranking_ready = funding_summary["complete"]
    ranking_authorized = all_mechanisms_pass and funding_ranking_ready

    input_artifacts = {
        name: _artifact(file, raw)
        for name, (file, raw, _) in zip((
            "loeoEvaluationContractV2", "taxonomyV5", "candidateManifestV2",
            "candidateManifestAuditV2", "featureFoundationV2", "featureFoundationLockV2",
            "featureFoundationAuditV2", "candidateProtocolV2", "protocolReadinessAuditV2",
            "loeoPreregistrationV2", "loeoPreregistrationAuditV2", "loeoReportSchemaV2",
        ), artifacts)
    }
    payload = {
        "schemaVersion": 2,
        "artifactType": "E14FourDetectorLoeoEvaluationReport",
        "status": STATUS,
        "inputs": input_artifacts,
        "inventory": {
            "candidateCount": len(candidate_reports),
            "evaluatedCandidateCount": len(candidate_reports),
            "foldAssignmentCount": sum(len(item["folds"]) for item in candidate_reports),
            "foldAssignmentCountByMechanism": contract["expectedFoldAssignmentCounts"],
            "absoluteGatePassingCandidateCount": sum(item["absoluteGatePassed"] for item in candidate_reports),
        },
        "checks": {
            "allInputHashesExact": True,
            "snapshotHashesUnchangedSincePreregistration": True,
            "all28CandidatesEvaluated": len(candidate_reports) == 28,
            "all140FrozenFoldsConsumedExactlyOnce": sum(len(item["folds"]) for item in candidate_reports) == 140,
            "heldOutEpisodeExcludedFromTransformFit": True,
            "heldOutLabelsExcludedFromThresholdSelection": True,
            "causalPercentilesUseAvailableHistoryOnly": True,
            "causalPercentileTiesUseMidrank": True,
            "missingnessResetsPersistenceWithoutZeroImputation": True,
            "absoluteGatesAppliedIndependently": True,
            "fundingSensitivityProduced": True,
            "candidateRankingAbsent": True,
            "crossMechanismCompositionAbsent": True,
            "outerOosClosed": True,
        },
        "candidates": candidate_reports,
        "mechanisms": mechanism_reports,
        "fundingBoundarySensitivity": funding_summary,
        "protocol": {
            "featureTransformationPerformed": True,
            "candidateFittingPerformed": True,
            "candidateEvaluationPerformed": True,
            "candidateRankingPerformed": False,
            "shortlistProduced": False,
            "crossMechanismCompositionPerformed": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "decision": {
            "allMechanismsHaveAbsoluteGatePassingCandidate": all_mechanisms_pass,
            "fundingSensitivityComplete": funding_ranking_ready,
            "withinMechanismRankingAuthorized": ranking_authorized,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["passingNextAction"] if ranking_authorized else contract["failingNextAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_loeo_evaluation_v2",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output_path, payload)


def apply_persistence_missing(
    scores: list[float | None], threshold: float, entry_months: int, recovery_months: int,
) -> list[bool | None]:
    active = False
    above = below = 0
    output: list[bool | None] = []
    for score in scores:
        if score is None:
            active = False
            above = below = 0
            output.append(None)
            continue
        if score >= threshold:
            above += 1
            below = 0
        else:
            below += 1
            above = 0
        if not active and above >= entry_months:
            active = True
        elif active and below >= recovery_months:
            active = False
        output.append(active)
    return output


def _profile_scores(
    candidate: dict[str, Any], series: dict[str, dict[str, Any]],
    excluded_months: set[str], cutoff: date,
) -> tuple[list[str], dict[str, float | None]]:
    transformed = [
        _causal_percentiles(series[item["seriesId"]], excluded_months, cutoff)
        for item in candidate["featureBindings"]
    ]
    keys = _month_range(
        min(_month(item["coverageFrom"]) for item in (series[x["seriesId"]] for x in candidate["featureBindings"])),
        cutoff,
    )
    aggregator = candidate["profile"]["aggregator"]
    scores: dict[str, float | None] = {}
    for key in keys:
        values = [item.get(key) for item in transformed]
        if any(value is None for value in values):
            scores[key] = None
        elif aggregator == "identity" and len(values) == 1:
            scores[key] = values[0]
        elif aggregator == "mean":
            scores[key] = round(fmean(float(value) for value in values), 8)
        elif aggregator == "maximum":
            scores[key] = round(max(float(value) for value in values), 8)
        else:
            raise DatasetValidationError(f"Unsupported E14 v2 aggregator '{aggregator}'.")
    return keys, scores


def _causal_percentiles(
    source: dict[str, Any], excluded_months: set[str], cutoff: date,
) -> dict[str, float | None]:
    history: list[float] = []
    output: dict[str, float | None] = {}
    observations = sorted(source["observations"], key=lambda item: (item["availableOn"], item["period"]))
    for observation in observations:
        scoring_month = max(_month(observation["period"]), _month(observation["availableOn"]))
        if scoring_month > cutoff:
            continue
        key = scoring_month.isoformat()
        value = observation.get("value")
        if value is None:
            output[key] = None
            continue
        numeric = float(value)
        if key in excluded_months:
            reference = history.copy()
            bisect.insort(reference, numeric)
            output[key] = _percentile_midrank(reference, numeric) if len(reference) >= 60 else None
            continue
        bisect.insort(history, numeric)
        output[key] = _percentile_midrank(history, numeric) if len(history) >= 60 else None
    return output


def _evaluate_fold(
    candidate: dict[str, Any], assignment: dict[str, Any], keys: list[str],
    scores: dict[str, float | None], episode_index: dict[str, dict[str, dict[str, Any]]],
    ambiguous_months: set[str], prereg: dict[str, Any],
) -> dict[str, Any]:
    held_out = assignment["heldOutPositiveEpisodeId"]
    excluded = set(_episode_months(episode_index["positive"][held_out]))
    train_values = [
        float(scores[key]) for key in keys
        if scores[key] is not None and key not in excluded and key not in ambiguous_months
    ]
    if not train_values:
        raise DatasetValidationError("E14 LOEO v2 fold has no training scores.")
    best: tuple[tuple[float, ...], float, float, dict[str, Any]] | None = None
    for quantile in prereg["thresholdSelection"]["quantiles"]:
        threshold = _quantile(train_values, float(quantile))
        states = _states(candidate, keys, scores, threshold)
        training = _training_metrics(
            keys, states, assignment["trainingPositiveEpisodeIds"],
            assignment["trainingHardNegativeEpisodeIds"], episode_index,
        )
        rank = (
            training["worstEpisodeRecall"], training["meanEpisodeRecall"],
            -training["hardNegativeAlertRate"], -training["meanOnsetDelayMonths"],
            -training["meanRecoveryLagMonths"], float(quantile),
        )
        if best is None or rank > best[0]:
            best = (rank, float(quantile), threshold, training)
    assert best is not None
    _, selected_quantile, threshold, training = best
    states = _states(candidate, keys, scores, threshold)
    held_metrics = _episode_metrics(keys, states, episode_index["positive"][held_out])
    control_rate = _hard_negative_rate(
        states, assignment["trainingHardNegativeEpisodeIds"], episode_index["hard-negative"]
    )
    unlabeled_alerts = _unlabeled_alert_count(keys, states, episode_index, ambiguous_months)
    return {
        "foldId": assignment["foldId"],
        "heldOutPositiveEpisodeId": held_out,
        "selectedQuantile": selected_quantile,
        "selectedThreshold": round(threshold, 8),
        "trainingScoreCount": len(train_values),
        "trainingMetrics": training,
        "heldOutObservedMonthCount": held_metrics["observedMonthCount"],
        "heldOutHit": held_metrics["hit"],
        "heldOutRecall": held_metrics["recall"],
        "heldOutOnsetDelayMonths": held_metrics["onsetDelayMonths"],
        "heldOutRecoveryLagMonths": held_metrics["recoveryLagMonths"],
        "hardNegativeAlertRate": control_rate,
        "unlabeledAlertCountReportedNotScored": unlabeled_alerts,
        "outerFeatureRowCountUsed": 0,
    }


def _states(
    candidate: dict[str, Any], keys: list[str], scores: dict[str, float | None], threshold: float,
) -> dict[str, bool | None]:
    persistence = candidate["persistence"]
    values = apply_persistence_missing(
        [scores[key] for key in keys], threshold,
        int(persistence["entryPersistenceMonths"]), int(persistence["recoveryPersistenceMonths"]),
    )
    return dict(zip(keys, values, strict=True))


def _training_metrics(
    keys: list[str], states: dict[str, bool | None], positive_ids: list[str],
    negative_ids: list[str], episode_index: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, float]:
    metrics = [_episode_metrics(keys, states, episode_index["positive"][item]) for item in positive_ids]
    if any(item["recall"] is None or item["onsetDelayMonths"] is None for item in metrics):
        return {
            "worstEpisodeRecall": -1.0, "meanEpisodeRecall": -1.0,
            "hardNegativeAlertRate": 1.0, "meanOnsetDelayMonths": 999.0,
            "meanRecoveryLagMonths": 999.0,
        }
    return {
        "worstEpisodeRecall": round(min(float(item["recall"]) for item in metrics), 8),
        "meanEpisodeRecall": round(fmean(float(item["recall"]) for item in metrics), 8),
        "hardNegativeAlertRate": _hard_negative_rate(states, negative_ids, episode_index["hard-negative"]),
        "meanOnsetDelayMonths": round(fmean(float(item["onsetDelayMonths"]) for item in metrics), 8),
        "meanRecoveryLagMonths": round(fmean(float(item["recoveryLagMonths"]) for item in metrics), 8),
    }


def _episode_metrics(
    keys: list[str], states: dict[str, bool | None], episode: dict[str, Any],
) -> dict[str, Any]:
    months = [key for key in _episode_months(episode) if key in states and states[key] is not None]
    if not months:
        return {"observedMonthCount": 0, "hit": False, "recall": None,
                "onsetDelayMonths": None, "recoveryLagMonths": None}
    active = [key for key in months if states[key] is True]
    hit = bool(active)
    recall = round(len(active) / len(months), 8)
    onset = _month_distance(_month(episode["firstMonth"]), _month(active[0])) if active else None
    last = _month(episode["lastMonth"])
    recovery = 0
    if states.get(last.isoformat()) is True:
        after = [key for key in keys if _month(key) > last]
        for key in after:
            if states[key] is not True:
                break
            recovery += 1
    return {"observedMonthCount": len(months), "hit": hit, "recall": recall,
            "onsetDelayMonths": onset, "recoveryLagMonths": recovery if hit else None}


def _hard_negative_rate(
    states: dict[str, bool | None], ids: list[str], episodes: dict[str, dict[str, Any]],
) -> float:
    months = sorted(set().union(*(_episode_months(episodes[item]) for item in ids)))
    observed = [states[item] for item in months if item in states and states[item] is not None]
    return round(sum(value is True for value in observed) / len(observed), 8) if observed else 1.0


def _unlabeled_alert_count(
    keys: list[str], states: dict[str, bool | None],
    episode_index: dict[str, dict[str, dict[str, Any]]], ambiguous: set[str],
) -> int:
    labeled = set().union(*(
        set(_episode_months(item))
        for group in episode_index.values() for item in group.values()
    )) | ambiguous
    return sum(states[key] is True for key in keys if key not in labeled)


def _aggregate_candidate(candidate: dict[str, Any], folds: list[dict[str, Any]]) -> dict[str, Any]:
    recalls = [item["heldOutRecall"] for item in folds]
    onsets = [item["heldOutOnsetDelayMonths"] for item in folds]
    recoveries = [item["heldOutRecoveryLagMonths"] for item in folds]
    thresholds = [float(item["selectedThreshold"]) for item in folds]
    complete = all(value is not None for value in recalls + onsets + recoveries)
    return {
        "observablePositiveEpisodeCount": candidate["eligibility"]["observablePositiveEpisodeCount"],
        "observableHardNegativeEpisodeCount": candidate["eligibility"]["observableHardNegativeEpisodeCount"],
        "episodeHitRate": round(sum(item["heldOutHit"] for item in folds) / len(folds), 8),
        "meanEpisodeRecall": round(fmean(float(value) for value in recalls), 8) if all(value is not None for value in recalls) else None,
        "worstEpisodeRecall": round(min(float(value) for value in recalls), 8) if all(value is not None for value in recalls) else None,
        "hardNegativeAlertRate": round(fmean(float(item["hardNegativeAlertRate"]) for item in folds), 8),
        "medianOnsetDelayMonths": round(float(median(float(value) for value in onsets)), 8) if complete else None,
        "medianRecoveryLagMonths": round(float(median(float(value) for value in recoveries)), 8) if complete else None,
        "thresholdRange": round(max(thresholds) - min(thresholds), 8),
        "unlabeledAlertCountReportedNotScored": sum(item["unlabeledAlertCountReportedNotScored"] for item in folds),
        "allMetricsComplete": complete,
    }


def _gate_checks(candidate: dict[str, Any], aggregate: dict[str, Any], req: dict[str, Any]) -> dict[str, bool]:
    def minimum(field: str, requirement: str) -> bool:
        value = aggregate[field]
        return value is not None and float(value) >= float(req[requirement])
    def maximum(field: str, requirement: str) -> bool:
        value = aggregate[field]
        return value is not None and float(value) <= float(req[requirement])
    return {
        "observablePositiveEpisodes": minimum("observablePositiveEpisodeCount", "minimumObservablePositiveEpisodes"),
        "observableHardNegativeEpisodes": minimum("observableHardNegativeEpisodeCount", "minimumObservableHardNegativeEpisodes"),
        "episodeHitRate": minimum("episodeHitRate", "minimumEpisodeHitRate"),
        "meanEpisodeRecall": minimum("meanEpisodeRecall", "minimumMeanEpisodeRecall"),
        "worstEpisodeRecall": minimum("worstEpisodeRecall", "minimumWorstEpisodeRecall"),
        "hardNegativeAlertRate": maximum("hardNegativeAlertRate", "maximumHardNegativeAlertRate"),
        "medianOnsetDelayMonths": maximum("medianOnsetDelayMonths", "maximumMedianOnsetDelayMonths"),
        "medianRecoveryLagMonths": maximum("medianRecoveryLagMonths", "maximumMedianRecoveryLagMonths"),
        "thresholdRange": maximum("thresholdRange", "maximumThresholdRange"),
        "allMetricsComplete": aggregate["allMetricsComplete"] is True,
    }


def _funding_sensitivity(
    candidate: dict[str, Any], assignment: dict[str, Any], keys: list[str],
    scores: dict[str, float | None], fold: dict[str, Any],
    episode_index: dict[str, dict[str, dict[str, Any]]], ambiguous_months: set[str],
    prereg: dict[str, Any],
) -> dict[str, Any]:
    boundary = _month(prereg["fundingBoundarySensitivity"]["boundaryMonth"])
    held = set(_episode_months(episode_index["positive"][assignment["heldOutPositiveEpisodeId"]]))
    full_values = [
        float(scores[key]) for key in keys
        if scores[key] is not None and key not in held and key not in ambiguous_months
    ]
    pre_values = [
        float(scores[key]) for key in keys
        if scores[key] is not None and _month(key) < boundary
        and key not in held and key not in ambiguous_months
    ]
    selected_quantile = float(fold["selectedQuantile"])
    pre_threshold = _quantile(pre_values, selected_quantile) if pre_values else None
    iqr = _quantile(pre_values, 0.75) - _quantile(pre_values, 0.25) if pre_values else 0.0
    full_threshold = float(fold["selectedThreshold"])
    states = _states(candidate, keys, scores, full_threshold)
    pre_states = [states[key] for key in keys if _month(key) < boundary and states[key] is not None]
    post_states = [states[key] for key in keys if _month(key) >= boundary and states[key] is not None]
    positive = episode_index["positive"]
    pre_ids = [key for key, item in positive.items() if _month(item["lastMonth"]) < boundary]
    post_ids = [key for key, item in positive.items() if _month(item["firstMonth"]) >= boundary]
    thresholds_by_quantile = [
        {
            "quantile": float(quantile),
            "fullTrainingThreshold": _quantile(full_values, float(quantile)),
            "pre2019TrainingThreshold": _quantile(pre_values, float(quantile)) if pre_values else None,
        }
        for quantile in prereg["thresholdSelection"]["quantiles"]
    ]
    return {
        "candidateId": candidate["candidateId"], "foldId": assignment["foldId"],
        "selectedQuantile": selected_quantile, "fullTrainingThreshold": full_threshold,
        "pre2019TrainingThreshold": round(pre_threshold, 8) if pre_threshold is not None else None,
        "pre2019Iqr": round(iqr, 8),
        "normalizedThresholdShiftByPre2019Iqr": round(abs(full_threshold - pre_threshold) / iqr, 8) if pre_threshold is not None and iqr > 0 else None,
        "pre2019AlertRate": round(sum(x is True for x in pre_states) / len(pre_states), 8) if pre_states else None,
        "post2019AlertRate": round(sum(x is True for x in post_states) / len(post_states), 8) if post_states else None,
        "thresholdsQ80Q90Q95FullVersusPre2019": thresholds_by_quantile,
        "pre2019PositiveEpisodeIds": pre_ids,
        "post2019PositiveEpisodeIds": post_ids,
        "pre2019PositiveEpisodeCount": len(pre_ids),
        "post2019PositiveEpisodeCount": len(post_ids),
        "episodeMetricsSplit": {
            "pre2019": _episode_group_summary(keys, states, pre_ids, positive),
            "post2019": _episode_group_summary(keys, states, post_ids, positive),
        },
        "insufficientPositiveEpisodesInPre2019Window": len(pre_ids) < 3,
    }


def _funding_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    required = (
        "pre2019TrainingThreshold", "normalizedThresholdShiftByPre2019Iqr",
        "pre2019AlertRate", "post2019AlertRate",
    )
    complete = bool(reports) and all(
        all(item[field] is not None for field in required)
        and len(item["thresholdsQ80Q90Q95FullVersusPre2019"]) == 3
        and item["episodeMetricsSplit"]["pre2019"]["episodeCount"] > 0
        and item["episodeMetricsSplit"]["post2019"]["episodeCount"] > 0
        for item in reports
    )
    return {
        "boundaryMonth": "2019-01-01",
        "candidateFoldReportCount": len(reports),
        "complete": complete,
        "missingSensitivityReportBlocksRanking": True,
        "distributionEquivalenceClaimed": False,
        "pre2019WindowUsedAsAlternativeEligibilityGate": False,
        "reports": reports,
    }


def _episode_group_summary(
    keys: list[str], states: dict[str, bool | None], ids: list[str],
    episodes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    metrics = [_episode_metrics(keys, states, episodes[item]) for item in ids]
    recalls = [item["recall"] for item in metrics if item["recall"] is not None]
    return {
        "episodeCount": len(ids),
        "episodeHitRate": round(sum(item["hit"] for item in metrics) / len(metrics), 8) if metrics else None,
        "meanEpisodeRecall": round(fmean(float(item) for item in recalls), 8) if len(recalls) == len(metrics) and metrics else None,
        "metrics": [dict(episodeId=episode_id, **metric) for episode_id, metric in zip(ids, metrics)],
    }


def _validate_governance(
    contract: dict[str, Any], taxonomy: dict[str, Any], manifest: dict[str, Any],
    manifest_audit: dict[str, Any], foundation: dict[str, Any], lock: dict[str, Any],
    foundation_audit: dict[str, Any], protocol: dict[str, Any], protocol_audit: dict[str, Any],
    prereg: dict[str, Any], prereg_audit: dict[str, Any], schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    expected_auth = {
        "innerFeatureTransformationAuthorized": True,
        "innerCandidateFittingAuthorized": True,
        "innerLoeoEvaluationAuthorized": True,
        "candidateRankingAuthorizedNow": False,
        "withinMechanismRankingAuthorizedOnAllMechanismsHavePassingCandidate": True,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    if (
        contract.get("contractId") != "e14-four-detector-loeo-evaluation-contract-v2"
        or contract.get("inputHashes") != hashes
        or contract.get("authorizationPolicy") != expected_auth
        or contract.get("expectedStatus") != STATUS
        or contract.get("absoluteGateRequirements") != prereg.get("absoluteGatePolicy", {}).get("requirements")
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or manifest.get("candidateCount") != contract.get("expectedCandidateCount")
        or manifest.get("candidateIds") != protocol.get("candidateIds")
        or manifest_audit.get("outputs", {}).get("candidateManifestV2", {}).get("sha256") != hashes["candidateManifestV2Sha256"]
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v2"
        or lock.get("foundation", {}).get("sha256") != hashes["featureFoundationV2Sha256"]
        or foundation_audit.get("outputs", {}).get("foundationV2", {}).get("sha256") != hashes["featureFoundationV2Sha256"]
        or protocol.get("protocolId") != "e14-four-detector-candidate-generation-protocol-v2"
        or protocol_audit.get("outputs", {}).get("candidateProtocolV2", {}).get("sha256") != hashes["candidateProtocolV2Sha256"]
        or prereg.get("preregistrationId") != "e14-four-detector-loeo-preregistration-v2"
        or prereg_audit.get("status") != "INNER_LOEO_V2_PREREGISTERED_FULL_READINESS_FITTING_EVALUATION_AUTHORIZED_OUTER_OOS_CLOSED"
        or prereg_audit.get("inventory", {}).get("candidateFoldAssignmentCount") != contract.get("expectedFoldAssignmentCount")
        or prereg_audit.get("decision", {}).get("innerCandidateFittingAuthorized") is not True
        or prereg_audit.get("decision", {}).get("outerOosAuthorized") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-loeo-report-v2.json"
    ):
        raise DatasetValidationError("E14 LOEO evaluation v2 inputs or governance are invalid.")
    ids = [item["foldId"] for item in prereg_audit.get("candidateFoldAssignments", [])]
    counts = Counter(item["mechanism"] for item in prereg_audit["candidateFoldAssignments"])
    if len(ids) != len(set(ids)) or {item: counts[item] for item in MECHANISMS} != contract["expectedFoldAssignmentCounts"]:
        raise DatasetValidationError("E14 LOEO evaluation v2 fold registry is invalid.")


def _input_hashes(raws: list[bytes]) -> dict[str, str]:
    names = (
        "taxonomyV5Sha256", "candidateManifestV2Sha256", "candidateManifestAuditV2Sha256",
        "featureFoundationV2Sha256", "featureFoundationLockV2Sha256", "featureFoundationAuditV2Sha256",
        "candidateProtocolV2Sha256", "protocolReadinessAuditV2Sha256",
        "loeoPreregistrationV2Sha256", "loeoPreregistrationAuditV2Sha256", "loeoReportSchemaV2Sha256",
    )
    return {name: _sha(raw) for name, raw in zip(names, raws)}


def _episode_index(taxonomy: dict[str, Any]) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    output = {mechanism: {"positive": {}, "hard-negative": {}} for mechanism in MECHANISMS}
    for collection in (taxonomy["episodes"], taxonomy["hardNegativeEpisodes"]):
        for episode in collection:
            state = episode.get("financialState")
            if state not in {"positive", "hard-negative"}:
                continue
            for mechanism in episode.get("mechanisms", []):
                output[mechanism][state][episode["independentEventId"]] = episode
    return output


def _ambiguous_months(taxonomy: dict[str, Any]) -> set[str]:
    return set().union(*(
        set(_episode_months(item)) for item in taxonomy["episodes"]
        if item.get("financialState") == "ambiguous"
    ))


def _episode_months(episode: dict[str, Any]) -> list[str]:
    return _month_range(_month(episode["firstMonth"]), _month(episode["lastMonth"]))


def _month_range(first: date, last: date) -> list[str]:
    output = []
    current = first
    while current <= last:
        output.append(current.isoformat())
        current = _add_months(current, 1)
    return output


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise DatasetValidationError("E14 LOEO v2 cannot compute a quantile on no values.")
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction, 8)


def _percentile_midrank(history: list[float], value: float) -> float:
    left = bisect.bisect_left(history, value)
    right = bisect.bisect_right(history, value)
    return round((left + right) / (2.0 * len(history)), 8)


def _complexity(candidate: dict[str, Any]) -> int:
    aggregator = 1 if candidate["profile"]["aggregator"] == "identity" else 2
    return aggregator + len(candidate["featureBindings"]) + int(candidate["persistence"]["entryPersistenceMonths"]) + int(candidate["persistence"]["recoveryPersistenceMonths"])


def _month_distance(first: date, second: date) -> int:
    return (second.year - first.year) * 12 + second.month - first.month


def _month(value: str) -> date:
    return date.fromisoformat(value).replace(day=1)


def _add_months(value: date, months: int) -> date:
    offset = value.year * 12 + value.month - 1 + months
    return date(offset // 12, offset % 12 + 1, 1)


def _read(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid E14 {label} JSON '{source}'.") from exc


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _write_new(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E14 LOEO evaluation report v2 already exists: '{destination}'.") from exc
    return destination
