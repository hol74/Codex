from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_replacement_source_feasibility import (
    write_e14_replacement_source_feasibility_audit,
)


class E14ReplacementSourceFeasibilityTests(unittest.TestCase):
    def test_blocks_all_families_and_only_opens_vintage_policy_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual({"ready": 1, "blocked": 9}, audit["inventory"]["sourceStatusCounts"])
            self.assertEqual({"ready": 0, "blocked": 8}, audit["inventory"]["familyStatusCounts"])
            self.assertFalse(audit["decision"]["fullSourceReadiness"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertTrue(audit["decision"]["vintagePolicyDecisionPreregistrationAuthorized"])
            self.assertFalse(audit["protocol"]["seriesObservationDownloaded"])
            self.assertFalse(audit["protocol"]["datasetRead"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            ready = [item["sourceId"] for item in audit["sourceAssessments"] if item["status"] == "ready"]
            self.assertEqual(["fred-dtb3"], ready)
            blocked = {item["familyId"] for item in audit["familyAssessments"] if item["status"] == "blocked"}
            self.assertEqual(8, len(blocked))
            self.assertIn("cross-dollar-shock", blocked)
            self.assertIn("broad-treasury-rate-dislocation", blocked)

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_rejects_readiness_swap_even_when_counts_and_hash_are_updated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads(_evidence().read_text(encoding="utf-8"))
            dgs2 = next(item for item in evidence["sources"] if item["sourceId"] == "fred-dgs2")
            for field in (
                "providerPrimaryPageReachable", "coverageVerified", "licensingCleared",
                "componentCoverageVerified", "releaseProofComplete", "vintageProofComplete",
                "methodologyManifestComplete",
            ):
                dgs2[field] = True
            dgs2["blockingReasons"] = []
            dtb3 = next(item for item in evidence["sources"] if item["sourceId"] == "fred-dtb3")
            dtb3["vintageProofComplete"] = False
            dtb3["blockingReasons"] = ["synthetic-test-block"]
            unsafe_evidence = root / "unsafe-evidence.json"
            unsafe_evidence.write_text(json.dumps(evidence), encoding="utf-8")
            unsafe_contract = _contract_for_evidence(root, unsafe_evidence)
            with self.assertRaisesRegex(DatasetValidationError, "classifications differ"):
                _write(root / "out.json", contract=unsafe_contract, evidence=unsafe_evidence)

    def test_rejects_contract_that_opens_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["sourceAcquisitionAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe)

    def test_rejects_evidence_roster_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads(_evidence().read_text(encoding="utf-8"))
            evidence["sources"][0]["sourceId"] = "unregistered-h8-substitute"
            unsafe_evidence = root / "unsafe-evidence.json"
            unsafe_evidence.write_text(json.dumps(evidence), encoding="utf-8")
            unsafe_contract = _contract_for_evidence(root, unsafe_evidence)
            with self.assertRaisesRegex(DatasetValidationError, "source roster differs"):
                _write(root / "out.json", contract=unsafe_contract, evidence=unsafe_evidence)


def _contract() -> Path:
    return Path("models/e14-replacement-source-feasibility-contract-v1.json")


def _evidence() -> Path:
    return Path("models/e14-replacement-source-feasibility-evidence-v1.json")


def _contract_for_evidence(root: Path, evidence: Path) -> Path:
    contract = json.loads(_contract().read_text(encoding="utf-8"))
    contract["inputHashes"]["reauditEvidenceV1Sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
    path = root / "unsafe-contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def _write(output: Path, contract: Path | None = None, evidence: Path | None = None) -> Path:
    return write_e14_replacement_source_feasibility_audit(
        contract or _contract(),
        Path("models/e14-new-information-hypothesis-plan-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-source-vintage-feasibility-audit-v1.json"),
        Path("models/e14-feasibility-remediation-contract-v1.json"),
        Path("models/e14-feasibility-remediation-plan-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-feasibility-remediation-audit-v1.json"),
        evidence or _evidence(),
        Path("models/e14-replacement-source-feasibility-evidence-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
