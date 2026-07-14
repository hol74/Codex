from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_historical_feasibility import write_e14_historical_feasibility


class E14HistoricalFeasibilityTests(unittest.TestCase):
    def test_allows_dossiers_but_blocks_population_without_hard_negatives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("GO_FOR_EPISODE_DOSSIERS_ONLY", payload["status"])
            self.assertEqual(12, payload["inventory"]["sourceCount"])
            self.assertEqual(5, payload["inventory"]["positiveHypothesisCount"])
            self.assertEqual(0, payload["inventory"]["hardNegativeHypothesisCount"])
            self.assertTrue(payload["decision"]["episodeDossierCurationAuthorized"])
            self.assertFalse(payload["decision"]["fullCorpusPopulationAuthorized"])
            self.assertFalse(payload["decision"]["candidateGenerationAuthorized"])
            self.assertEqual(0, payload["protocol"]["outerFeatureRowCountUsed"])
            self.assertIn("minimumHardNegativeHypothesesPerMechanism", payload["failedChecks"])
            self.assertTrue(all(row["projectedPositiveEpisodeCount"] >= 3 for row in payload["mechanismFeasibility"]))

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E14 feasibility report"):
                _write(first)

    def test_rejects_reconstructed_history_promoted_to_pilot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = json.loads(Path("models/e14-historical-source-catalog-v1.json").read_text(encoding="utf-8"))
            next(item for item in catalog["sources"] if item["id"] == "chicago-fed-nfci")["eligibility"] = "pilot-with-snapshot"
            catalog_path = root / "unsafe-catalog.json"
            catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

            contract = json.loads(Path("models/e14-historical-feasibility-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["sourceCatalogSha256"] = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
            contract_path = root / "unsafe-contract.json"
            contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "must remain diagnostic-only"):
                _write(root / "report.json", catalog_path, contract_path)


def _write(
    output: Path,
    catalog: Path = Path("models/e14-historical-source-catalog-v1.json"),
    contract: Path = Path("models/e14-historical-feasibility-contract-v1.json"),
) -> Path:
    return write_e14_historical_feasibility(
        catalog,
        Path("ground-truth/us-financial-stress-v3.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-label-audit-v1.json"),
        contract,
        output,
    )


if __name__ == "__main__":
    unittest.main()
