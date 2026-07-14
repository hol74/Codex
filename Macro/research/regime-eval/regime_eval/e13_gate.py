from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


EXPECTED_IDS = {"e13-financial-8ec8415452", "e13-financial-7452a93533"}


def write_e13_financial_gate_decisions(
    shortlist_path: str | Path,
    loeo_report_path: str | Path,
    gate_path: str | Path,
    output_path: str | Path,
) -> Path:
    shortlist_file, shortlist_bytes, shortlist = _read_json(shortlist_path, "E13 shortlist")
    report_file, report_bytes, report = _read_json(loeo_report_path, "E13 LOEO report")
    gate_file, gate_bytes, gate = _read_json(gate_path, "E13 financial gate")
    _validate_contract(shortlist_bytes, shortlist, report_bytes, report, gate)

    report_candidates = {
        candidate["candidateId"]: candidate
        for candidate in report["tasks"]["financial-stress-signal"]["candidates"]
    }
    decisions = []
    for selected in shortlist["selection"]["selected"]:
        candidate_id = selected["candidateId"]
        report_candidate = report_candidates[candidate_id]
        _validate_metric_copy(selected, report_candidate)
        metrics = selected["loeoMetrics"]
        requirements = gate["requirements"]
        checks = {
            "minimumObservableEpisodes": int(report_candidate["episodeCount"])
            >= int(requirements["minimumObservableEpisodes"]),
            "minimumEpisodeHitRate": float(metrics["episodeHitRate"])
            >= float(requirements["minimumEpisodeHitRate"]),
            "minimumMeanEpisodeRecall": float(metrics["meanEpisodeRecall"])
            >= float(requirements["minimumMeanEpisodeRecall"]),
            "minimumWorstEpisodeRecall": float(metrics["worstEpisodeRecall"])
            >= float(requirements["minimumWorstEpisodeRecall"]),
            "maximumMeanControlFalsePositiveRate": float(metrics["meanControlFalsePositiveRate"])
            <= float(requirements["maximumMeanControlFalsePositiveRate"]),
            "maximumThresholdRange": float(metrics["thresholdRange"])
            <= float(requirements["maximumThresholdRange"]),
            "maximumComplexityScore": float(metrics["complexityScore"])
            <= float(requirements["maximumComplexityScore"]),
            "outerTestClosed": True,
        }
        passed = all(checks.values())
        decisions.append({
            "candidateId": candidate_id,
            "selectionRole": selected["selectionRole"],
            "metrics": metrics,
            "checks": checks,
            "failedChecks": sorted(key for key, value in checks.items() if not value),
            "passed": passed,
            "status": gate["passingStatus"] if passed else gate["failingStatus"],
            "maximumLifecycle": gate["maximumLifecycleOnPass"] if passed else "research-rejected",
            "operationalApprovalAuthorized": False,
        })
    decisions.sort(key=lambda item: item["candidateId"])
    passed_count = sum(item["passed"] for item in decisions)
    payload = {
        "schemaVersion": 1,
        "artifactType": "E13FinancialAbsoluteGateDecisions",
        "status": "completed-with-eligible-candidates" if passed_count else "completed-no-eligible-candidates",
        "decidedAt": gate["frozenAt"],
        "inputs": {
            "shortlist": _artifact(shortlist_file, shortlist_bytes),
            "loeoReport": _artifact(report_file, report_bytes),
            "gate": _artifact(gate_file, gate_bytes),
        },
        "protocol": {
            "task": "financial-stress-signal",
            "decisionMode": "independent-absolute-all-checks-required",
            "candidateCount": len(decisions),
            "passedCount": passed_count,
            "outerTestRowCountUsed": 0,
            "relativeRankingUsed": False,
            "fallbackCandidateAllowed": False,
        },
        "decisions": decisions,
        "blockedTasks": [{
            "task": "recession-signal",
            "status": "NO_GATE_INSUFFICIENT_EPISODES",
            "candidateCount": 0,
        }],
        "phaseDecision": {
            "eligibleForShadowReviewCount": passed_count,
            "fusionAllowed": False,
            "outerOosOpened": False,
            "operationalApprovalAuthorized": False,
        },
        "implementation": {
            "module": "regime_eval.e13_gate",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new_json(output_path, payload)


def _validate_contract(
    shortlist_bytes: bytes, shortlist: Any, report_bytes: bytes, report: Any, gate: Any
) -> None:
    selected = shortlist.get("selection", {}).get("selected", []) if isinstance(shortlist, dict) else []
    selected_ids = {item.get("candidateId") for item in selected}
    if (
        shortlist.get("artifactType") != "E13FinancialShortlist"
        or shortlist.get("status") != "shortlisted-not-gated"
        or len(selected) != 2 or selected_ids != EXPECTED_IDS
        or shortlist.get("lifecycle", {}).get("outerOosOpened") is not False
        or shortlist.get("lifecycle", {}).get("promotionAuthorized") is not False
        or shortlist.get("blockedTasks", [{}])[0].get("candidateCountSelected") != 0
    ):
        raise DatasetValidationError("E13.4 shortlist is invalid.")
    if (
        report.get("reportType") != "E13LeaveOneEpisodeOutEvaluation"
        or report.get("status") != "evaluated-no-shortlist"
        or report.get("protocol", {}).get("outerTestRowCountUsed") != 0
        or report.get("tasks", {}).get("recession-signal", {}).get("status") != "INSUFFICIENT_EPISODES"
    ):
        raise DatasetValidationError("E13.4 LOEO report is invalid.")
    requirements = gate.get("requirements", {}) if isinstance(gate, dict) else {}
    if (
        gate.get("contractId") != "e13-financial-absolute-gate-v1"
        or gate.get("shortlistSha256") != hashlib.sha256(shortlist_bytes).hexdigest()
        or gate.get("loeoReportSha256") != hashlib.sha256(report_bytes).hexdigest()
        or set(gate.get("registeredCandidateIds", [])) != EXPECTED_IDS
        or requirements != {
            "minimumObservableEpisodes": 3,
            "minimumEpisodeHitRate": 1.0,
            "minimumMeanEpisodeRecall": 0.5,
            "minimumWorstEpisodeRecall": 0.5,
            "maximumMeanControlFalsePositiveRate": 0.15,
            "maximumThresholdRange": 0.15,
            "maximumComplexityScore": 6,
        }
        or "Every requirement" not in str(gate.get("decisionPolicy"))
        or "Forbidden" not in str(gate.get("outerOosPolicy"))
        or gate.get("operationalApprovalAuthorized") is not False
        or gate.get("humanReviewRequired") is not True
    ):
        raise DatasetValidationError("E13.4 absolute gate contract is invalid.")


def _validate_metric_copy(selected: dict[str, Any], report_candidate: dict[str, Any]) -> None:
    expected = {
        **report_candidate["aggregate"],
        "complexityScore": float(report_candidate["complexityScore"]),
    }
    actual = selected.get("loeoMetrics")
    if not isinstance(actual, dict) or any(float(actual[key]) != float(value) for key, value in expected.items()):
        raise DatasetValidationError("E13.4 shortlist metrics differ from the frozen LOEO report.")


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
        raise DatasetValidationError(f"Immutable E13 gate decisions exist: '{destination}'.") from exc
    return destination
