from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_taxonomy_v4 import write_e14_taxonomy_v4


class E14TaxonomyV4Tests(unittest.TestCase):
    def test_versions_mechanism_aware_taxonomy_without_opening_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            v3 = Path("ground-truth/us-financial-stress-v3.json")
            before = hashlib.sha256(v3.read_bytes()).hexdigest()
            taxonomy_a, audit_a = _write(root / "a")
            taxonomy_b, audit_b = _write(root / "b")
            taxonomy = json.loads(taxonomy_a.read_text(encoding="utf-8"))
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual(taxonomy_a.read_bytes(), taxonomy_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual(before, hashlib.sha256(v3.read_bytes()).hexdigest())
            self.assertEqual("us-financial-stress-mechanism-aware-v4", taxonomy["groundTruthId"])
            self.assertEqual("1984-05-01", taxonomy["coverageFrom"])
            self.assertEqual("2025-12-31", taxonomy["coverageTo"])
            self.assertEqual(12, len(taxonomy["foundationEvidence"]))
            self.assertEqual(11, taxonomy["coverage"]["combinedPositiveEpisodeCount"])
            self.assertEqual(2, taxonomy["coverage"]["combinedHardNegativeEpisodeCount"])
            self.assertFalse(taxonomy["governance"]["candidateGenerationAuthorized"])
            self.assertEqual("TAXONOMY_V4_VERSIONED_MORE_HARD_NEGATIVES_REQUIRED", audit["status"])
            self.assertTrue(audit["decision"]["taxonomyV4Ready"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])

            brexit = [
                item for item in taxonomy["hardNegativeEpisodes"]
                if item["independentEventId"] == "brexit-contained-transmission-2016"
            ]
            self.assertEqual(3, len(brexit))
            self.assertEqual(1, len({item["independentEventId"] for item in brexit}))

            mexico = [
                item for item in taxonomy["episodes"] + taxonomy["hardNegativeEpisodes"]
                if item["firstMonth"] <= "1995-01-01" <= item["lastMonth"]
                and item.get("foundationOrigin") == "accepted-e14-dossier"
            ]
            self.assertIn("positive", {item["financialState"] for item in mexico})
            self.assertIn("hard-negative", {item["financialState"] for item in mexico})

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_contract_that_opens_candidate_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(
                Path("models/e14-taxonomy-v4-materialization-contract-v1.json").read_text(encoding="utf-8")
            )
            contract["authorizationPolicy"]["candidateGenerationAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "unsafe", unsafe)


def _write(
    root: Path,
    contract: Path = Path("models/e14-taxonomy-v4-materialization-contract-v1.json"),
) -> tuple[Path, Path]:
    return write_e14_taxonomy_v4(
        contract,
        Path("ground-truth/us-financial-stress-v3.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-label-foundation-proposal-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-label-foundation-gate-audit-v1.json"),
        Path("models/e14-label-foundation-proposal-schema-v1.json"),
        Path("models/e14-financial-stress-taxonomy-v4-schema.json"),
        Path("models/e14-label-audit-contract-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        root / "taxonomy-v4.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
