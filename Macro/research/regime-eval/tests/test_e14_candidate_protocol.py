from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_candidate_protocol import write_e14_candidate_protocol_readiness


class E14CandidateProtocolTests(unittest.TestCase):
    def test_freezes_four_detector_protocol_and_opens_only_research_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_a = _write(root / "a.json")
            report_b = _write(root / "b.json")
            self.assertEqual(report_a.read_bytes(), report_b.read_bytes())
            report = json.loads(report_a.read_text(encoding="utf-8"))

            self.assertEqual("RESEARCH_CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED", report["status"])
            self.assertEqual(4, report["inventory"]["mechanismCount"])
            self.assertEqual(10, report["inventory"]["profileCount"])
            self.assertEqual(40, report["inventory"]["candidateBudget"])
            self.assertEqual(
                {"broad-market-repricing": 16, "funding-liquidity": 4,
                 "banking-credit": 16, "cross-border-growth": 4},
                report["inventory"]["candidateCountByMechanism"],
            )
            self.assertTrue(all(report["checks"].values()))
            self.assertTrue(report["decision"]["researchCandidateGenerationAuthorized"])
            self.assertFalse(report["decision"]["candidateEvaluationAuthorized"])
            self.assertFalse(report["decision"]["crossMechanismCompositionAuthorized"])
            self.assertFalse(report["decision"]["strictVintageReady"])
            self.assertFalse(report["decision"]["outerOosAuthorized"])
            self.assertFalse(report["decision"]["promotionAuthorized"])
            self.assertFalse(report["protocol"]["candidateGenerated"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a.json")

    def test_rejects_contract_that_opens_outer_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(
                Path("models/e14-four-detector-protocol-readiness-contract-v1.json").read_text()
            )
            contract["authorizationPolicy"]["outerOosAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out.json", contract=unsafe)

    def test_rejects_cross_mechanism_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = json.loads(
                Path("models/e14-four-detector-candidate-generation-protocol-v1.json").read_text()
            )
            protocol["detectors"]["funding-liquidity"]["profiles"][0]["seriesIds"] = [
                "e14-vix-monthly-maximum"
            ]
            protocol_path = root / "protocol.json"
            protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
            contract = json.loads(
                Path("models/e14-four-detector-protocol-readiness-contract-v1.json").read_text()
            )
            contract["inputHashes"]["candidateProtocolSha256"] = hashlib.sha256(
                protocol_path.read_bytes()
            ).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "not ready"):
                _write(root / "out.json", contract=contract_path, protocol=protocol_path)


def _write(
    output: Path,
    contract: Path = Path("models/e14-four-detector-protocol-readiness-contract-v1.json"),
    protocol: Path = Path("models/e14-four-detector-candidate-generation-protocol-v1.json"),
) -> Path:
    return write_e14_candidate_protocol_readiness(
        contract,
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        protocol,
        Path("models/e14-four-detector-candidate-protocol-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
