from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_loeo_evaluation_v2 import (
    _causal_percentiles,
    apply_persistence_missing,
    write_e14_loeo_evaluation_v2,
)


class E14LoeoEvaluationV2Tests(unittest.TestCase):
    def test_real_report_is_deterministic_inner_only_and_consumes_all_folds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            report = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(28, report["inventory"]["evaluatedCandidateCount"])
            self.assertEqual(140, report["inventory"]["foldAssignmentCount"])
            self.assertTrue(report["checks"]["heldOutEpisodeExcludedFromTransformFit"])
            self.assertTrue(report["checks"]["heldOutLabelsExcludedFromThresholdSelection"])
            self.assertTrue(report["protocol"]["candidateFittingPerformed"])
            self.assertTrue(report["protocol"]["candidateEvaluationPerformed"])
            self.assertFalse(report["protocol"]["candidateRankingPerformed"])
            self.assertFalse(report["protocol"]["shortlistProduced"])
            self.assertEqual(0, report["protocol"]["outerFeatureRowCountUsed"])
            self.assertEqual(12, report["fundingBoundarySensitivity"]["candidateFoldReportCount"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_missing_score_resets_persistence_without_imputation(self) -> None:
        self.assertEqual(
            [False, True, None, False, True],
            apply_persistence_missing([0.8, 0.9, None, 0.8, 0.9], 0.7, 2, 2),
        )

    def test_excluded_heldout_value_never_enters_future_percentile_history(self) -> None:
        observations = []
        current = date(2000, 1, 1)
        for index in range(62):
            period = current.isoformat()
            observations.append({"period": period, "availableOn": period, "value": float(index)})
            month = current.year * 12 + current.month
            current = date(month // 12, month % 12 + 1, 1)
        source = {"observations": observations}
        source["observations"][60]["value"] = 30.5
        changed = copy.deepcopy(source)
        changed["observations"][60]["value"] = 100000.0
        heldout = {observations[60]["period"]}
        left = _causal_percentiles(source, heldout, date(2005, 12, 1))
        right = _causal_percentiles(changed, heldout, date(2005, 12, 1))
        self.assertNotEqual(left[observations[60]["period"]], right[observations[60]["period"]])
        self.assertEqual(left[observations[61]["period"]], right[observations[61]["period"]])

    def test_rejects_contract_that_opens_outer_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["outerOosAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "report.json", contract=unsafe)


def _contract() -> Path:
    return Path("models/e14-four-detector-loeo-evaluation-contract-v2.json")


def _write(output: Path, contract: Path | None = None) -> Path:
    data = Path("../../data/historical-real-v12-2008-2025")
    return write_e14_loeo_evaluation_v2(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-generated-four-detector-candidates-v2.json"),
        data / "challengers/e14-four-detector-candidate-manifest-audit-v2.json",
        data / "e14-feature-foundation-v2/e14-mechanism-feature-foundation-v2.json",
        Path("models/e14-mechanism-feature-foundation-lock-v2.json"),
        data / "challengers/e14-mechanism-feature-foundation-audit-v2.json",
        Path("models/e14-four-detector-candidate-generation-protocol-v2.json"),
        data / "challengers/e14-four-detector-protocol-readiness-audit-v2.json",
        Path("models/e14-four-detector-loeo-preregistration-v2.json"),
        data / "challengers/e14-four-detector-loeo-preregistration-audit-v2.json",
        Path("models/e14-four-detector-loeo-report-schema-v2.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
