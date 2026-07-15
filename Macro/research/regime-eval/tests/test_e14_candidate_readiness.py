from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_candidate_readiness import write_e14_candidate_readiness_gate


class E14CandidateReadinessTests(unittest.TestCase):
    def test_blocks_generation_on_unpopulated_features_and_legacy_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_a = _write(root / "a.json")
            report_b = _write(root / "b.json")
            report = json.loads(report_a.read_text(encoding="utf-8"))

            self.assertEqual(report_a.read_bytes(), report_b.read_bytes())
            self.assertEqual("CANDIDATE_READINESS_BLOCKED_FOUNDATION_AND_PROTOCOL", report["status"])
            self.assertEqual(4, report["inventory"]["detectorCount"])
            self.assertEqual(6, report["inventory"]["detectorFeatureProposalCount"])
            self.assertEqual(0, report["inventory"]["populatedManifestedFeatureCount"])
            self.assertTrue(report["checks"]["taxonomyCoverageSufficient"])
            self.assertTrue(report["checks"]["oneIndependentDetectorPerMechanism"])
            self.assertFalse(report["checks"]["generationProtocolBoundToTaxonomyV5"])
            self.assertFalse(report["checks"]["generationProtocolMechanismSeparated"])
            self.assertEqual(4, len(report["blockers"]))
            self.assertFalse(report["decision"]["candidateGenerationAuthorized"])
            self.assertFalse(report["decision"]["outerOosAuthorized"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a.json")

    def test_rejects_contract_that_opens_outer_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-candidate-readiness-gate-contract-v1.json").read_text())
            contract["authorizationPolicy"]["outerOosAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out.json", unsafe)

    def test_rejects_taxonomy_hash_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            taxonomy = json.loads(Path("ground-truth/us-financial-stress-v5.json").read_text())
            taxonomy["label"] += " tampered"
            tampered = root / "taxonomy.json"
            tampered.write_text(json.dumps(taxonomy), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out.json", taxonomy=tampered)


def _write(
    output: Path,
    contract: Path = Path("models/e14-candidate-readiness-gate-contract-v1.json"),
    taxonomy: Path = Path("ground-truth/us-financial-stress-v5.json"),
) -> Path:
    return write_e14_candidate_readiness_gate(
        contract,
        taxonomy,
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-taxonomy-v5-materialization-audit-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        Path("models/e14-historical-source-catalog-v1.json"),
        Path("models/e13-candidate-generation-protocol-v1.json"),
        Path("models/e12-data-foundation-lock-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
