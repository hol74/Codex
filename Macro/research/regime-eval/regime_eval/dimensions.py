from __future__ import annotations

import math
from typing import Any

from .dataset import DatasetValidationError


DIMENSION_NAMES = {
    "growthDeterioration",
    "inflationPressure",
    "financialStress",
    "monetaryRestriction",
}


def dimension_scores(row: dict[str, Any]) -> dict[str, float]:
    raw = row.get("featureScores")
    if not isinstance(raw, list):
        raise DatasetValidationError("Dimension scoring requires featureScores.")
    features = {item.get("featureCode"): item.get("normalizedScore") for item in raw if isinstance(item, dict)}
    required = {"GROWTH_MOM", "INFL_PRESS", "RISK_APPETITE", "MONETARY_COND", "CREDIT_STRESS"}
    if set(features) != required:
        raise DatasetValidationError("Dimension scoring requires the five canonical normalized features.")
    values = {key: _score(features[key], key) for key in required}
    return {
        "growthDeterioration": round(1.0 - values["GROWTH_MOM"], 8),
        "inflationPressure": round(values["INFL_PRESS"], 8),
        "financialStress": round(
            1.0 - math.sqrt(values["RISK_APPETITE"] * values["CREDIT_STRESS"]), 8
        ),
        "monetaryRestriction": round(1.0 - values["MONETARY_COND"], 8),
    }


def _score(value: Any, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DatasetValidationError(f"Feature {code} normalized score is not numeric.")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise DatasetValidationError(f"Feature {code} normalized score must be between zero and one.")
    return numeric
