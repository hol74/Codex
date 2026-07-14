from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .dataset import DatasetValidationError, load_dataset
from .shadow import _validate_ledger, write_baseline_prediction_ledger


QUALITY_POLICY = "shadow-data-quality-v1"
REQUIRED_MACRO_SERIES = {
    "INDPRO_YOY",
    "SAHM",
    "CPI_YOY",
    "T10YIE",
    "VIX",
    "YC_10Y2Y",
    "HY_OAS",
    "CPI_YOY_3M_CHANGE",
    "YC_10Y2Y_3M_CHANGE",
}
CSHARP_SOURCE_PATHS = (
    "src/MacroRegime.Domain/Features",
    "src/MacroRegime.Domain/Regimes",
    "src/MacroRegime.Infrastructure/External/FredHistoricalDataClient.cs",
    "src/MacroRegime.Infrastructure/External/FredSeriesCatalog.cs",
    "src/MacroRegime.Infrastructure/External/HistoricalDataPopulator.cs",
    "src/MacroRegime.Infrastructure/External/HistoricalDatasetBuilder.cs",
    "src/MacroRegime.Infrastructure/External/HistoricalBaselineEvaluator.cs",
    "src/MacroRegime.Cli/Program.cs",
)


def write_shadow_preflight(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    model_config_path: str | Path,
    as_of_dates: Iterable[str],
    generated_at_utc: str,
    source_root: str | Path,
    output_path: str | Path,
) -> Path:
    dataset = load_dataset(dataset_path)
    evaluation_file, evaluation_bytes, evaluation = _read_json(evaluation_path, "baseline evaluation")
    config_file, config_bytes, config = _read_json(model_config_path, "model config")
    generated_at = _utc_datetime(generated_at_utc, "generatedAtUtc")
    requested = list(as_of_dates)
    if not requested or len(requested) != len(set(requested)):
        raise DatasetValidationError("At least one unique preflight as-of date is required.")
    requested_dates = sorted(_iso_date(value, "asOfDate") for value in requested)
    rows = {row["asOfDate"]: row for row in dataset.rows}
    evaluation_rows = {
        row["asOfDate"]: row for row in evaluation.get("rows", [])
        if isinstance(row, dict) and isinstance(row.get("asOfDate"), str)
    }
    if evaluation.get("datasetSha256") != dataset.sha256:
        raise DatasetValidationError("Baseline evaluation does not match the shadow dataset.")
    if config.get("modelVersion") != evaluation.get("modelVersion"):
        raise DatasetValidationError("Model config does not match the evaluation model version.")

    freshness: list[dict[str, Any]] = []
    for as_of in requested_dates:
        _validate_closed_month(as_of, generated_at)
        row = rows.get(as_of.isoformat())
        if row is None or as_of.isoformat() not in evaluation_rows:
            raise DatasetValidationError(f"Shadow preflight inputs do not contain {as_of.isoformat()}.")
        if row.get("forwardReturns"):
            raise DatasetValidationError("Shadow preflight dataset must not contain forward returns.")
        observations = row.get("macroObservations")
        if not isinstance(observations, list):
            raise DatasetValidationError("Shadow preflight row has no macro observations.")
        by_code: dict[str, dict[str, Any]] = {}
        for observation in observations:
            code = observation.get("seriesCode") if isinstance(observation, dict) else None
            if not isinstance(code, str) or code in by_code:
                raise DatasetValidationError("Shadow preflight macro series must be named and unique.")
            by_code[code] = observation
        missing = sorted(REQUIRED_MACRO_SERIES - set(by_code))
        if missing:
            raise DatasetValidationError(f"Shadow preflight is missing required macro series: {', '.join(missing)}.")
        for code in sorted(REQUIRED_MACRO_SERIES):
            observed = _iso_date(by_code[code].get("observationDate"), f"{code}.observationDate")
            lag = ((as_of.year - observed.year) * 12) + as_of.month - observed.month
            if lag < 0 or lag > 3:
                raise DatasetValidationError(
                    f"Shadow preflight found stale macro series '{code}' ({lag} months at {as_of})."
                )
            freshness.append({
                "asOfDate": as_of.isoformat(),
                "seriesCode": code,
                "observationDate": observed.isoformat(),
                "lagMonths": lag,
                "maximumLagMonths": 3,
                "status": "passed",
            })

    csharp_sha, csharp_files = _fingerprint_csharp_sources(source_root)
    python_sha, python_files = _fingerprint_python_sources()
    payload = {
        "schemaVersion": 1,
        "artifactType": "ShadowPreflight",
        "immutable": True,
        "status": "passed",
        "generatedAtUtc": generated_at_utc,
        "asOfDates": [value.isoformat() for value in requested_dates],
        "qualityPolicy": QUALITY_POLICY,
        "checks": {
            "completedInformationMonth": "passed",
            "pointInTimeDataset": "passed",
            "forwardReturnsAbsent": "passed",
            "requiredMacroSeries": sorted(REQUIRED_MACRO_SERIES),
            "macroFreshness": freshness,
            "outcomesAbsent": "passed",
        },
        "inputs": {
            "datasetFileName": dataset.path.name,
            "datasetSha256": dataset.sha256,
            "evaluationFileName": evaluation_file.name,
            "evaluationSha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "modelConfigFileName": config_file.name,
            "modelConfigSha256": hashlib.sha256(config_bytes).hexdigest(),
        },
        "implementation": {
            "csharpSourceSha256": csharp_sha,
            "csharpSourceFileCount": csharp_files,
            "pythonSourceSha256": python_sha,
            "pythonSourceFileCount": python_files,
        },
    }
    return _write_new_json(output_path, payload)


def ensure_shadow_ledger(
    evaluation_path: str | Path,
    dataset_path: str | Path,
    model_config_path: str | Path,
    preflight_path: str | Path,
    as_of_dates: Iterable[str],
    generated_at_utc: str,
    output_path: str | Path,
) -> Path:
    destination = Path(output_path).resolve()
    requested = sorted(as_of_dates)
    if not requested or len(requested) != len(set(requested)):
        raise DatasetValidationError("At least one unique shadow-cycle as-of date is required.")
    if not destination.exists():
        return write_baseline_prediction_ledger(
            evaluation_path,
            dataset_path,
            model_config_path,
            requested,
            generated_at_utc,
            "shadow-live",
            destination,
            preflight_path,
        )
    _, ledger_bytes, ledger = _read_json(destination, "prediction ledger")
    predictions = _validate_ledger(ledger)
    inputs = ledger["runManifest"].get("inputs", {})
    expected = {
        "datasetSha256": _file_sha(dataset_path),
        "evaluationSha256": _file_sha(evaluation_path),
        "modelConfigSha256": _file_sha(model_config_path),
        "preflightSha256": _file_sha(preflight_path),
    }
    actual_dates = [item["asOfDate"] for item in predictions]
    if (
        ledger["runManifest"].get("runMode") != "shadow-live"
        or actual_dates != requested
        or any(inputs.get(key) != value for key, value in expected.items())
        or not ledger_bytes
    ):
        raise DatasetValidationError(
            f"Existing immutable ledger conflicts with the requested shadow cycle: '{destination}'."
        )
    return destination


def write_shadow_index(ledger_directory: str | Path, output_path: str | Path) -> Path:
    directory = Path(ledger_directory).resolve()
    entries: list[dict[str, Any]] = []
    seen_dates: set[str] = set()
    for path in sorted(directory.glob("*.json"), key=lambda value: value.name):
        if path.resolve() == Path(output_path).resolve():
            continue
        try:
            raw = path.read_bytes()
            ledger = json.loads(raw)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(ledger, dict) or ledger.get("artifactType") != "PredictionLedger":
            continue
        predictions = _validate_ledger(ledger)
        if ledger["runManifest"].get("runMode") != "shadow-live":
            continue
        if len(predictions) != 1:
            raise DatasetValidationError("Each operational shadow-live ledger must contain one prediction.")
        prediction = predictions[0]
        as_of = prediction["asOfDate"]
        if as_of in seen_dates:
            raise DatasetValidationError(f"Multiple shadow-live ledgers exist for {as_of}.")
        seen_dates.add(as_of)
        entries.append({
            "asOfDate": as_of,
            "ledgerFileName": path.name,
            "ledgerSha256": hashlib.sha256(raw).hexdigest(),
            "runId": ledger["runManifest"]["runId"],
            "generatedAtUtc": ledger["runManifest"]["generatedAtUtc"],
            "modelId": ledger["model"]["modelId"],
            "modelVersion": ledger["model"]["modelVersion"],
            "operationalRegime": prediction["operationalRegime"],
            "recessionProbability": prediction["recessionProbability"],
        })
    entries.sort(key=lambda item: item["asOfDate"])
    payload = {
        "schemaVersion": 1,
        "artifactType": "ShadowIndex",
        "authoritative": False,
        "derivationPolicy": "deterministic scan of immutable shadow-live PredictionLedger files",
        "entryCount": len(entries),
        "entries": entries,
    }
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if destination.exists() and destination.read_bytes() == encoded:
        return destination
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_bytes(encoded)
    temporary.replace(destination)
    return destination


def _validate_closed_month(as_of: date, generated_at: datetime) -> None:
    next_month = date(as_of.year + (as_of.month == 12), 1 if as_of.month == 12 else as_of.month + 1, 1)
    if generated_at.date() < next_month:
        raise DatasetValidationError(
            f"Shadow information month {as_of:%Y-%m} is not complete at {generated_at.date()}."
        )


def _fingerprint_csharp_sources(source_root: str | Path) -> tuple[str, int]:
    root = Path(source_root).resolve()
    files: list[Path] = []
    for relative in CSHARP_SOURCE_PATHS:
        path = root / relative
        if path.is_dir():
            files.extend(path.rglob("*.cs"))
        elif path.is_file():
            files.append(path)
        else:
            raise DatasetValidationError(f"Required C# source path is missing: '{relative}'.")
    return _fingerprint_files(root, files)


def _fingerprint_python_sources() -> tuple[str, int]:
    root = Path(__file__).resolve().parent.parent
    return _fingerprint_files(root, list((root / "regime_eval").glob("*.py")))


def _fingerprint_files(root: Path, files: list[Path]) -> tuple[str, int]:
    digest = hashlib.sha256()
    unique = sorted({path.resolve() for path in files}, key=lambda value: value.relative_to(root).as_posix())
    if not unique:
        raise DatasetValidationError("Implementation fingerprint cannot be empty.")
    for path in unique:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), len(unique)


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise DatasetValidationError(f"Immutable artifact already exists: '{destination}'.") from exc
    return destination


def _read_json(path: str | Path, label: str) -> tuple[Path, bytes, Any]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        return source, raw, json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Cannot read valid {label} JSON '{source}'.") from exc


def _file_sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).resolve().read_bytes()).hexdigest()


def _iso_date(value: Any, location: str) -> date:
    if not isinstance(value, str):
        raise DatasetValidationError(f"{location} must be an ISO date string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid ISO date.") from exc


def _utc_datetime(value: Any, location: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DatasetValidationError(f"{location} must be an ISO UTC timestamp ending in Z.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid timestamp.") from exc
    if parsed.tzinfo != timezone.utc:
        raise DatasetValidationError(f"{location} must be UTC.")
    return parsed
