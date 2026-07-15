from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean
from typing import Any

from .dataset import DatasetValidationError


STATUS = "LOEO_V2_NO_GO_DIAGNOSED_NEW_INFORMATION_HYPOTHESIS_REQUIRED"
MECHANISMS = [
    "banking-credit", "broad-market-repricing", "cross-border-growth", "funding-liquidity",
]


def write_e14_no_go_diagnostic(
    contract_path: str | Path, taxonomy_path: str | Path,
    candidate_manifest_path: str | Path, candidate_protocol_path: str | Path,
    preregistration_path: str | Path, preregistration_audit_path: str | Path,
    loeo_report_path: str | Path, diagnostic_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    labels = (
        "no-go diagnostic contract", "taxonomy v5", "candidate manifest v2",
        "candidate protocol v2", "LOEO preregistration v2", "LOEO preregistration audit v2",
        "LOEO report v2", "no-go diagnostic schema",
    )
    paths = (
        contract_path, taxonomy_path, candidate_manifest_path, candidate_protocol_path,
        preregistration_path, preregistration_audit_path, loeo_report_path, diagnostic_schema_path,
    )
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    ((contract_file, contract_raw, contract), (taxonomy_file, taxonomy_raw, taxonomy),
     (manifest_file, manifest_raw, manifest), (protocol_file, protocol_raw, protocol),
     (prereg_file, prereg_raw, prereg), (prereg_audit_file, prereg_audit_raw, prereg_audit),
     (report_file, report_raw, report), (schema_file, schema_raw, schema)) = artifacts
    hashes = {
        "taxonomyV5Sha256": _sha(taxonomy_raw),
        "candidateManifestV2Sha256": _sha(manifest_raw),
        "candidateProtocolV2Sha256": _sha(protocol_raw),
        "loeoPreregistrationV2Sha256": _sha(prereg_raw),
        "loeoPreregistrationAuditV2Sha256": _sha(prereg_audit_raw),
        "loeoReportV2Sha256": _sha(report_raw),
        "diagnosticSchemaV1Sha256": _sha(schema_raw),
    }
    _validate(contract, taxonomy, manifest, protocol, prereg, prereg_audit, report, schema, hashes)

    gate_diagnostics = _gate_failures(report)
    episode_diagnostics = _episode_diagnostics(report)
    profile_diagnostics = _profile_diagnostics(report, manifest)
    persistence_diagnostics = _persistence_diagnostics(report)
    conclusions = _mechanism_conclusions(
        report, episode_diagnostics, profile_diagnostics, gate_diagnostics,
    )
    all_worst_zero = all(
        candidate["aggregate"]["worstEpisodeRecall"] in {0, 0.0}
        for candidate in report["candidates"]
    )
    hard_negative_gate_failure_count = sum(
        not candidate["absoluteGateChecks"]["hardNegativeAlertRate"]
        for candidate in report["candidates"]
    )
    threshold_range_failure_count = sum(
        not candidate["absoluteGateChecks"]["thresholdRange"]
        for candidate in report["candidates"]
    )
    input_artifacts = {
        name: _artifact(file, raw)
        for name, (file, raw, _) in zip((
            "diagnosticContract", "taxonomyV5", "candidateManifestV2",
            "candidateProtocolV2", "loeoPreregistrationV2",
            "loeoPreregistrationAuditV2", "loeoReportV2", "diagnosticSchemaV1",
        ), artifacts)
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14LoeoNoGoDiagnostic",
        "status": STATUS,
        "inputs": input_artifacts,
        "inventory": {
            "candidateCount": len(report["candidates"]),
            "foldCount": report["inventory"]["foldAssignmentCount"],
            "absoluteGatePassingCandidateCount": report["inventory"]["absoluteGatePassingCandidateCount"],
            "mechanismCount": len(MECHANISMS),
            "profileCount": len({(item["mechanism"], item["profileId"]) for item in report["candidates"]}),
        },
        "gateFailureDiagnostics": gate_diagnostics,
        "episodeDiagnostics": episode_diagnostics,
        "profileDiagnostics": profile_diagnostics,
        "persistenceDiagnostics": persistence_diagnostics,
        "mechanismConclusions": conclusions,
        "globalConclusion": {
            "allCandidatesHaveZeroWorstEpisodeRecall": all_worst_zero,
            "hardNegativeAlertGateFailureCount": hard_negative_gate_failure_count,
            "thresholdRangeGateFailureCount": threshold_range_failure_count,
            "dominantFailure": "positive-cross-episode-generalization",
            "falseAlarmControlIsDominantFailure": False,
            "thresholdInstabilityIsDominantFailure": False,
            "existingCandidateFamilyExhaustedUnderFrozenProtocol": True,
            "evidenceSupportsGateRelaxation": False,
            "evidenceSupportsThresholdRetuning": False,
            "evidenceSupportsRelativeRankingRescue": False,
            "evidenceSupportsNewInformationHypothesis": True,
        },
        "decision": {
            "existingCandidateFamilyClosedNoGo": True,
            "newInformationHypothesisRequired": True,
            "newInformationHypothesisDesignAuthorized": True,
            "taxonomyMutationAuthorized": False,
            "featureFoundationMaterializationAuthorized": False,
            "candidateGenerationAuthorized": False,
            "candidateFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "candidateRankingAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "protocol": {
            "thresholdsRetuned": False,
            "absoluteGatesRelaxed": False,
            "candidatesReevaluated": False,
            "rankingPerformed": False,
            "shortlistProduced": False,
            "crossMechanismCompositionPerformed": False,
            "outerFeatureRowCountUsed": 0,
            "promotionPerformed": False,
        },
        "implementation": {
            "module": "regime_eval.e14_no_go_diagnostic",
            "sourceSha256": _sha(Path(__file__).read_bytes()),
        },
    }
    return _write_new(output_path, payload)


def _gate_failures(report: dict[str, Any]) -> dict[str, Any]:
    by_mechanism = {}
    overall = Counter()
    for mechanism in MECHANISMS:
        counts = Counter()
        candidates = [item for item in report["candidates"] if item["mechanism"] == mechanism]
        for candidate in candidates:
            for gate, passed in candidate["absoluteGateChecks"].items():
                if not passed:
                    counts[gate] += 1
                    overall[gate] += 1
        by_mechanism[mechanism] = {
            "candidateCount": len(candidates),
            "failureCountByGate": dict(sorted(counts.items())),
            "universallyFailedGates": sorted(gate for gate, count in counts.items() if count == len(candidates)),
        }
    return {"overallFailureCountByGate": dict(sorted(overall.items())), "byMechanism": by_mechanism}


def _episode_diagnostics(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    output = {}
    for mechanism in MECHANISMS:
        grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
        for candidate in (item for item in report["candidates"] if item["mechanism"] == mechanism):
            for fold in candidate["folds"]:
                grouped[fold["heldOutPositiveEpisodeId"]].append((candidate, fold))
        diagnostics = []
        for episode_id, rows in sorted(grouped.items()):
            recalls = [float(fold["heldOutRecall"] or 0.0) for _, fold in rows]
            hit_profiles = sorted({candidate["profileId"] for candidate, fold in rows if fold["heldOutHit"]})
            diagnostics.append({
                "episodeId": episode_id,
                "candidateCount": len(rows),
                "candidateHitCount": sum(fold["heldOutHit"] for _, fold in rows),
                "candidateHitRate": round(sum(fold["heldOutHit"] for _, fold in rows) / len(rows), 8),
                "meanRecallAcrossCandidates": round(fmean(recalls), 8),
                "maximumRecallAcrossCandidates": round(max(recalls), 8),
                "hitProfileIds": hit_profiles,
                "missedByEveryCandidate": not hit_profiles,
            })
        output[mechanism] = diagnostics
    return output


def _profile_diagnostics(report: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = {
        item["candidateId"]: [binding["seriesId"] for binding in item["featureBindings"]]
        for item in manifest["candidates"]
    }
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for candidate in report["candidates"]:
        grouped[(candidate["mechanism"], candidate["profileId"])].append(candidate)
    output = []
    for (mechanism, profile), candidates in sorted(grouped.items()):
        best = max(candidates, key=lambda item: (
            float(item["aggregate"]["episodeHitRate"]),
            float(item["aggregate"]["meanEpisodeRecall"] or 0.0),
            -float(item["aggregate"]["hardNegativeAlertRate"]),
        ))
        output.append({
            "mechanism": mechanism,
            "profileId": profile,
            "seriesIds": bindings[best["candidateId"]],
            "singleFeatureProfile": len(bindings[best["candidateId"]]) == 1,
            "candidateCount": len(candidates),
            "passingCandidateCount": sum(item["absoluteGatePassed"] for item in candidates),
            "meanEpisodeHitRateAcrossCandidates": round(fmean(float(item["aggregate"]["episodeHitRate"]) for item in candidates), 8),
            "bestCandidateId": best["candidateId"],
            "bestEpisodeHitRate": best["aggregate"]["episodeHitRate"],
            "bestMeanEpisodeRecall": best["aggregate"]["meanEpisodeRecall"],
            "bestWorstEpisodeRecall": best["aggregate"]["worstEpisodeRecall"],
            "bestHardNegativeAlertRate": best["aggregate"]["hardNegativeAlertRate"],
        })
    return output


def _persistence_diagnostics(report: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for item in report["candidates"]:
        grouped[(item["mechanism"], item["persistence"]["entryPersistenceMonths"],
                 item["persistence"]["recoveryPersistenceMonths"])].append(item)
    return [
        {
            "mechanism": mechanism, "entryPersistenceMonths": entry,
            "recoveryPersistenceMonths": recovery, "candidateCount": len(items),
            "meanEpisodeHitRate": round(fmean(float(item["aggregate"]["episodeHitRate"]) for item in items), 8),
            "meanEpisodeRecall": round(fmean(float(item["aggregate"]["meanEpisodeRecall"] or 0.0) for item in items), 8),
            "passingCandidateCount": sum(item["absoluteGatePassed"] for item in items),
        }
        for (mechanism, entry, recovery), items in sorted(grouped.items())
    ]


def _mechanism_conclusions(
    report: dict[str, Any], episodes: dict[str, list[dict[str, Any]]],
    profiles: list[dict[str, Any]], gates: dict[str, Any],
) -> dict[str, Any]:
    output = {}
    diagnosis = {
        "banking-credit": "partial-single-feature-signal-with-one-or-more-total-episode-misses",
        "broad-market-repricing": "existing-vix-baa10y-profile-family-lacks-cross-episode-separability",
        "cross-border-growth": "single-feature-absolute-fx-change-is-partial-and-not-mechanism-sufficient",
        "funding-liquidity": "fedfunds-minus-tbill-state-proxy-does-not-detect-the-frozen-positive-episodes",
    }
    requirement = {
        "banking-credit": "preregister complementary solvency-credit-deterioration and event-intensity signatures",
        "broad-market-repricing": "preregister orthogonal breadth-liquidity-and-price-dislocation signatures beyond vix-and-baa10y",
        "cross-border-growth": "preregister joint external-demand-funding-and-fx-dislocation signatures",
        "funding-liquidity": "replace the standalone level proxy with preregistered funding-spread-and-market-function signatures",
    }
    for mechanism in MECHANISMS:
        mechanism_candidates = [item for item in report["candidates"] if item["mechanism"] == mechanism]
        best = max(mechanism_candidates, key=lambda item: float(item["aggregate"]["episodeHitRate"]))
        mechanism_profiles = [item for item in profiles if item["mechanism"] == mechanism]
        output[mechanism] = {
            "bestCandidateId": best["candidateId"],
            "bestEpisodeHitRate": best["aggregate"]["episodeHitRate"],
            "bestWorstEpisodeRecall": best["aggregate"]["worstEpisodeRecall"],
            "bestHardNegativeAlertRate": best["aggregate"]["hardNegativeAlertRate"],
            "profileCount": len(mechanism_profiles),
            "allProfilesSingleFeature": all(item["singleFeatureProfile"] for item in mechanism_profiles),
            "episodesMissedByEveryCandidate": [item["episodeId"] for item in episodes[mechanism] if item["missedByEveryCandidate"]],
            "universallyFailedGates": gates["byMechanism"][mechanism]["universallyFailedGates"],
            "diagnosis": diagnosis[mechanism],
            "nextHypothesisRequirement": requirement[mechanism],
            "existingCandidateFamilyClosed": True,
        }
    return output


def _validate(
    contract: dict[str, Any], taxonomy: dict[str, Any], manifest: dict[str, Any],
    protocol: dict[str, Any], prereg: dict[str, Any], prereg_audit: dict[str, Any],
    report: dict[str, Any], schema: dict[str, Any], hashes: dict[str, str],
) -> None:
    auth = {
        "noGoDiagnosticAuthorized": True,
        "newInformationHypothesisDesignAuthorizedOnNoGo": True,
        "taxonomyMutationAuthorized": False,
        "featureFoundationMaterializationAuthorized": False,
        "candidateGenerationAuthorized": False,
        "candidateFittingAuthorized": False,
        "candidateEvaluationAuthorized": False,
        "candidateRankingAuthorized": False,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    if (
        contract.get("contractId") != "e14-loeo-no-go-diagnostic-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("authorizationPolicy") != auth
        or contract.get("expectedStatus") != STATUS
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or manifest.get("candidateCount") != contract.get("expectedCandidateCount")
        or manifest.get("candidateIds") != protocol.get("candidateIds")
        or protocol.get("protocolId") != "e14-four-detector-candidate-generation-protocol-v2"
        or prereg.get("preregistrationId") != "e14-four-detector-loeo-preregistration-v2"
        or prereg_audit.get("inventory", {}).get("candidateFoldAssignmentCount") != contract.get("expectedFoldCount")
        or report.get("status") != "INNER_LOEO_V2_EVALUATED_ABSOLUTE_GATES_APPLIED_OUTER_OOS_CLOSED"
        or report.get("inventory", {}).get("candidateCount") != contract.get("expectedCandidateCount")
        or report.get("inventory", {}).get("foldAssignmentCount") != contract.get("expectedFoldCount")
        or report.get("inventory", {}).get("absoluteGatePassingCandidateCount") != contract.get("expectedPassingCandidateCount")
        or report.get("decision", {}).get("withinMechanismRankingAuthorized") is not False
        or report.get("decision", {}).get("outerOosAuthorized") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-loeo-no-go-diagnostic-v1.json"
    ):
        raise DatasetValidationError("E14 no-go diagnostic inputs or governance are invalid.")


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
        raise DatasetValidationError(f"Immutable E14 no-go diagnostic already exists: '{destination}'.") from exc
    return destination
