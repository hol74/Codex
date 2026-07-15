from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_hard_negative_coverage_gate import write_e14_hard_negative_coverage_gate


BASE = Path("../../data/historical-real-v12-2008-2025/challengers")
DOSSIER_DIRS = [
    BASE / "e14-dossiers-v1",
    BASE / "e14-hard-negative-dossiers-v2",
    BASE / "e14-revised-dossiers-v1",
    BASE / "e14-hard-negative-expansion-dossiers-v1",
    BASE / "e14-hard-negative-expansion-revised-dossiers-v1",
    BASE / "e14-hard-negative-expansion-revised-dossiers-v2",
]


class E14HardNegativeCoverageGateTests(unittest.TestCase):
    def test_accepted_evidence_reaches_six_events_and_two_per_mechanism(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _write(Path(directory) / "audit.json", DOSSIER_DIRS)
            audit = json.loads(output.read_text())
            self.assertEqual("ACCEPTED_HARD_NEGATIVE_COVERAGE_READY", audit["status"])
            self.assertEqual(16, audit["inventory"]["acceptedQueueDossierCount"])
            self.assertEqual(12, audit["inventory"]["taxonomyFoundationDossierCount"])
            self.assertEqual(4, audit["inventory"]["newAcceptedHardNegativeDossierCount"])
            self.assertEqual(0, audit["inventory"]["sameMechanismMonthConflictCount"])
            coverage = audit["acceptedCoverageAfterExpansion"]
            self.assertEqual(6, coverage["combinedHardNegativeEpisodeCount"])
            self.assertTrue(coverage["coverageThresholdsSatisfied"])
            self.assertTrue(all(item["combinedHardNegativeEpisodeCount"] == 2
                                for item in coverage["mechanismCoverage"]))
            self.assertTrue(audit["decision"]["taxonomyV5ProposalAuthorized"])
            self.assertFalse(audit["decision"]["taxonomyMutationAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])

    def test_manifest_must_resolve_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = [*DOSSIER_DIRS, DOSSIER_DIRS[0]]
            with self.assertRaisesRegex(DatasetValidationError, "exactly once"):
                _write(Path(directory) / "audit.json", duplicate)

    def test_output_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            _write(output, DOSSIER_DIRS)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(output, DOSSIER_DIRS)


def _write(output: Path, dossier_dirs: list[Path]) -> Path:
    return write_e14_hard_negative_coverage_gate(
        Path("models/e14-hard-negative-coverage-gate-contract-v1.json"),
        BASE / "e14-independent-review-queue-v11.json",
        BASE / "e14-hard-negative-targeted-review-ingestion-audit-v2.json",
        Path("ground-truth/us-financial-stress-v4.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-label-audit-contract-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        Path("models/e14-hard-negative-expansion-contract-v1.json"),
        dossier_dirs, output,
    )


if __name__ == "__main__":
    unittest.main()
