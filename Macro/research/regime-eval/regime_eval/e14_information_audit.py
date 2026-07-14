from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import fmean, median
from typing import Any

from .dataset import DatasetValidationError, load_dataset
from .e13_loeo import _financial_controls, _financial_episode_inventory, _inner_dates
from .ground_truth import validate_recession_truth
from .stress import validate_stress_truth


FEATURES = (
    "vixSeverity",
    "spyDrawdownSeverity",
    "hygDrawdownSeverity",
    "creditSeverity",
    "fundingSeverity",
)


def write_e14_information_audit(
    dataset_path: str | Path,
    plan_path: str | Path,
    stress_truth_path: str | Path,
    recession_truth_path: str | Path,
    foundation_lock_path: str | Path,
    e13_decisions_path: str | Path,
    contract_path: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    plan_file, plan_bytes, plan = _read_json(plan_path, "walk-forward plan")
    stress_file, stress_bytes, stress = _read_json(stress_truth_path, "stress truth")
    recession_file, recession_bytes, recession = _read_json(recession_truth_path, "recession truth")
    lock_file, lock_bytes, lock = _read_json(foundation_lock_path, "foundation lock")
    decisions_file, decisions_bytes, decisions = _read_json(e13_decisions_path, "E13 decisions")
    contract_file, contract_bytes, contract = _read_json(contract_path, "E14 audit contract")
    _, stress_episodes = validate_stress_truth(stress)
    recession_periods = validate_recession_truth(recession)
    _validate_contract(
        dataset.sha256, plan_bytes, stress_bytes, recession_bytes, lock_bytes, lock,
        decisions_bytes, decisions, contract,
    )

    rows = sorted(dataset.rows, key=lambda item: item["asOfDate"])
    inner_keys, folds = _inner_dates(rows, plan)
    row_by_key = {row["asOfDate"]: row for row in rows}
    episodes = _financial_episode_inventory(inner_keys, stress_episodes)
    positive_keys = sorted({key for episode in episodes for key in episode["observedMonths"]})
    contrast_keys = _financial_controls(inner_keys, stress_episodes)
    unlabeled_keys = sorted(set(inner_keys) - set(positive_keys) - set(contrast_keys))
    severities = {key: _severities(row_by_key[key]) for key in inner_keys}

    feature_reports = []
    for feature in FEATURES:
        positive = [severities[key][feature] for key in positive_keys if severities[key][feature] is not None]
        contrast = [severities[key][feature] for key in contrast_keys if severities[key][feature] is not None]
        feature_reports.append({
            "feature": feature,
            "positive": _distribution(positive, len(positive_keys)),
            "contrast": _distribution(contrast, len(contrast_keys)),
            "directionalPairwiseAuc": _pairwise_auc(positive, contrast),
            "rangeOverlapRatio": _range_overlap(positive, contrast),
        })

    candidate_thresholds = contract["candidateDiagnostics"]
    diagnostics = {
        "noisyOr": _candidate_diagnostic(
            inner_keys, positive_keys, contrast_keys, severities,
            "noisy-or", float(candidate_thresholds["noisyOrThreshold"]),
        ),
        "topTwoMean": _candidate_diagnostic(
            inner_keys, positive_keys, contrast_keys, severities,
            "top-two-mean", float(candidate_thresholds["topTwoMeanThreshold"]),
        ),
    }
    episode_signatures = []
    for episode in episodes:
        keys = episode["observedMonths"]
        episode_signatures.append({
            **episode,
            "features": {
                feature: _distribution(
                    [severities[key][feature] for key in keys if severities[key][feature] is not None], len(keys)
                ) for feature in FEATURES
            },
            "noisyOrAlertMonths": [key for key in keys if diagnostics["noisyOr"]["scoresByDate"][key] >= diagnostics["noisyOr"]["threshold"]],
            "topTwoMeanAlertMonths": [key for key in keys if diagnostics["topTwoMean"]["scoresByDate"][key] >= diagnostics["topTwoMean"]["threshold"]],
        })
    for item in diagnostics.values():
        item.pop("scoresByDate")

    recession_observable = []
    for period in recession_periods:
        observed = [key for key in inner_keys if period["first"] <= _month(key) <= period["trough"]]
        if observed:
            recession_observable.append({"episodeId": period["name"], "observedMonths": observed})

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14InformationAudit",
        "status": "diagnostic-complete",
        "inputs": {
            "dataset": _artifact(dataset.path, dataset.path.read_bytes()),
            "walkForwardPlan": _artifact(plan_file, plan_bytes),
            "stressGroundTruth": _artifact(stress_file, stress_bytes),
            "recessionGroundTruth": _artifact(recession_file, recession_bytes),
            "foundationLock": _artifact(lock_file, lock_bytes),
            "e13GateDecisions": _artifact(decisions_file, decisions_bytes),
            "auditContract": _artifact(contract_file, contract_bytes),
        },
        "protocol": {
            "purpose": contract["purpose"],
            "scope": contract["scope"],
            "outerTestRowCountUsed": 0,
            "candidateGenerated": False,
            "rankingProduced": False,
            "promotionAuthorized": False,
            "contrastSemantics": "curated contrast, not confirmed negative class",
        },
        "coverage": {
            "foldCount": len(folds),
            "uniqueInnerRowCount": len(inner_keys),
            "from": inner_keys[0],
            "to": inner_keys[-1],
            "financialEpisodeCount": len(episodes),
            "financialPositiveMonthCount": len(positive_keys),
            "curatedContrastMonthCount": len(contrast_keys),
            "unlabeledMonthCount": len(unlabeled_keys),
            "observableRecessionEpisodeCount": len(recession_observable),
        },
        "featureSeparability": feature_reports,
        "episodeSignatures": episode_signatures,
        "candidateDiagnostics": diagnostics,
        "labelAudit": {
            "positiveMonths": positive_keys,
            "contrastMonths": contrast_keys,
            "unlabeledMonthsExcludedFromClassMetrics": len(unlabeled_keys),
            "contrastLabelCounts": _contrast_label_counts(contrast_keys, stress_episodes),
            "absenceOfFinancialLabelIsConfirmedNegative": False,
        },
        "recessionAudit": {
            "status": "INSUFFICIENT_EPISODES",
            "observableEpisodes": recession_observable,
            "minimumNeededForLoeo": 3,
            "outerRowsUsedToIncreaseEpisodeCount": 0,
        },
        "implementation": {
            "module": "regime_eval.e14_information_audit",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _severities(row: dict[str, Any]) -> dict[str, float | None]:
    values = {
        str(item["seriesCode"]): float(item["value"])
        for item in row.get("macroObservations", [])
        if item.get("seriesCode") and item.get("value") is not None
    }
    required = ("VIX_MONTHLY_MAX", "SPY_MONTHLY_MAX_DRAWDOWN", "HYG_MONTHLY_MAX_DRAWDOWN", "HY_OAS")
    missing = [code for code in required if code not in values]
    if missing:
        raise DatasetValidationError(f"E14 audit row lacks financial inputs: {missing}.")
    return {
        "vixSeverity": _clip01((values["VIX_MONTHLY_MAX"] - 18.0) / 42.0),
        "spyDrawdownSeverity": _clip01(values["SPY_MONTHLY_MAX_DRAWDOWN"] / 25.0),
        "hygDrawdownSeverity": _clip01(values["HYG_MONTHLY_MAX_DRAWDOWN"] / 15.0),
        "creditSeverity": _clip01((values["HY_OAS"] - 2.0) / 4.0),
        "fundingSeverity": _clip01(values["SOFR_EFFR_MONTHLY_MAX"] / 200.0)
        if "SOFR_EFFR_MONTHLY_MAX" in values else None,
    }


def _candidate_diagnostic(
    keys: list[str], positive_keys: list[str], contrast_keys: list[str],
    severities: dict[str, dict[str, float | None]], aggregator: str, threshold: float,
) -> dict[str, Any]:
    scores = {}
    for key in keys:
        values = [value for value in severities[key].values() if value is not None]
        if aggregator == "noisy-or":
            score = 1.0 - math.prod(1.0 - value for value in values)
        else:
            score = fmean(sorted(values, reverse=True)[:2])
        scores[key] = round(score, 8)
    positive_alerts = [key for key in positive_keys if scores[key] >= threshold]
    contrast_alerts = [key for key in contrast_keys if scores[key] >= threshold]
    return {
        "threshold": threshold,
        "positiveAlertCount": len(positive_alerts),
        "positiveMonthCount": len(positive_keys),
        "positiveRecall": round(len(positive_alerts) / len(positive_keys), 8),
        "contrastAlertCount": len(contrast_alerts),
        "contrastMonthCount": len(contrast_keys),
        "contrastAlertRate": round(len(contrast_alerts) / len(contrast_keys), 8),
        "contrastAlertMonths": contrast_alerts,
        "scoresByDate": scores,
    }


def _distribution(values: list[float], expected_count: int) -> dict[str, Any]:
    ordered = sorted(values)
    if not ordered:
        return {"expectedCount": expected_count, "availableCount": 0, "availabilityRate": 0.0, "min": None, "q25": None, "median": None, "q75": None, "max": None, "mean": None}
    return {
        "expectedCount": expected_count,
        "availableCount": len(ordered),
        "availabilityRate": round(len(ordered) / expected_count, 8),
        "min": round(ordered[0], 8),
        "q25": round(_quantile(ordered, 0.25), 8),
        "median": round(median(ordered), 8),
        "q75": round(_quantile(ordered, 0.75), 8),
        "max": round(ordered[-1], 8),
        "mean": round(fmean(ordered), 8),
    }


def _pairwise_auc(positive: list[float], contrast: list[float]) -> float | None:
    if not positive or not contrast:
        return None
    score = sum(1.0 if left > right else 0.5 if left == right else 0.0 for left in positive for right in contrast)
    return round(score / (len(positive) * len(contrast)), 8)


def _range_overlap(left: list[float], right: list[float]) -> float | None:
    if not left or not right:
        return None
    union = max(max(left), max(right)) - min(min(left), min(right))
    overlap = max(0.0, min(max(left), max(right)) - max(min(left), min(right)))
    return round(overlap / union, 8) if union > 0 else 1.0


def _quantile(values: list[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return values[lower] * (1.0 - fraction) + values[upper] * fraction


def _contrast_label_counts(keys: list[str], episodes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in keys:
        for episode in episodes:
            if episode["first"] <= _month(key) <= episode["last"]:
                for label in episode["labels"]:
                    if label != "financial_stress":
                        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def _validate_contract(
    dataset_sha: str, plan_bytes: bytes, stress_bytes: bytes, recession_bytes: bytes,
    lock_bytes: bytes, lock: Any, decisions_bytes: bytes, decisions: Any, contract: Any,
) -> None:
    actual = {
        "datasetSha256": dataset_sha,
        "walkForwardPlanSha256": hashlib.sha256(plan_bytes).hexdigest(),
        "stressGroundTruthSha256": hashlib.sha256(stress_bytes).hexdigest(),
        "recessionGroundTruthSha256": hashlib.sha256(recession_bytes).hexdigest(),
        "foundationLockSha256": hashlib.sha256(lock_bytes).hexdigest(),
        "e13GateDecisionsSha256": hashlib.sha256(decisions_bytes).hexdigest(),
    }
    if (
        not isinstance(contract, dict)
        or contract.get("contractId") != "e14-information-audit-contract-v1"
        or contract.get("inputHashes") != actual
        or contract.get("scope") != "unique nested-inner-validation dates only"
        or contract.get("featureFormulaVersion") != "e13-financial-severity-v1"
        or "Forbidden" not in str(contract.get("outerOosPolicy"))
        or "cannot authorize" not in str(contract.get("decisionBoundary"))
    ):
        raise DatasetValidationError("E14 information-audit contract is invalid.")
    if (
        not isinstance(lock, dict) or lock.get("status") != "frozen"
        or lock.get("hashes", {}).get("datasetSha256") != dataset_sha
        or decisions.get("status") != "completed-no-eligible-candidates"
        or decisions.get("phaseDecision", {}).get("outerOosOpened") is not False
    ):
        raise DatasetValidationError("E14 upstream evidence is invalid.")


def _month(value: str):
    from datetime import date
    return date.fromisoformat(value).replace(day=1)


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
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
        raise DatasetValidationError(f"Immutable E14 information audit exists: '{destination}'.") from exc
    return destination
