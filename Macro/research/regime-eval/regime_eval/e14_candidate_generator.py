from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


STATUS = "GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED"
EXPECTED_COUNTS = {
    "banking-credit": 16,
    "broad-market-repricing": 16,
    "cross-border-growth": 4,
    "funding-liquidity": 4,
}
EXPECTED_AUTHORIZATIONS = {
    "manifestGenerationAuthorized": True,
    "featureTransformationAuthorized": False,
    "candidateFittingAuthorized": False,
    "candidateEvaluationAuthorized": False,
    "candidateRankingAuthorized": False,
    "crossMechanismCompositionAuthorized": False,
    "outerOosAuthorized": False,
    "promotionAuthorized": False,
    "taxonomyMutationAuthorized": False,
}


def write_e14_candidate_manifest(
    contract_path: str | Path,
    protocol_path: str | Path,
    readiness_audit_path: str | Path,
    foundation_path: str | Path,
    foundation_lock_path: str | Path,
    manifest_schema_path: str | Path,
    output_path: str | Path,
) -> Path:
    contract_file, contract_raw, contract = _read(contract_path, "generation contract")
    protocol_file, protocol_raw, protocol = _read(protocol_path, "candidate protocol")
    readiness_file, readiness_raw, readiness = _read(readiness_audit_path, "protocol readiness audit")
    foundation_file, foundation_raw, foundation = _read(foundation_path, "feature foundation")
    lock_file, lock_raw, lock = _read(foundation_lock_path, "feature foundation lock")
    schema_file, schema_raw, schema = _read(manifest_schema_path, "candidate manifest schema")
    _validate_inputs(
        contract,
        protocol,
        readiness,
        foundation,
        lock,
        schema,
        protocol_raw,
        readiness_raw,
        foundation_raw,
        lock_raw,
        schema_raw,
    )

    bindings = {
        (item["mechanism"], item["seriesId"]): {
            "seriesId": item["seriesId"],
            "sourceId": item["sourceId"],
            "transform": item["transform"],
            "fitScope": item["fitScope"],
        }
        for item in foundation["detectorBindings"]
    }
    candidates: list[dict[str, Any]] = []
    for mechanism in sorted(protocol["detectors"]):
        grammar = protocol["detectors"][mechanism]
        for profile, entry, recovery in itertools.product(
            sorted(grammar["profiles"], key=lambda item: item["profileId"]),
            sorted(protocol["persistence"]["entryPersistenceMonths"]),
            sorted(protocol["persistence"]["recoveryPersistenceMonths"]),
        ):
            feature_bindings = [bindings[(mechanism, series_id)] for series_id in profile["seriesIds"]]
            parameters = {
                "thresholdQuantiles": protocol["thresholdSelection"]["quantiles"],
                "thresholdSelectionScope": protocol["thresholdSelection"]["scope"],
                "thresholdDirection": protocol["thresholdSelection"]["direction"],
                "minimumHistoryMonths": protocol["thresholdSelection"]["minimumHistoryMonths"],
                "entryPersistenceMonths": entry,
                "recoveryPersistenceMonths": recovery,
                "hysteresisRequired": protocol["persistence"]["hysteresisRequired"],
            }
            identity = {
                "protocolId": protocol["protocolId"],
                "mechanism": mechanism,
                "detectorId": grammar["detectorId"],
                "profile": profile,
                "featureBindings": feature_bindings,
                "parameters": parameters,
            }
            suffix = hashlib.sha256(_canonical_bytes(identity)).hexdigest()[:12]
            candidates.append(
                {
                    "candidateId": f"e14-{_slug(mechanism)}-{suffix}",
                    "mechanism": mechanism,
                    "detectorId": grammar["detectorId"],
                    "lifecycleStatus": "research-generated-not-fit",
                    "profile": profile,
                    "featureBindings": feature_bindings,
                    "parameters": parameters,
                }
            )

    counts = dict(sorted(Counter(item["mechanism"] for item in candidates).items()))
    ids = [item["candidateId"] for item in candidates]
    if counts != contract["expectedCandidateCounts"] or len(candidates) != protocol["candidateBudget"]:
        raise DatasetValidationError("E14 grammar expansion does not match the frozen candidate budget.")
    if len(ids) != len(set(ids)) or any(candidate_id.startswith("e12-") for candidate_id in ids):
        raise DatasetValidationError("E14 generated candidate IDs are not unique and phase-isolated.")

    input_artifacts = {
        "generationContract": _artifact(contract_file, contract_raw),
        "candidateProtocol": _artifact(protocol_file, protocol_raw),
        "protocolReadinessAudit": _artifact(readiness_file, readiness_raw),
        "featureFoundation": _artifact(foundation_file, foundation_raw),
        "featureFoundationLock": _artifact(lock_file, lock_raw),
        "manifestSchema": _artifact(schema_file, schema_raw),
    }
    generation_identity = {
        "inputHashes": {key: value["sha256"] for key, value in sorted(input_artifacts.items())},
        "candidateIds": ids,
    }
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14FourDetectorGeneratedCandidateManifest",
        "immutable": True,
        "status": STATUS,
        "generationId": hashlib.sha256(_canonical_bytes(generation_identity)).hexdigest()[:24],
        "inputs": input_artifacts,
        "candidateCount": len(candidates),
        "candidateCountByMechanism": counts,
        "researchBoundary": protocol["researchBoundary"],
        "authorizations": contract["authorizationPolicy"],
        "candidates": candidates,
        "implementation": {
            "module": "regime_eval.e14_candidate_generator",
            "sourceSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return _write_new(output_path, payload)


def _validate_inputs(
    contract: Any,
    protocol: Any,
    readiness: Any,
    foundation: Any,
    lock: Any,
    schema: Any,
    protocol_raw: bytes,
    readiness_raw: bytes,
    foundation_raw: bytes,
    lock_raw: bytes,
    schema_raw: bytes,
) -> None:
    hashes = {
        "candidateProtocolSha256": hashlib.sha256(protocol_raw).hexdigest(),
        "protocolReadinessAuditSha256": hashlib.sha256(readiness_raw).hexdigest(),
        "featureFoundationSha256": hashlib.sha256(foundation_raw).hexdigest(),
        "featureFoundationLockSha256": hashlib.sha256(lock_raw).hexdigest(),
        "manifestSchemaSha256": hashlib.sha256(schema_raw).hexdigest(),
    }
    generation_policy = {
        "deterministicEnumerationRequired": True,
        "candidateIdentityBoundToProtocolAndParameters": True,
        "featureBindingsMustResolveExactly": True,
        "thresholdQuantilesAreInnerSelectionOptionsNotIdentityMultiplier": True,
        "writeOnceManifestRequired": True,
        "reuseRejectedE12CandidateIdsForbidden": True,
    }
    if (
        not isinstance(contract, dict)
        or contract.get("contractId") != "e14-four-detector-candidate-manifest-contract-v1"
        or contract.get("inputHashes") != hashes
        or contract.get("expectedCandidateCounts") != EXPECTED_COUNTS
        or contract.get("generationPolicy") != generation_policy
        or contract.get("authorizationPolicy") != EXPECTED_AUTHORIZATIONS
        or contract.get("expectedStatus") != STATUS
        or protocol.get("protocolId") != "e14-four-detector-candidate-generation-protocol-v1"
        or protocol.get("candidateBudget") != 40
        or protocol.get("featureFoundationSha256") != hashes["featureFoundationSha256"]
        or protocol.get("featureFoundationLockSha256") != hashes["featureFoundationLockSha256"]
        or readiness.get("status") != "RESEARCH_CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED"
        or readiness.get("decision", {}).get("researchCandidateGenerationAuthorized") is not True
        or readiness.get("decision", {}).get("candidateEvaluationAuthorized") is not False
        or readiness.get("decision", {}).get("outerOosAuthorized") is not False
        or readiness.get("inputs", {}).get("candidateProtocol", {}).get("sha256") != hashes["candidateProtocolSha256"]
        or readiness.get("inputs", {}).get("featureFoundation", {}).get("sha256") != hashes["featureFoundationSha256"]
        or readiness.get("inputs", {}).get("featureFoundationLock", {}).get("sha256") != hashes["featureFoundationLockSha256"]
        or foundation.get("foundationId") != "e14-mechanism-feature-foundation-v1"
        or lock.get("lockId") != "e14-mechanism-feature-foundation-lock-v1"
        or lock.get("foundation", {}).get("sha256") != hashes["featureFoundationSha256"]
        or lock.get("strictVintageReady") is not False
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-four-detector-candidate-manifest-v1.json"
    ):
        raise DatasetValidationError("E14 candidate-manifest inputs or contract are invalid.")

    bindings = foundation.get("detectorBindings")
    if not isinstance(bindings, list):
        raise DatasetValidationError("E14 feature bindings are missing.")
    binding_map = {(item.get("mechanism"), item.get("seriesId")): item for item in bindings}
    for mechanism, grammar in protocol.get("detectors", {}).items():
        for profile in grammar.get("profiles", []):
            for series_id in profile.get("seriesIds", []):
                binding = binding_map.get((mechanism, series_id))
                if (
                    binding is None
                    or binding.get("detectorId") != grammar.get("detectorId")
                    or binding.get("fitScope") != "inner-only"
                    or binding.get("status") != "populated-manifested"
                ):
                    raise DatasetValidationError("E14 candidate profile does not resolve to one exact inner-only feature binding.")


def _slug(mechanism: str) -> str:
    return {
        "banking-credit": "banking",
        "broad-market-repricing": "broad",
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
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write_new(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable E14 candidate manifest already exists: '{destination}'.") from exc
    return destination
