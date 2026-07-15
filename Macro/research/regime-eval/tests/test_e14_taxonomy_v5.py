from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_taxonomy_v5 import write_e14_taxonomy_v5


class E14TaxonomyV5Tests(unittest.TestCase):
    def test_versions_accepted_expansion_without_opening_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            v4 = Path("ground-truth/us-financial-stress-v4.json")
            before = hashlib.sha256(v4.read_bytes()).hexdigest()
            taxonomy_a, audit_a = _write(root / "a")
            taxonomy_b, audit_b = _write(root / "b")
            taxonomy = json.loads(taxonomy_a.read_text(encoding="utf-8"))
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual(taxonomy_a.read_bytes(), taxonomy_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual(before, hashlib.sha256(v4.read_bytes()).hexdigest())
            self.assertEqual(5, taxonomy["schemaVersion"])
            self.assertEqual("us-financial-stress-mechanism-aware-v5", taxonomy["groundTruthId"])
            self.assertEqual("us-financial-stress-mechanism-aware-v4", taxonomy["derivedFrom"])
            self.assertEqual(16, len(taxonomy["foundationEvidence"]))
            self.assertEqual(8, len(taxonomy["hardNegativeEpisodes"]))
            self.assertEqual(11, taxonomy["coverage"]["combinedPositiveEpisodeCount"])
            self.assertEqual(6, taxonomy["coverage"]["combinedHardNegativeEpisodeCount"])
            self.assertTrue(taxonomy["coverage"]["coverageThresholdsSatisfied"])
            self.assertTrue(all(
                item["combinedHardNegativeEpisodeCount"] >= 2
                for item in taxonomy["coverage"]["mechanismCoverage"]
            ))
            added_ids = set(taxonomy["acceptedExpansion"]["addedDossierIds"])
            self.assertEqual(4, len(added_ids))
            self.assertTrue(added_ids.issubset({item["id"] for item in taxonomy["hardNegativeEpisodes"]}))
            self.assertFalse(taxonomy["governance"]["candidateGenerationAuthorized"])
            self.assertEqual(
                "TAXONOMY_V5_VERSIONED_CANDIDATE_READINESS_REQUIRED", audit["status"]
            )
            self.assertTrue(audit["decision"]["taxonomyV5Ready"])
            self.assertTrue(audit["decision"]["candidateReadinessGateAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_contract_that_opens_candidate_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(
                Path("models/e14-taxonomy-v5-materialization-contract-v1.json").read_text(
                    encoding="utf-8"
                )
            )
            contract["authorizationPolicy"]["candidateGenerationAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "unsafe", unsafe)


def _write(
    root: Path,
    contract: Path = Path("models/e14-taxonomy-v5-materialization-contract-v1.json"),
) -> tuple[Path, Path]:
    return write_e14_taxonomy_v5(
        contract,
        Path("ground-truth/us-financial-stress-v4.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-coverage-gate-audit-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v11.json"),
        Path("models/e14-financial-stress-taxonomy-v4-schema.json"),
        Path("models/e14-financial-stress-taxonomy-v5-schema.json"),
        Path("models/e14-label-audit-contract-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        root / "taxonomy-v5.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
