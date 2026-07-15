from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_no_go_diagnostic import write_e14_no_go_diagnostic


class E14NoGoDiagnosticTests(unittest.TestCase):
    def test_diagnoses_positive_generalization_and_opens_only_hypothesis_design(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(28, audit["inventory"]["candidateCount"])
            self.assertEqual(140, audit["inventory"]["foldCount"])
            self.assertEqual(0, audit["inventory"]["absoluteGatePassingCandidateCount"])
            self.assertTrue(audit["globalConclusion"]["allCandidatesHaveZeroWorstEpisodeRecall"])
            self.assertEqual("positive-cross-episode-generalization", audit["globalConclusion"]["dominantFailure"])
            self.assertFalse(audit["globalConclusion"]["falseAlarmControlIsDominantFailure"])
            self.assertTrue(audit["decision"]["existingCandidateFamilyClosedNoGo"])
            self.assertTrue(audit["decision"]["newInformationHypothesisDesignAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])
            self.assertFalse(audit["decision"]["candidateEvaluationAuthorized"])
            self.assertFalse(audit["decision"]["outerOosAuthorized"])
            self.assertFalse(audit["protocol"]["thresholdsRetuned"])
            self.assertFalse(audit["protocol"]["candidatesReevaluated"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])
            self.assertEqual(4, len(audit["mechanismConclusions"]))

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_rejects_contract_that_authorizes_candidate_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["candidateEvaluationAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe)

    def test_rejects_mutated_loeo_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = json.loads(_report().read_text(encoding="utf-8"))
            report["decision"]["withinMechanismRankingAuthorized"] = True
            unsafe = root / "unsafe-report.json"
            unsafe.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", report=unsafe)


def _contract() -> Path:
    return Path("models/e14-loeo-no-go-diagnostic-contract-v1.json")


def _report() -> Path:
    return Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-loeo-report-v2.json")


def _write(
    output: Path,
    contract: Path | None = None,
    report: Path | None = None,
) -> Path:
    return write_e14_no_go_diagnostic(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-generated-four-detector-candidates-v2.json"),
        Path("models/e14-four-detector-candidate-generation-protocol-v2.json"),
        Path("models/e14-four-detector-loeo-preregistration-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-loeo-preregistration-audit-v2.json"),
        report or _report(),
        Path("models/e14-loeo-no-go-diagnostic-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
