from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_mechanism_contract import write_e14_mechanism_contract_audit


class E14MechanismContractTests(unittest.TestCase):
    def test_freezes_four_independent_detectors_without_opening_population(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("READY_FOR_DOSSIER_CURATION", payload["status"])
            self.assertEqual(4, payload["inventory"]["detectorCount"])
            self.assertEqual(6, payload["inventory"]["featureProposalCount"])
            self.assertEqual(0, payload["protocol"]["dossierCountRead"])
            self.assertEqual(0, payload["protocol"]["outerFeatureRowCountUsed"])
            self.assertTrue(payload["decision"]["dossierCurationAuthorized"])
            self.assertFalse(payload["decision"]["groundTruthMutationAuthorized"])
            self.assertFalse(payload["decision"]["corpusPopulationAuthorized"])
            self.assertFalse(payload["decision"]["candidateGenerationAuthorized"])
            self.assertTrue(all(item["status"] == "contract-only-not-fitted" for item in payload["detectors"]))

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E14 mechanism contract audit"):
                _write(first)

    def test_rejects_diagnostic_composite_as_detector_feature(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-mechanism-detector-contract-v1.json").read_text(encoding="utf-8"))
            contract["detectors"][0]["featureProposals"][0]["sourceId"] = "chicago-fed-nfci"
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "feature proposal is not eligible"):
                _write(root / "report.json", unsafe)


def _write(
    output: Path,
    contract: Path = Path("models/e14-mechanism-detector-contract-v1.json"),
) -> Path:
    return write_e14_mechanism_contract_audit(
        contract,
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-historical-source-catalog-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-historical-feasibility-v1.json"),
        Path("ground-truth/us-financial-stress-v3.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
