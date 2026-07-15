from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "INNER_LOEO_PREREGISTERED_STRUCTURAL_COVERAGE_BLOCKED"
MECHANISMS = [
    "banking-credit",
    "broad-market-repricing",
    "cross-border-growth",
    "funding-liquidity",
]


def write_e14_loeo_preregistration_audit(
    contract_path: str | Path,
    taxonomy_path: str | Path,
    candidate_manifest_path: str | Path,
    foundation_path: str | Path,
    foundation_lock_path: str | Path,
    candidate_protocol_path: str | Path,
    preregistration_path: str | Path,
    preregistration_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_raw, contract = _read(contract_path, "readiness contract")
    taxonomy_file, taxonomy_raw, taxonomy = _read(taxonomy_path, "taxonomy v5")
    manifest_file, manifest_raw, manifest = _read(candidate_manifest_path, "candidate manifest")
    foundation_file, foundation_raw, foundation = _read(foundation_path, "feature foundation")
    lock_file, lock_raw, lock = _read(foundation_lock_path, "feature foundation lock")
    protocol_file, protocol_raw, protocol = _read(candidate_protocol_path, "candidate protocol")
    prereg_file, prereg_raw, prereg = _read(preregistration_path, "LOEO preregistration")
    schema_file, schema_raw, schema = _read(preregistration_schema_path, "LOEO preregistration schema")
    _validate_inputs(
        contract, taxonomy, manifest, foundation, lock, protocol, prereg, schema,
        taxonomy_raw, manifest_raw, foundation_raw, lock_raw, protocol_raw,
        prereg_raw, schema_raw,
    )

    label_inventory = _label_inventory(taxonomy)
    if label_inventory != contract["expectedLabelEpisodeCounts"]:
        raise DatasetValidationError("E14 LOEO label inventory differs from the frozen readiness contract.")

    series_ranges = _series_ranges(foundation, prereg["temporalPolicy"]["minimumHistoryMonths"])
    positive_by_mechanism = _episodes_by_mechanism(taxonomy["episodes"], "positive")
    negative_by_mechanism = _episodes_by_mechanism(taxonomy["hardNegativeEpisodes"], "hard-negative")
    eligibility = []
    for candidate in manifest["candidates"]:
        mechanism = candidate["mechanism"]
        series_ids = [item["seriesId"] for item in candidate["featureBindings"]]
        observable_positive = _observable_ids(positive_by_mechanism[mechanism], series_ids, series_ranges)
        observable_negative = _observable_ids(negative_by_mechanism[mechanism], series_ids, series_ranges)
        positive_ready = len(observable_positive) >= prereg["eligibilityPolicy"]["minimumObservablePositiveEpisodes"]
        negative_ready = len(observable_negative) >= prereg["eligibilityPolicy"]["minimumObservableHardNegativeEpisodes"]
        eligible = positive_ready and negative_ready
        eligibility.append({
            "candidateId": candidate["candidateId"],
            "mechanism": mechanism,
            "profileId": candidate["profile"]["profileId"],
            "seriesIds": series_ids,
            "observablePositiveEpisodeIds": observable_positive,
            "observablePositiveEpisodeCount": len(observable_positive),
            "observableHardNegativeEpisodeIds": observable_negative,
            "observableHardNegativeEpisodeCount": len(observable_negative),
            "plannedLeaveOneOutFoldCount": len(observable_positive) if eligible else 0,
            "structurallyEligible": eligible,
            "reason": None if eligible else _reason(positive_ready, negative_ready),
        })

    eligible_counts = dict(sorted(Counter(
        item["mechanism"] for item in eligibility if item["structurallyEligible"]
    ).items()))
    eligible_counts = {mechanism: eligible_counts.get(mechanism, 0) for mechanism in MECHANISMS}
    if eligible_counts != contract["expectedEligibleCandidateCounts"]:
        raise DatasetValidationError("E14 LOEO structural eligibility differs from the frozen contract.")
    ready_mechanisms = [mechanism for mechanism in MECHANISMS if eligible_counts[mechanism] > 0]
    blocked_mechanisms = [mechanism for mechanism in MECHANISMS if eligible_counts[mechanism] == 0]
    full_ready = not blocked_mechanisms
    if full_ready or contract["expectedStatus"] != STATUS:
        raise DatasetValidationError("E14 LOEO expected blocked status is inconsistent with structural coverage.")

    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FourDetectorLoeoPreregistrationAudit",
        "status": STATUS,
        "inputs": {
            "readinessContract": _artifact(contract_file, contract_raw),
            "taxonomyV5": _artifact(taxonomy_file, taxonomy_raw),
            "candidateManifest": _artifact(manifest_file, manifest_raw),
            "featureFoundation": _artifact(foundation_file, foundation_raw),
            "featureFoundationLock": _artifact(lock_file, lock_raw),
            "candidateProtocol": _artifact(protocol_file, protocol_raw),
            "loeoPreregistration": _artifact(prereg_file, prereg_raw),
            "loeoPreregistrationSchema": _artifact(schema_file, schema_raw),
        },
        "labelInventory": label_inventory,
        "seriesStructuralRanges": series_ranges,
        "inventory": {
            "candidateCount": len(eligibility),
            "eligibleCandidateCount": sum(eligible_counts.values()),
            "ineligibleCandidateCount": len(eligibility) - sum(eligible_counts.values()),
            "eligibleCandidateCountByMechanism": eligible_counts,
            "labelDefinedPositiveFoldCount": sum(item["positive"] for item in label_inventory.values()),
            "eligibleCandidateFoldAssignmentCount": sum(item["plannedLeaveOneOutFoldCount"] for item in eligibility),
            "readyMechanismCount": len(ready_mechanisms),
            "blockedMechanismCount": len(blocked_mechanisms),
        },
        "candidateEligibility": eligibility,
        "checks": {
            "hashBindingsExact": True,
            "fortyCandidatesRemainImmutable": len(eligibility) == 40,
            "labelsSeparatedByMechanism": True,
            "unlabeledMonthsNotUsedAsNegatives": prereg["episodePolicy"]["unlabeledMonthsAreNotNegatives"],
            "heldOutLabelsForbidden": prereg["foldPolicy"]["heldOutLabelsForbiddenForTransformAndThresholdSelection"],
            "causalTrainOnlyTransforms": prereg["temporalPolicy"]["causalTransformsOnly"]
            and prereg["temporalPolicy"]["transformParametersFitOnTrainingOnly"],
            "minimumHistoryAppliedBeforeEpisodeObservability": True,
            "missingnessAndMethodologyBoundariesPreserved": prereg["temporalPolicy"]["missingValuesRemainExplicit"]
            and prereg["temporalPolicy"]["zeroImputationForbidden"]
            and prereg["temporalPolicy"]["crossMethodologySplicingForbidden"]
            and prereg["temporalPolicy"]["carryBeyondMethodologyCoverageEndForbidden"],
            "outerOosClosed": "Forbidden" in prereg["foldPolicy"]["outerOos"],
            "allMechanismsStructurallyReady": full_ready,
        },
        "protocol": {
            "candidateFittingPerformed": False,
            "candidateEvaluationPerformed": False,
            "candidateRankingPerformed": False,
            "shortlistProduced": False,
            "outerFeatureRowCountUsed": 0,
            "crossMechanismCompositionPerformed": False,
            "promotionPerformed": False,
        },
        "decision": {
            "preregistrationFrozen": True,
            "readyMechanisms": ready_mechanisms,
            "blockedMechanisms": blocked_mechanisms,
            "fullFourMechanismReadiness": full_ready,
            "candidateFittingAuthorized": False,
            "partialMechanismFittingAuthorized": False,
            "candidateEvaluationAuthorized": False,
            "candidateRankingAuthorized": False,
            "crossMechanismCompositionAuthorized": False,
            "outerOosAuthorized": False,
            "promotionAuthorized": False,
            "nextAllowedAction": contract["nextAllowedAction"],
        },
        "implementation": {
            "module": "regime_eval.e14_loeo_preregistration",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new(output_path, payload)


def _validate_inputs(
    contract: Any, taxonomy: Any, manifest: Any, foundation: Any, lock: Any,
    protocol: Any, prereg: Any, schema: Any, taxonomy_raw: bytes,
    manifest_raw: bytes, foundation_raw: bytes, lock_raw: bytes,
    protocol_raw: bytes, prereg_raw: bytes, schema_raw: bytes,
) -> None:
    hashes = {
        "taxonomyV5Sha256": hashlib.sha256(taxonomy_raw).hexdigest(),
        "candidateManifestSha256": hashlib.sha256(manifest_raw).hexdigest(),
        "featureFoundationSha256": hashlib.sha256(foundation_raw).hexdigest(),
        "featureFoundationLockSha256": hashlib.sha256(lock_raw).hexdigest(),
        "candidateProtocolSha256": hashlib.sha256(protocol_raw).hexdigest(),
        "loeoPreregistrationSha256": hashlib.sha256(prereg_raw).hexdigest(),
        "loeoPreregistrationSchemaSha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    auth = {
        "preregistrationAuditAuthorized": True,
        "candidateFittingAuthorizedOnFullMechanismReadiness": True,
        "partialMechanismFittingAuthorized": False,
        "candidateEvaluationAuthorizedNow": False,
        "candidateRankingAuthorizedNow": False,
        "crossMechanismCompositionAuthorized": False,
        "outerOosAuthorized": False,
        "promotionAuthorized": False,
    }
    if (
        contract.get("contractId") != "e14-four-detector-loeo-readiness-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("authorizationPolicy") != auth
        or taxonomy.get("groundTruthId") != "us-financial-stress-mechanism-aware-v5"
        or manifest.get("status") != "GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED"
        or manifest.get("candidateCount") != 40
        or manifest.get("authorizations", {}).get("candidateFittingAuthorized") is not False
        or manifest.get("authorizations", {}).get("outerOosAuthorized") is not False
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v1"
        or lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v1"
        or protocol.get("protocolId") != "e14-four-detector-candidate-generation-protocol-v1"
        or prereg.get("preregistrationId") != "e14-four-detector-loeo-preregistration-v1"
        or prereg.get("inputHashes") != {key: hashes[key] for key in prereg["inputHashes"]}
        or prereg.get("mechanisms") != MECHANISMS
        or prereg.get("scope") != "nested-inner-development-only"
        or prereg.get("thresholdSelection", {}).get("quantiles") != [0.8, 0.9, 0.95]
        or prereg.get("eligibilityPolicy", {}).get("minimumObservablePositiveEpisodes") != 3
        or prereg.get("eligibilityPolicy", {}).get("minimumObservableHardNegativeEpisodes") != 2
        or prereg.get("selectionPolicy", {}).get("shortlistProducedInThisStep") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-loeo-preregistration-v1.json"
    ):
        raise DatasetValidationError("E14 LOEO preregistration inputs or policy are invalid.")


def _label_inventory(taxonomy: dict[str, Any]) -> dict[str, dict[str, int]]:
    positive = _episodes_by_mechanism(taxonomy["episodes"], "positive")
    negative = _episodes_by_mechanism(taxonomy["hardNegativeEpisodes"], "hard-negative")
    return {
        mechanism: {
            "positive": len({item["independentEventId"] for item in positive[mechanism]}),
            "hardNegative": len({item["independentEventId"] for item in negative[mechanism]}),
        }
        for mechanism in MECHANISMS
    }


def _episodes_by_mechanism(episodes: list[dict[str, Any]], state: str) -> dict[str, list[dict[str, Any]]]:
    output = {mechanism: [] for mechanism in MECHANISMS}
    for episode in episodes:
        if episode.get("financialState") != state:
            continue
        for mechanism in episode.get("mechanisms", []):
            if mechanism in output:
                output[mechanism].append(episode)
    return output


def _series_ranges(foundation: dict[str, Any], history_months: int) -> dict[str, dict[str, str]]:
    output = {}
    for series in foundation["series"]:
        start = _period_month(series["coverageFrom"])
        end = _period_month(series["coverageTo"])
        output[series["seriesId"]] = {
            "coverageFrom": start.isoformat(),
            "matureFrom": _add_months(start, history_months).isoformat(),
            "coverageTo": end.isoformat(),
        }
    return dict(sorted(output.items()))


def _observable_ids(
    episodes: list[dict[str, Any]], series_ids: list[str], ranges: dict[str, dict[str, str]],
) -> list[str]:
    mature = max(date.fromisoformat(ranges[item]["matureFrom"]) for item in series_ids)
    coverage_end = min(date.fromisoformat(ranges[item]["coverageTo"]) for item in series_ids)
    ids = []
    for episode in episodes:
        first = date.fromisoformat(episode["firstMonth"])
        last = date.fromisoformat(episode["lastMonth"])
        if max(first, mature) <= min(last, coverage_end):
            ids.append(episode["independentEventId"])
    return sorted(set(ids))


def _reason(positive_ready: bool, negative_ready: bool) -> str:
    if not positive_ready and not negative_ready:
        return "insufficient-observable-positive-and-hard-negative-independent-episodes"
    if not positive_ready:
        return "insufficient-observable-positive-independent-episodes"
    return "insufficient-observable-hard-negative-independent-episodes"


def _period_month(value: str) -> date:
    if "Q" in value:
        year, quarter = value.split("Q", 1)
        return date(int(year), (int(quarter) - 1) * 3 + 1, 1)
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
        raise DatasetValidationError(f"Immutable E14 LOEO preregistration audit already exists: '{destination}'.") from exc
    return destination
