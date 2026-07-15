from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_candidate_generator import write_e14_candidate_manifest


class E14CandidateGeneratorTests(unittest.TestCase):
    def test_generates_exactly_40_deterministic_unfit_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_a = _write(root / "a.json")
            manifest_b = _write(root / "b.json")
            self.assertEqual(manifest_a.read_bytes(), manifest_b.read_bytes())
            manifest = json.loads(manifest_a.read_text(encoding="utf-8"))

            self.assertEqual("GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED", manifest["status"])
            self.assertEqual(40, manifest["candidateCount"])
            self.assertEqual(
                {
                    "banking-credit": 16,
                    "broad-market-repricing": 16,
                    "cross-border-growth": 4,
                    "funding-liquidity": 4,
                },
                manifest["candidateCountByMechanism"],
            )
            ids = [item["candidateId"] for item in manifest["candidates"]]
            self.assertEqual(40, len(set(ids)))
            self.assertTrue(all(item["lifecycleStatus"] == "research-generated-not-fit" for item in manifest["candidates"]))
            self.assertTrue(all(item["parameters"]["thresholdQuantiles"] == [0.8, 0.9, 0.95] for item in manifest["candidates"]))
            self.assertTrue(all(item["parameters"]["thresholdSelectionScope"] == "inner-train-within-leave-one-episode-out" for item in manifest["candidates"]))
            self.assertTrue(all(binding["fitScope"] == "inner-only" for item in manifest["candidates"] for binding in item["featureBindings"]))
            self.assertFalse(manifest["authorizations"]["candidateFittingAuthorized"])
            self.assertFalse(manifest["authorizations"]["candidateEvaluationAuthorized"])
            self.assertFalse(manifest["authorizations"]["outerOosAuthorized"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a.json")

    def test_rejects_contract_that_authorizes_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(
                Path("models/e14-four-detector-candidate-manifest-contract-v1.json").read_text()
            )
            contract["authorizationPolicy"]["candidateEvaluationAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out.json", contract=unsafe)

    def test_rejects_protocol_not_bound_to_readiness_audit(self) -> None:
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
                Path("models/e14-four-detector-candidate-manifest-contract-v1.json").read_text()
            )
            contract["inputHashes"]["candidateProtocolSha256"] = hashlib.sha256(
                protocol_path.read_bytes()
            ).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out.json", contract=contract_path, protocol=protocol_path)


def _write(
    output: Path,
    contract: Path = Path("models/e14-four-detector-candidate-manifest-contract-v1.json"),
    protocol: Path = Path("models/e14-four-detector-candidate-generation-protocol-v1.json"),
) -> Path:
    return write_e14_candidate_manifest(
        contract,
        protocol,
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-protocol-readiness-audit-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v1.json"),
        Path("models/e14-four-detector-candidate-manifest-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
