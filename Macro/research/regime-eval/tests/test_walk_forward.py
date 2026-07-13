from __future__ import annotations

import unittest
from datetime import date

from regime_eval.walk_forward import WalkForwardConfig, build_walk_forward_plan


class WalkForwardTests(unittest.TestCase):
    def test_builds_rolling_ten_two_one_folds_without_overlap(self) -> None:
        dates = [date(year, 1, 1) for year in range(2000, 2015)]

        folds = build_walk_forward_plan(dates)

        self.assertEqual(3, len(folds))
        first = folds[0]
        self.assertEqual(date(2000, 1, 1), first.train_from)
        self.assertEqual(date(2009, 12, 31), first.train_to)
        self.assertEqual(date(2010, 1, 1), first.test_from)
        self.assertEqual(date(2011, 12, 31), first.test_to)
        self.assertLess(first.train_to, first.test_from)
        self.assertEqual(date(2001, 1, 1), folds[1].train_from)

    def test_returns_no_fold_when_coverage_is_shorter_than_twelve_years(self) -> None:
        dates = [date(year, 1, 1) for year in range(2000, 2011)]

        self.assertEqual((), build_walk_forward_plan(dates))

    def test_rejects_non_positive_configuration(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            build_walk_forward_plan([date(2000, 1, 1)], WalkForwardConfig(test_years=0))


if __name__ == "__main__":
    unittest.main()
