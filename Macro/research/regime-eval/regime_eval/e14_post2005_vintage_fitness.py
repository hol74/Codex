from __future__ import annotations

import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError


READY = "POST_2005_ALL_FAMILIES_VINTAGE_FIT_TRANSFORMATION_GATE_AUTHORIZED"
PARTIAL = "POST_2005_PARTIAL_VINTAGE_FITNESS_REMEDIATION_REQUIRED"


def write_e14_post2005_vintage_fitness_audit(
    contract_path: str | Path,
    snapshot_index_path: str | Path,
    acquisition_audit_path: str | Path,
    scope_plan_path: str | Path,
    fitness_plan_path: str | Path,
    fitness_schema_path: str | Path,
    snapshot_root: str | Path,
    output_path: str | Path,
) -> Path:
    labels = ("fitness contract", "snapshot index", "acquisition audit", "scope plan", "fitness plan", "fitness schema")
    paths = (contract_path, snapshot_index_path, acquisition_audit_path, scope_plan_path, fitness_plan_path, fitness_schema_path)
    artifacts = [_read(path, label) for path, label in zip(paths, labels)]
    (_, _, contract), (_, index_raw, index), (_, acquisition_raw, acquisition), (_, scope_raw, scope), (_, plan_raw, plan), (_, schema_raw, schema) = artifacts
    actual_hashes = {"snapshotIndexSha256": _sha(index_raw), "acquisitionAuditSha256": _sha(acquisition_raw), "scopeFeasibilityPlanSha256": _sha(scope_raw), "fitnessPlanSha256": _sha(plan_raw), "fitnessSchemaSha256": _sha(schema_raw)}
    _validate_inputs(contract, index, acquisition, scope, plan, schema, actual_hashes)

    root = Path(snapshot_root).resolve()
    indexed = index["artifacts"]
    for item in indexed:
        path = _inside(root, item["relativePath"])
        raw = path.read_bytes()
        if _sha(raw) != item["sha256"] or len(raw) != item["sizeBytes"]:
            raise DatasetValidationError(f"E14.7l artifact hash mismatch: {item['relativePath']}")

    by_source: dict[str, list[dict[str, Any]]] = {}
    for item in indexed:
        by_source.setdefault(item["sourceId"], []).append(item)
    source_assessments = []
    fred_lag_limits = plan["fredInitialReleaseMaximumLagDaysBySource"]
    for source_id in contract["expectedSourceIds"]:
        items = by_source[source_id]
        if source_id.startswith("fred-"):
            assessment = _fred_assessment(root, source_id, items, fred_lag_limits[source_id])
        elif source_id == "fdic-qbp-archive":
            assessment = _fdic_assessment(root, source_id, items)
        else:
            assessment = _sdmx_assessment(root, source_id, items)
        source_assessments.append(assessment)

    source_map = {item["sourceId"]: item for item in source_assessments}
    families = []
    for policy in plan["familyPolicies"]:
        assessments = [source_map[source_id] for source_id in policy["sourceIds"]]
        coverage_failures = _coverage_failures(policy, assessments)
        event_failures = [item["sourceId"] for item in assessments if not item["eventTimeFit"]]
        history_months = min(_history_months(item["coverageStart"], item["coverageEnd"]) for item in assessments)
        scope_family = next(item for item in scope["post2005FeatureFamilies"] if item["familyId"] == policy["familyId"])
        episode_months = plan["positiveEpisodeFirstMonthById"]
        pre_episode_lookbacks = [
            min(_months_before(item["coverageStart"], episode_months[episode_id]) for item in assessments)
            for episode_id in scope_family["applicablePositiveEpisodeIds"]
        ]
        minimum_pre_episode_lookback = min(pre_episode_lookbacks)
        history_complete = history_months >= policy["minimumHistoryMonths"] and minimum_pre_episode_lookback >= policy["minimumHistoryMonths"]
        ready = not coverage_failures and not event_failures and history_complete
        families.append({
            "familyId": policy["familyId"], "mechanism": policy["mechanism"],
            "sourceIds": policy["sourceIds"], "coverageComplete": not coverage_failures,
            "eventTimeFit": not event_failures, "historySpanMonths": history_months,
            "minimumPreEpisodeLookbackMonths": minimum_pre_episode_lookback,
            "minimumHistoryMonths": policy["minimumHistoryMonths"], "historyComplete": history_complete,
            "vintageFit": ready,
            "coverageFailures": coverage_failures, "eventTimeFailures": event_failures,
            "status": "VINTAGE_FIT" if ready else "VINTAGE_REMEDIATION_REQUIRED",
        })

    all_ready = all(item["vintageFit"] for item in families)
    status = READY if all_ready else PARTIAL
    output = Path(output_path).resolve()
    if output.exists():
        raise DatasetValidationError("Immutable E14.7l vintage-fitness audit already exists.")
    payload = {
        "schemaVersion": 1,
        "artifactType": "E14Post2005VintageFitnessAudit",
        "status": status,
        "inputs": {name: _artifact(file, raw) for name, (file, raw, _) in zip(("fitnessContract", "snapshotIndex", "acquisitionAudit", "scopeFeasibilityPlan", "fitnessPlan", "fitnessSchema"), artifacts)},
        "inventory": {"sourceCount": len(source_assessments), "familyCount": len(families), "vintageFitFamilyCount": sum(item["vintageFit"] for item in families), "blockedFamilyCount": sum(not item["vintageFit"] for item in families), "artifactCount": len(indexed), "fredObservationCount": sum(item.get("observationCount", 0) for item in source_assessments if item["sourceId"].startswith("fred-"))},
        "sourceAssessments": source_assessments,
        "familyAssessments": families,
        "checks": {"allInputHashesExact": True, "allArtifactHashesVerified": True, "allContainersIntegrityChecked": all(item["containerIntegrity"] for item in source_assessments), "fredDatesUniquePerSeries": all(item.get("duplicateObservationDateCount", 0) == 0 for item in source_assessments if item["sourceId"].startswith("fred-")), "fredIndexMetadataReconciled": all(item.get("indexMetadataReconciled", True) for item in source_assessments), "fredRealtimeChunksValid": all(item.get("realtimeChunksValid", True) for item in source_assessments), "fredReleaseLagsValid": all(item.get("releaseLagsValid", True) for item in source_assessments), "rawOnlyNeverTreatedAsEventTimeFit": all(item["eventTimeFit"] is False for item in source_assessments if item["rawOnlyArtifactCount"] > 0), "allMinimumHistoryRequirementsMetForReadyFamilies": all(item["historyComplete"] for item in families if item["vintageFit"]), "globalTransformationRequiresAllFamilies": all_ready == all(item["vintageFit"] for item in families)},
        "protocol": {"observationValuesUsedForFeatures": 0, "featuresTransformed": 0, "candidatesGenerated": 0, "evaluationPerformed": False, "outerOosRead": False},
        "decision": {"allFamiliesVintageFit": all_ready, "readyMechanisms": [item["mechanism"] for item in families if item["vintageFit"]], "blockedMechanisms": [item["mechanism"] for item in families if not item["vintageFit"]], "featureTransformationAuthorized": all_ready, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False, "nextAllowedAction": contract["nextActionIfAllReady"] if all_ready else contract["nextActionIfPartial"]},
        "implementation": {"module": "regime_eval.e14_post2005_vintage_fitness", "sourceSha256": _sha(Path(__file__).read_bytes())},
    }
    _validate_schema_instance(payload, schema)
    if payload["decision"]["featureTransformationAuthorized"] != all(item["vintageFit"] for item in families):
        raise DatasetValidationError("E14.7l transformation decision is inconsistent with family fitness.")
    return _write(output, _json_bytes(payload))


def _fred_assessment(root: Path, source_id: str, items: list[dict[str, Any]], maximum_lag_days: int) -> dict[str, Any]:
    observations = []
    chunks = []
    for item in sorted(items, key=lambda value: value["realtimeChunk"]):
        payload = json.loads(_inside(root, item["relativePath"]).read_bytes())
        chunk = item["realtimeChunk"]
        chunks.append(chunk)
        chunk_observations = payload.get("observations", [])
        if (
            payload.get("realtime_start") != chunk[0]
            or payload.get("realtime_end") != chunk[1]
            or payload.get("observation_start") != "2006-01-01"
            or payload.get("observation_end") != "2025-12-31"
            or payload.get("output_type") != 4
            or payload.get("offset") != 0
            or payload.get("count") != len(chunk_observations)
            or not isinstance(payload.get("limit"), int)
            or len(chunk_observations) >= payload["limit"]
            or len(chunk_observations) != item["observationCount"]
            or min(value["date"] for value in chunk_observations) != item["observationStart"]
            or max(value["date"] for value in chunk_observations) != item["observationEnd"]
        ):
            raise DatasetValidationError(f"E14.7l FRED payload disagrees with frozen index: {item['relativePath']}")
        for observation in chunk_observations:
            try:
                observed = date.fromisoformat(observation["date"])
                realtime_start = date.fromisoformat(observation["realtime_start"])
                realtime_end = date.fromisoformat(observation["realtime_end"])
            except (KeyError, TypeError, ValueError) as error:
                raise DatasetValidationError(f"E14.7l invalid FRED ISO date: {source_id}") from error
            if not (chunk[0] <= observation["realtime_start"] <= chunk[1] and chunk[0] <= observation["realtime_end"] <= chunk[1]):
                raise DatasetValidationError(f"E14.7l FRED realtime date escapes chunk: {source_id}")
            if observed > realtime_start or realtime_end < realtime_start or (realtime_start - observed).days > maximum_lag_days:
                raise DatasetValidationError(f"E14.7l invalid FRED initial-release chronology: {source_id}")
            observations.append(observation)
    for previous, current in zip(chunks, chunks[1:]):
        if date.fromisoformat(current[0]) != date.fromisoformat(previous[1]) + timedelta(days=1):
            raise DatasetValidationError(f"E14.7l FRED realtime chunks are not contiguous: {source_id}")
    dates = [item["date"] for item in observations]
    vintages = [item["realtime_start"] for item in observations]
    duplicates = len(dates) - len(set(dates))
    event_time_fit = duplicates == 0 and all(item["usageBoundary"].startswith("event-time") for item in items)
    return {"sourceId": source_id, "artifactCount": len(items), "rawOnlyArtifactCount": sum(item["usageBoundary"].startswith("raw-only") for item in items), "containerIntegrity": True, "coverageStart": min(dates), "coverageEnd": max(dates), "vintageStart": min(vintages), "vintageEnd": max(vintages), "observationCount": len(observations), "duplicateObservationDateCount": duplicates, "maximumReleaseLagDays": max((date.fromisoformat(item["realtime_start"]) - date.fromisoformat(item["date"])).days for item in observations), "indexMetadataReconciled": True, "realtimeChunksValid": True, "releaseLagsValid": True, "eventTimeFit": event_time_fit, "blockingReasons": [] if event_time_fit else ["duplicate-initial-release-observation-dates"]}


def _sdmx_assessment(root: Path, source_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    archive_item = next(item for item in items if item["relativePath"].endswith(".zip"))
    path = _inside(root, archive_item["relativePath"])
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise DatasetValidationError(f"E14.7l corrupt SDMX archive: {source_id}")
        data_name = next(name for name in archive.namelist() if name.endswith("_data.xml"))
        coverage_start: str | None = None
        coverage_end: str | None = None
        observation_count = 0
        series_count = 0
        with archive.open(data_name) as stream:
            for _, element in ET.iterparse(stream, events=("start",)):
                tag = element.tag.rsplit("}", 1)[-1]
                if tag == "Series":
                    series_count += 1
                elif tag == "Obs" and element.attrib.get("TIME_PERIOD"):
                    period = element.attrib["TIME_PERIOD"]
                    coverage_start = period if coverage_start is None or period < coverage_start else coverage_start
                    coverage_end = period if coverage_end is None or period > coverage_end else coverage_end
                    observation_count += 1
                element.clear()
    if coverage_start is None or coverage_end is None:
        raise DatasetValidationError(f"E14.7l SDMX archive has no dated observations: {source_id}")
    raw_only = sum(item["usageBoundary"].startswith("raw-only") for item in items)
    return {"sourceId": source_id, "artifactCount": len(items), "rawOnlyArtifactCount": raw_only, "containerIntegrity": True, "coverageStart": coverage_start, "coverageEnd": coverage_end, "seriesCount": series_count, "observationCount": observation_count, "eventTimeFit": raw_only == 0, "blockingReasons": ["current-bulk-package-does-not-preserve-release-level-vintages"] if raw_only else []}


def _fdic_assessment(root: Path, source_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    quarters = []
    for item in items:
        if not item["relativePath"].endswith(".xlsx"):
            continue
        path = _inside(root, item["relativePath"])
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise DatasetValidationError("E14.7l corrupt FDIC workbook.")
            for name in archive.namelist():
                if name.endswith(".xml"):
                    quarters.extend(re.findall(r"(?:19|20)\d{2}Q[1-4]", archive.read(name).decode("utf-8", errors="ignore")))
    unique = sorted(set(quarters))
    if not unique:
        raise DatasetValidationError("E14.7l FDIC workbook has no quarter headers.")
    raw_only = sum(item["usageBoundary"].startswith("raw-only") for item in items)
    return {"sourceId": source_id, "artifactCount": len(items), "rawOnlyArtifactCount": raw_only, "containerIntegrity": True, "coverageStart": _quarter_start(unique[0]), "coverageEnd": _quarter_end(unique[-1]), "quarterCount": len(unique), "eventTimeFit": False, "blockingReasons": ["archived-spreadsheets-end-before-2025", "quarter-publication-vintages-not-preserved"]}


def _coverage_failures(policy: dict[str, Any], assessments: list[dict[str, Any]]) -> list[str]:
    failures = []
    by_id = {item["sourceId"]: item for item in assessments}
    if "coverageStartRequired" in policy:
        failures.extend(item["sourceId"] for item in assessments if item["coverageStart"] > policy["coverageStartRequired"] or item["coverageEnd"] < policy["coverageEndRequired"])
    elif "coverageStartTolerance" in policy:
        failures.extend(item["sourceId"] for item in assessments if item["vintageStart"] > policy["coverageStartTolerance"] or item["coverageEnd"] < policy["coverageEndTolerance"])
    else:
        failures.extend(item["sourceId"] for item in assessments if item["vintageStart"] > policy["coverageStartToleranceBySource"][item["sourceId"]] or item["coverageEnd"] < policy["coverageEndTolerance"])
    return sorted(set(failures))


def _history_months(start: str, end: str) -> int:
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    return (last.year - first.year) * 12 + last.month - first.month + 1


def _months_before(start: str, episode_first_month: str) -> int:
    first = date.fromisoformat(start)
    episode = date.fromisoformat(episode_first_month)
    return (episode.year - first.year) * 12 + episode.month - first.month


def _validate_inputs(contract: dict[str, Any], index: dict[str, Any], acquisition: dict[str, Any], scope: dict[str, Any], plan: dict[str, Any], schema: dict[str, Any], actual_hashes: dict[str, str]) -> None:
    policies = plan.get("familyPolicies", [])
    scope_families = {item["familyId"]: item for item in scope.get("post2005FeatureFamilies", [])}
    expected_decision_policy = {
        "hashMismatchFailsClosed": True,
        "coverageFailureBlocksFamily": True,
        "rawOnlyUsageBlocksEventTimeFitness": True,
        "familyFailureBlocksGlobalTransformation": True,
        "auditCannotTransformValues": True,
        "auditCannotGenerateCandidates": True,
    }
    expected_fitness_policy = {
        "allArtifactHashesMustMatch": True,
        "allContainersMustPassIntegrityTest": True,
        "fredDatesMustBeUniquePerSeries": True,
        "fredRealtimeDatesMustRemainInsideFrozenChunks": True,
        "fredPayloadMustReconcileWithFrozenIndex": True,
        "fredInitialReleaseChronologyMustPass": True,
        "rawOnlyPayloadCannotProveEventTimeFitness": True,
        "allSourcesInFamilyMustPass": True,
        "minimumHistoryMustPass": True,
        "globalTransformationRequiresAllFourFamilies": True,
    }
    lag_limits = plan.get("fredInitialReleaseMaximumLagDaysBySource")
    episode_months = plan.get("positiveEpisodeFirstMonthById")
    if (
        contract.get("contractId") != "e14-post2005-vintage-fitness-audit-contract-v1"
        or contract.get("inputHashes") != actual_hashes
        or contract.get("decisionPolicy") != expected_decision_policy
        or index.get("status") != "POST_2005_RAW_SOURCE_SNAPSHOT_ACQUIRED_TRANSFORMATION_GATE_REQUIRED"
        or acquisition.get("decision", {}).get("rawSnapshotComplete") is not True
        or acquisition.get("outputs", {}).get("snapshotIndex", {}).get("sha256") != actual_hashes["snapshotIndexSha256"]
        or plan.get("planId") != "e14-post2005-vintage-fitness-audit-plan-v1"
        or len(policies) != 4 or [item.get("mechanism") for item in policies] != contract.get("expectedMechanisms")
        or any(item.get("familyId") not in scope_families or item.get("sourceIds") != scope_families[item["familyId"]].get("sourceIds") or item.get("minimumHistoryMonths") != scope_families[item["familyId"]].get("minimumHistoryMonths") for item in policies)
        or {item.get("sourceId") for item in index.get("artifacts", [])} != set(contract.get("expectedSourceIds", []))
        or plan.get("fitnessPolicy") != expected_fitness_policy
        or lag_limits != {"fred-dgs2": 10, "fred-dgs10": 10, "fred-dcpf3m": 45, "fred-dtb3": 10}
        or episode_months != {"china-eme-stress-2015-2016": "2015-08-01", "euro-sovereign-stress-2011": "2011-09-01", "regional-bank-stress-2023": "2023-03-01", "repo-stress-2019": "2019-09-01", "risk-repricing-2018q4": "2018-10-01", "taper-tantrum-2013": "2013-05-01"}
        or plan.get("authorizationPolicy") != {"auditAuthorized": True, "featureTransformationAuthorized": False, "candidateGenerationAuthorized": False, "evaluationAuthorized": False, "outerOosAuthorized": False}
        or schema.get("$id") != "https://macro-regime.local/schemas/e14-post2005-vintage-fitness-audit-v1.json"
    ):
        raise DatasetValidationError("E14.7l vintage-fitness inputs are invalid.")


def _validate_schema_instance(value: Any, schema: dict[str, Any], path: str = "$", root_schema: dict[str, Any] | None = None) -> None:
    root_schema = schema if root_schema is None else root_schema
    if "$ref" in schema:
        if schema["$ref"] != "#/$defs/artifact":
            raise DatasetValidationError(f"E14.7l unsupported schema reference at {path}.")
        schema = root_schema["$defs"]["artifact"]
    if "const" in schema and value != schema["const"]:
        raise DatasetValidationError(f"E14.7l schema const violation at {path}.")
    if "enum" in schema and value not in schema["enum"]:
        raise DatasetValidationError(f"E14.7l schema enum violation at {path}.")
    expected_type = schema.get("type")
    type_matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }
    if expected_type and not type_matches.get(expected_type, True):
        raise DatasetValidationError(f"E14.7l schema type violation at {path}.")
    if isinstance(value, dict):
        required = set(schema.get("required", []))
        if not required.issubset(value):
            raise DatasetValidationError(f"E14.7l schema required-property violation at {path}.")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and not set(value).issubset(properties):
            raise DatasetValidationError(f"E14.7l schema additional-property violation at {path}.")
        for key, child in value.items():
            if key in properties:
                _validate_schema_instance(child, properties[key], f"{path}.{key}", root_schema)
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            raise DatasetValidationError(f"E14.7l schema item-count violation at {path}.")
        if "items" in schema:
            for index, child in enumerate(value):
                _validate_schema_instance(child, schema["items"], f"{path}[{index}]", root_schema)


def _quarter_start(value: str) -> str:
    year, quarter = int(value[:4]), int(value[-1])
    return f"{year:04d}-{(quarter - 1) * 3 + 1:02d}-01"


def _quarter_end(value: str) -> str:
    year, quarter = int(value[:4]), int(value[-1])
    return f"{year:04d}-{quarter * 3:02d}-{'30' if quarter in {2, 3} else '31'}"


def _inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise DatasetValidationError("E14.7l artifact path escapes snapshot root.") from error
    return path


def _read(path: str | Path, label: str) -> tuple[Path, bytes, dict[str, Any]]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7l {label} is not valid JSON: {source}") from error


def _artifact(path: Path, raw: bytes) -> dict[str, Any]:
    return {"fileName": path.name, "sha256": _sha(raw), "sizeBytes": len(raw)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write(path: Path, raw: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise DatasetValidationError(f"Immutable E14.7l output exists: {path}") from error
    return path
