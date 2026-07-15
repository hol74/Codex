from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_loeo_preregistration import write_e14_loeo_preregistration_audit


class E14LoeoPreregistrationTests(unittest.TestCase):
    def test_preregisters_loeo_and_blocks_structurally_ineligible_mechanisms(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit_a = _write(root / "a.json")
            audit_b = _write(root / "b.json")
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual("INNER_LOEO_PREREGISTERED_STRUCTURAL_COVERAGE_BLOCKED", audit["status"])
            self.assertEqual(40, audit["inventory"]["candidateCount"])
            self.assertEqual(16, audit["inventory"]["eligibleCandidateCount"])
            self.assertEqual(24, audit["inventory"]["ineligibleCandidateCount"])
            self.assertEqual(
                {"banking-credit": 0, "broad-market-repricing": 16,
                 "cross-border-growth": 0, "funding-liquidity": 0},
                audit["inventory"]["eligibleCandidateCountByMechanism"],
            )
            self.assertEqual(["broad-market-repricing"], audit["decision"]["readyMechanisms"])
            self.assertEqual(
                ["banking-credit", "cross-border-growth", "funding-liquidity"],
                audit["decision"]["blockedMechanisms"],
            )
            self.assertFalse(audit["decision"]["candidateFittingAuthorized"])
            self.assertFalse(audit["decision"]["partialMechanismFittingAuthorized"])
            self.assertFalse(audit["decision"]["outerOosAuthorized"])
            self.assertFalse(audit["protocol"]["candidateFittingPerformed"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a.json")

    def test_rejects_contract_that_authorizes_partial_fitting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(
                Path("models/e14-four-detector-loeo-readiness-contract-v1.json").read_text()
            )
            contract["authorizationPolicy"]["partialMechanismFittingAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or policy are invalid"):
                _write(root / "out.json", contract=unsafe)

    def test_rejects_taxonomy_not_bound_to_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            taxonomy = json.loads(Path("ground-truth/us-financial-stress-v5.json").read_text())
            taxonomy["coverageTo"] = "2025-11-30"
            taxonomy_path = root / "taxonomy.json"
            taxonomy_path.write_text(json.dumps(taxonomy), encoding="utf-8")
            self.assertNotEqual(
                hashlib.sha256(taxonomy_path.read_bytes()).hexdigest(),
                json.loads(Path("models/e14-four-detector-loeo-readiness-contract-v1.json").read_text())["inputHashes"]["taxonomyV5Sha256"],
            )
            with self.assertRaisesRegex(DatasetValidationError, "inputs or policy are invalid"):
                _write(root / "out.json", taxonomy=taxonomy_path)


def _write(
    output: Path,
    contract: Path = Path("models/e14-four-detector-loeo-readiness-contract-v1.json"),
    taxonomy: Path = Path("ground-truth/us-financial-stress-v5.json"),
) -> Path:
    return write_e14_loeo_preregistration_audit(
        contract,
        taxonomy,
        Path("models/e14-generated-four-detector-candidates-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v1.json"),
        Path("models/e14-four-detector-candidate-generation-protocol-v1.json"),
        Path("models/e14-four-detector-loeo-preregistration-v1.json"),
        Path("models/e14-four-detector-loeo-preregistration-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
