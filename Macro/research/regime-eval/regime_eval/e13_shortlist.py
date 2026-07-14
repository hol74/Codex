from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


MAXIMIZE = ("episodeHitRate", "meanEpisodeRecall", "worstEpisodeRecall")
MINIMIZE = ("meanControlFalsePositiveRate", "thresholdRange", "complexityScore")


def write_e13_shortlist(
    loeo_report_path: str | Path,
    evaluation_contract_path: str | Path,
    generated_manifest_path: str | Path,
    shortlist_contract_path: str | Path,
    output_path: str | Path,
) -> Path:
    report_file, report_bytes, report = _read_json(loeo_report_path, "E13 LOEO report")
    evaluation_file, evaluation_bytes, evaluation = _read_json(
        evaluation_contract_path, "E13 LOEO evaluation contract"
    )
    manifest_file, manifest_bytes, manifest = _read_json(generated_manifest_path, "E13 generated manifest")
    contract_file, contract_bytes, contract = _read_json(shortlist_contract_path, "E13 shortlist contract")
    _validate_contract(report_bytes, report, evaluation_bytes, evaluation, manifest_bytes, manifest, contract)

    financial = report["tasks"]["financial-stress-signal"]["candidates"]
    eligible = [candidate for candidate in financial if _eligible(candidate, contract)]
    if len(eligible) < 2:
        raise DatasetValidationError("E13.3 needs at least two eligible financial candidates.")
    frontier = [candidate for candidate in eligible if not any(
        _dominates(other, candidate) for other in eligible if other is not candidate
    )]
    coverage = max(frontier, key=_coverage_rank)
    precision = min(frontier, key=_precision_rank)
    if coverage["candidateId"] == precision["candidateId"]:
        remaining = [candidate for candidate in frontier if candidate["candidateId"] != coverage["candidateId"]]
        if not remaining:
            raise DatasetValidationError("E13.3 cannot produce two distinct Pareto profiles.")
        precision = min(remaining, key=_precision_rank)

    selected_by_id = {coverage["candidateId"]: "coverage", precision["candidateId"]: "precision"}
    selected = [
        _selected(candidate, selected_by_id[candidate["candidateId"]])
        for candidate in sorted((coverage, precision), key=lambda item: selected_by_id[item["candidateId"]])
    ]
    excluded = []
    frontier_ids = {candidate["candidateId"] for candidate in frontier}
    for candidate in financial:
        candidate_id = candidate["candidateId"]
        if candidate_id in selected_by_id:
            continue
        if not _eligible(candidate, contract):
            reason = "below-minimum-episode-hit-rate-or-not-loeo-evaluated"
        elif candidate_id not in frontier_ids:
            dominators = sorted(
                other["candidateId"] for other in eligible if _dominates(other, candidate)
            )
            reason = "pareto-dominated-by:" + ",".join(dominators)
        else:
            reason = "pareto-frontier-not-profile-champion"
        excluded.append({"candidateId": candidate_id, "reason": reason})

    payload = {
        "schemaVersion": 1,
        "artifactType": "E13FinancialShortlist",
        "status": "shortlisted-not-gated",
        "frozenAt": contract["frozenAt"],
        "inputs": {
            "loeoReport": _artifact(report_file, report_bytes),
            "loeoEvaluationContract": _artifact(evaluation_file, evaluation_bytes),
            "generatedManifest": _artifact(manifest_file, manifest_bytes),
            "shortlistContract": _artifact(contract_file, contract_bytes),
        },
        "selection": {
            "task": "financial-stress-signal",
            "eligibleCandidateCount": len(eligible),
            "paretoFrontierCandidateIds": sorted(frontier_ids),
            "maximumShortlistCount": contract["maximumShortlistPerTask"],
            "selectedCount": len(selected),
            "selected": selected,
            "excluded": sorted(excluded, key=lambda item: item["candidateId"]),
        },
        "blockedTasks": [{
            "task": "recession-signal",
            "status": "NO_SHORTLIST",
            "reason": contract["blockedTasks"]["recession-signal"],
            "candidateCountSelected": 0,
        }],
        "lifecycle": {
            "maximum": contract["maximumLifecycle"],
            "gatePassed": False,
            "promotionAuthorized": False,
            "outerOosOpened": False,
        },
        "implementation": {
            "module": "regime_eval.e13_shortlist",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _eligible(candidate: dict[str, Any], contract: dict[str, Any]) -> bool:
    aggregate = candidate.get("aggregate")
    return (
        candidate.get("status") == contract["eligibility"]["requiredStatus"]
        and isinstance(aggregate, dict)
        and float(aggregate["episodeHitRate"]) + 1e-9
        >= float(contract["eligibility"]["minimumEpisodeHitRate"])
    )


def _dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_metrics = _metrics(left)
    right_metrics = _metrics(right)
    no_worse = all(left_metrics[key] >= right_metrics[key] for key in MAXIMIZE) and all(
        left_metrics[key] <= right_metrics[key] for key in MINIMIZE
    )
    strictly_better = any(left_metrics[key] > right_metrics[key] for key in MAXIMIZE) or any(
        left_metrics[key] < right_metrics[key] for key in MINIMIZE
    )
    return no_worse and strictly_better


def _coverage_rank(candidate: dict[str, Any]) -> tuple[float, ...]:
    metrics = _metrics(candidate)
    return (
        metrics["episodeHitRate"], metrics["worstEpisodeRecall"], metrics["meanEpisodeRecall"],
        -metrics["meanControlFalsePositiveRate"], -metrics["complexityScore"],
    )


def _precision_rank(candidate: dict[str, Any]) -> tuple[float, ...]:
    metrics = _metrics(candidate)
    return (
        metrics["meanControlFalsePositiveRate"], metrics["complexityScore"],
        -metrics["episodeHitRate"], -metrics["worstEpisodeRecall"], -metrics["meanEpisodeRecall"],
    )


def _metrics(candidate: dict[str, Any]) -> dict[str, float]:
    aggregate = candidate["aggregate"]
    return {
        "episodeHitRate": float(aggregate["episodeHitRate"]),
        "meanEpisodeRecall": float(aggregate["meanEpisodeRecall"]),
        "worstEpisodeRecall": float(aggregate["worstEpisodeRecall"]),
        "meanControlFalsePositiveRate": float(aggregate["meanControlFalsePositiveRate"]),
        "thresholdRange": float(aggregate["thresholdRange"]),
        "complexityScore": float(candidate["complexityScore"]),
    }


def _selected(candidate: dict[str, Any], role: str) -> dict[str, Any]:
    thresholds = sorted({float(item["selectedThreshold"]) for item in candidate["leaveouts"]})
    return {
        "candidateId": candidate["candidateId"],
        "selectionRole": role,
        "parameters": candidate["parameters"],
        "loeoMetrics": _metrics(candidate),
        "observedSelectedThresholds": thresholds,
        "lifecycleStatus": "research-shortlisted",
        "gateStatus": "NOT_RUN",
    }


def _validate_contract(
    report_bytes: bytes, report: Any, evaluation_bytes: bytes, evaluation: Any,
    manifest_bytes: bytes, manifest: Any, contract: Any,
) -> None:
    if (
        not isinstance(report, dict)
        or report.get("reportType") != "E13LeaveOneEpisodeOutEvaluation"
        or report.get("status") != "evaluated-no-shortlist"
        or report.get("protocol", {}).get("outerTestRowCountUsed") != 0
        or report.get("protocol", {}).get("shortlistProduced") is not False
        or report.get("tasks", {}).get("financial-stress-signal", {}).get("status") != "LOEO_COMPLETE"
        or report.get("tasks", {}).get("recession-signal", {}).get("status") != "INSUFFICIENT_EPISODES"
    ):
        raise DatasetValidationError("E13.3 LOEO report is not eligible for shortlist construction.")
    if evaluation.get("contractId") != "e13-loeo-evaluation-contract-v1" or manifest.get("status") != "generated-not-evaluated":
        raise DatasetValidationError("E13.3 upstream contracts are invalid.")
    if (
        not isinstance(contract, dict)
        or contract.get("contractId") != "e13-shortlist-contract-v1"
        or contract.get("loeoReportSha256") != hashlib.sha256(report_bytes).hexdigest()
        or contract.get("loeoEvaluationContractSha256") != hashlib.sha256(evaluation_bytes).hexdigest()
        or contract.get("generatedManifestSha256") != hashlib.sha256(manifest_bytes).hexdigest()
        or contract.get("eligibleTasks") != ["financial-stress-signal"]
        or contract.get("blockedTasks") != {"recession-signal": "INSUFFICIENT_EPISODES"}
        or contract.get("paretoObjectives", {}).get("maximize") != list(MAXIMIZE)
        or contract.get("paretoObjectives", {}).get("minimize") != list(MINIMIZE)
        or contract.get("maximumShortlistPerTask") != 2
        or "Forbidden" not in str(contract.get("outerOosPolicy"))
        or contract.get("maximumLifecycle") != "research-shortlisted"
        or contract.get("promotionAuthorized") is not False
    ):
        raise DatasetValidationError("E13.3 shortlist contract is invalid.")


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
        raise DatasetValidationError(f"Immutable E13 shortlist exists: '{destination}'.") from exc
    return destination
