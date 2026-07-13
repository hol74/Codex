from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class DatasetValidationError(ValueError):
    """Raised when a historical dataset violates the research data contract."""


@dataclass(frozen=True)
class HistoricalDataset:
    path: Path
    schema_version: int
    declared_from: date
    declared_to: date
    horizons_days: tuple[int, ...]
    rows: tuple[dict[str, Any], ...]
    sha256: str
    size_bytes: int

    @property
    def dates(self) -> tuple[date, ...]:
        return tuple(_parse_date(row["asOfDate"], "rows[].asOfDate") for row in self.rows)

    def manifest(self) -> dict[str, Any]:
        dates = self.dates
        symbols = sorted(
            {
                str(item["symbol"])
                for row in self.rows
                for item in row.get("marketObservations", [])
                if item.get("symbol")
            }
        )
        actual_from = dates[0] if dates else None
        actual_to = dates[-1] if dates else None
        expected_days = (self.declared_to - self.declared_from).days + 1
        return {
            "manifestVersion": 1,
            "dataset": {
                "fileName": self.path.name,
                "sha256": self.sha256,
                "sizeBytes": self.size_bytes,
                "schemaVersion": self.schema_version,
            },
            "coverage": {
                "declaredFrom": self.declared_from.isoformat(),
                "declaredTo": self.declared_to.isoformat(),
                "actualFrom": actual_from.isoformat() if actual_from else None,
                "actualTo": actual_to.isoformat() if actual_to else None,
                "rowCount": len(self.rows),
                "missingDeclaredDates": expected_days - len(self.rows),
                "calendarCoverageRatio": round(len(self.rows) / expected_days, 8),
            },
            "forwardReturnHorizonsDays": list(self.horizons_days),
            "marketSymbols": symbols,
            "pointInTimeValidation": "passed",
        }


def load_dataset(path: str | Path) -> HistoricalDataset:
    dataset_path = Path(path).resolve()
    try:
        raw_bytes = dataset_path.read_bytes()
    except OSError as exc:
        raise DatasetValidationError(f"Cannot read dataset '{dataset_path}': {exc}") from exc

    try:
        payload = json.loads(raw_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(f"Dataset '{dataset_path}' is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise DatasetValidationError("Dataset root must be a JSON object.")
    if payload.get("schemaVersion") != 1:
        raise DatasetValidationError(
            f"Unsupported schemaVersion {payload.get('schemaVersion')!r}; expected 1."
        )

    declared_from = _parse_date(payload.get("from"), "from")
    declared_to = _parse_date(payload.get("to"), "to")
    if declared_from > declared_to:
        raise DatasetValidationError("Dataset 'from' must be on or before 'to'.")

    horizons = payload.get("forwardReturnHorizonsDays")
    if not isinstance(horizons, list) or not horizons:
        raise DatasetValidationError("forwardReturnHorizonsDays must be a non-empty array.")
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in horizons):
        raise DatasetValidationError("Every forward return horizon must be a positive integer.")
    normalized_horizons = tuple(sorted(set(horizons)))

    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise DatasetValidationError("rows must be an array.")
    _validate_rows(rows, declared_from, declared_to, normalized_horizons)

    return HistoricalDataset(
        path=dataset_path,
        schema_version=1,
        declared_from=declared_from,
        declared_to=declared_to,
        horizons_days=normalized_horizons,
        rows=tuple(rows),
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        size_bytes=len(raw_bytes),
    )


def write_manifest(dataset: HistoricalDataset, output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(dataset.manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination.resolve()


def _validate_rows(
    rows: list[Any],
    declared_from: date,
    declared_to: date,
    horizons: tuple[int, ...],
) -> None:
    previous_date: date | None = None
    for index, row in enumerate(rows):
        location = f"rows[{index}]"
        if not isinstance(row, dict):
            raise DatasetValidationError(f"{location} must be an object.")
        as_of = _parse_date(row.get("asOfDate"), f"{location}.asOfDate")
        if not declared_from <= as_of <= declared_to:
            raise DatasetValidationError(f"{location}.asOfDate is outside the declared range.")
        if previous_date is not None and as_of <= previous_date:
            raise DatasetValidationError("Dataset rows must have unique, strictly increasing dates.")
        previous_date = as_of

        _validate_macro_observations(row.get("macroObservations"), as_of, location)
        _validate_market_observations(row.get("marketObservations"), as_of, location)
        _validate_forward_returns(row.get("forwardReturns"), as_of, horizons, location)


def _validate_macro_observations(value: Any, as_of: date, location: str) -> None:
    if not isinstance(value, list):
        raise DatasetValidationError(f"{location}.macroObservations must be an array.")
    for index, observation in enumerate(value):
        item_location = f"{location}.macroObservations[{index}]"
        if not isinstance(observation, dict):
            raise DatasetValidationError(f"{item_location} must be an object.")
        publication = _parse_date(observation.get("publicationDate"), f"{item_location}.publicationDate")
        availability_field = "availabilityDate" if "availabilityDate" in observation else "vintageDate"
        availability = _parse_date(observation.get(availability_field), f"{item_location}.{availability_field}")
        observed = _parse_date(observation.get("observationDate"), f"{item_location}.observationDate")
        if observed > as_of or publication > as_of or availability > as_of:
            raise DatasetValidationError(
                f"{item_location} leaks future information beyond {as_of.isoformat()}."
            )
        _decimal(observation.get("value"), f"{item_location}.value")


def _validate_market_observations(value: Any, as_of: date, location: str) -> None:
    if not isinstance(value, list):
        raise DatasetValidationError(f"{location}.marketObservations must be an array.")
    for index, observation in enumerate(value):
        item_location = f"{location}.marketObservations[{index}]"
        if not isinstance(observation, dict) or not observation.get("symbol"):
            raise DatasetValidationError(f"{item_location}.symbol is required.")
        observed = _parse_date(observation.get("observationDate"), f"{item_location}.observationDate")
        availability = _parse_date(observation.get("availabilityDate"), f"{item_location}.availabilityDate")
        if observed > as_of or availability > as_of:
            raise DatasetValidationError(
                f"{item_location} leaks future information beyond {as_of.isoformat()}."
            )
        _decimal(observation.get("value"), f"{item_location}.value")


def _validate_forward_returns(
    value: Any, as_of: date, horizons: tuple[int, ...], location: str
) -> None:
    if not isinstance(value, list):
        raise DatasetValidationError(f"{location}.forwardReturns must be an array.")
    seen: set[tuple[str, int]] = set()
    for index, item in enumerate(value):
        item_location = f"{location}.forwardReturns[{index}]"
        if not isinstance(item, dict) or not item.get("symbol"):
            raise DatasetValidationError(f"{item_location}.symbol is required.")
        horizon = item.get("horizonDays")
        if horizon not in horizons:
            raise DatasetValidationError(f"{item_location}.horizonDays is not declared by the dataset.")
        key = (str(item["symbol"]).casefold(), horizon)
        if key in seen:
            raise DatasetValidationError(f"Duplicate forward return for {key[0]} at {horizon} days.")
        seen.add(key)
        from_date = _parse_date(item.get("fromDate"), f"{item_location}.fromDate")
        to_date = _parse_date(item.get("toDate"), f"{item_location}.toDate")
        if from_date != as_of:
            raise DatasetValidationError(f"{item_location}.fromDate must equal the row asOfDate.")
        if to_date < as_of + timedelta(days=horizon):
            raise DatasetValidationError(f"{item_location}.toDate precedes its target horizon.")
        start = _decimal(item.get("startValue"), f"{item_location}.startValue")
        end = _decimal(item.get("endValue"), f"{item_location}.endValue")
        actual = _decimal(item.get("returnValue"), f"{item_location}.returnValue")
        if start == 0:
            raise DatasetValidationError(f"{item_location}.startValue cannot be zero.")
        expected = (end / start) - Decimal(1)
        if abs(expected - actual) > Decimal("0.00000001"):
            raise DatasetValidationError(f"{item_location}.returnValue is inconsistent with prices.")


def _parse_date(value: Any, location: str) -> date:
    if not isinstance(value, str):
        raise DatasetValidationError(f"{location} must be an ISO date string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetValidationError(f"{location} is not a valid ISO date.") from exc


def _decimal(value: Any, location: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise DatasetValidationError(f"{location} must be numeric.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DatasetValidationError(f"{location} must be numeric.") from exc
    if not result.is_finite():
        raise DatasetValidationError(f"{location} must be finite.")
    return result
