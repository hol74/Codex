from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_hard_negative_expansion import write_e14_hard_negative_expansion


class E14HardNegativeExpansionTests(unittest.TestCase):
    def test_curates_four_independent_conflict_free_dossiers_and_preserves_prior_accepts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_a, audit_a = _write(root / "a")
            queue_b, audit_b = _write(root / "b")
            queue = json.loads(queue_a.read_text(encoding="utf-8"))
            audit = json.loads(audit_a.read_text(encoding="utf-8"))
            base = json.loads(
                Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v5.json")
                .read_text(encoding="utf-8")
            )

            self.assertEqual(queue_a.read_bytes(), queue_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual(base["dossiers"], queue["dossiers"][:12])
            self.assertEqual(16, len(queue["dossiers"]))
            self.assertEqual("EXPANSION_AWAITING_INDEPENDENT_REVIEW", queue["status"])
            self.assertEqual("INDEPENDENT_REVIEW_REQUIRED", audit["status"])
            self.assertEqual(4, audit["inventory"]["newIndependentEventCount"])
            self.assertEqual(0, audit["inventory"]["sameMechanismMonthConflictCount"])
            potential = audit["potentialCoverageIfAllAccepted"]
            self.assertEqual(6, potential["combinedHardNegativeEpisodeCount"])
            self.assertTrue(potential["coverageThresholdsSatisfied"])
            self.assertTrue(all(
                item["combinedHardNegativeEpisodeCount"] == 2
                for item in potential["mechanismCoverage"]
            ))
            self.assertFalse(audit["decision"]["independentReviewComplete"])
            self.assertFalse(audit["decision"]["taxonomyUpdateAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_contract_that_opens_candidate_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(
                Path("models/e14-hard-negative-expansion-contract-v1.json").read_text(encoding="utf-8")
            )
            contract["authorizationPolicy"]["candidateGenerationAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "unsafe", unsafe)


def _write(
    root: Path,
    contract: Path = Path("models/e14-hard-negative-expansion-contract-v1.json"),
) -> tuple[Path, Path]:
    return write_e14_hard_negative_expansion(
        contract,
        Path("models/e14-hard-negative-expansion-pack-v1.json"),
        Path("ground-truth/us-financial-stress-v4.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-taxonomy-v4-materialization-audit-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v5.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        Path("models/e14-label-audit-contract-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        root / "dossiers",
        root / "queue-v6.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
