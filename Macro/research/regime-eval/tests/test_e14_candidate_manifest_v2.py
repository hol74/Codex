from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_candidate_manifest_v2 import write_e14_candidate_manifest_v2


class E14CandidateManifestV2Tests(unittest.TestCase):
    def test_materializes_exact_roster_with_lifecycle_only_transition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_a = _write(root / "a")
            outputs_b = _write(root / "b")
            for left, right in zip(outputs_a, outputs_b):
                self.assertEqual(left.read_bytes(), right.read_bytes())

            manifest = json.loads(outputs_a[0].read_text(encoding="utf-8"))
            audit = json.loads(outputs_a[1].read_text(encoding="utf-8"))
            roster = json.loads(_roster().read_text(encoding="utf-8"))
            protocol = json.loads(_protocol().read_text(encoding="utf-8"))

            self.assertEqual(28, manifest["candidateCount"])
            self.assertEqual(protocol["candidateIds"], manifest["candidateIds"])
            for source, generated in zip(roster["candidates"], manifest["candidates"]):
                restored = copy.deepcopy(generated)
                self.assertEqual("research-generated-not-fit", restored.pop("lifecycleStatus"))
                expected = copy.deepcopy(source)
                expected.pop("lifecycleStatus")
                self.assertEqual(expected, restored)
            self.assertTrue(audit["checks"]["onlyLifecycleStatusChanged"])
            self.assertTrue(audit["decision"]["candidateManifestV2Materialized"])
            self.assertFalse(audit["decision"]["candidateFittingAuthorized"])
            self.assertEqual(0, audit["protocol"]["featureRowsTransformed"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_contract_that_opens_fitting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["candidateFittingAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out", contract=unsafe)

    def test_rejects_protocol_candidate_order_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = json.loads(_protocol().read_text(encoding="utf-8"))
            protocol["candidateIds"][0], protocol["candidateIds"][1] = (
                protocol["candidateIds"][1], protocol["candidateIds"][0]
            )
            unsafe = root / "unsafe-protocol.json"
            unsafe.write_text(json.dumps(protocol), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out", protocol=unsafe)


def _contract() -> Path:
    return Path("models/e14-four-detector-candidate-manifest-contract-v2.json")


def _roster() -> Path:
    return Path("models/e14-four-detector-readiness-roster-v2.json")


def _protocol() -> Path:
    return Path("models/e14-four-detector-candidate-generation-protocol-v2.json")


def _write(
    root: Path,
    contract: Path | None = None,
    protocol: Path | None = None,
) -> tuple[Path, Path]:
    return write_e14_candidate_manifest_v2(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/e14-mechanism-feature-foundation-v2.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v2.json"),
        _roster(),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-readiness-audit-v2.json"),
        protocol or _protocol(),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-protocol-readiness-audit-v2.json"),
        Path("models/e14-four-detector-candidate-manifest-schema-v2.json"),
        root / "manifest.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
