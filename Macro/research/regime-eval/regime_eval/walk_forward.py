from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Iterable


@dataclass(frozen=True)
class WalkForwardConfig:
    train_years: int = 10
    test_years: int = 2
    step_years: int = 1

    def validate(self) -> None:
        if self.train_years <= 0 or self.test_years <= 0 or self.step_years <= 0:
            raise ValueError("Walk-forward windows and step must be positive.")


@dataclass(frozen=True)
class WalkForwardFold:
    number: int
    train_from: date
    train_to: date
    test_from: date
    test_to: date
    train_row_count: int
    test_row_count: int

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        for key in ("train_from", "train_to", "test_from", "test_to"):
            value[key] = value[key].isoformat()
        return value


def build_walk_forward_plan(
    dates: Iterable[date], config: WalkForwardConfig | None = None
) -> tuple[WalkForwardFold, ...]:
    settings = config or WalkForwardConfig()
    settings.validate()
    ordered_dates = tuple(sorted(set(dates)))
    if not ordered_dates:
        return ()

    last_observed = ordered_dates[-1]
    anchor = ordered_dates[0]
    folds: list[WalkForwardFold] = []
    number = 1
    while True:
        train_from = anchor
        test_from = _add_years(train_from, settings.train_years)
        train_to = test_from - timedelta(days=1)
        test_to = _add_years(test_from, settings.test_years) - timedelta(days=1)
        if test_to > last_observed:
            break
        train_count = sum(train_from <= value <= train_to for value in ordered_dates)
        test_count = sum(test_from <= value <= test_to for value in ordered_dates)
        if train_count and test_count:
            folds.append(
                WalkForwardFold(
                    number,
                    train_from,
                    train_to,
                    test_from,
                    test_to,
                    train_count,
                    test_count,
                )
            )
            number += 1
        anchor = _add_years(anchor, settings.step_years)
    return tuple(folds)


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, month=2, day=28)

