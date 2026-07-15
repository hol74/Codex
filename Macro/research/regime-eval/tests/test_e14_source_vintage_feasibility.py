from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_source_vintage_feasibility import (
    write_e14_source_vintage_feasibility_audit,
)


class E14SourceVintageFeasibilityTests(unittest.TestCase):
    def test_classifies_families_and_keeps_acquisition_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual({"ready": 1, "conditional": 5, "blocked": 4}, audit["inventory"]["sourceStatusCounts"])
            self.assertEqual({"ready": 0, "conditional": 3, "blocked": 5}, audit["inventory"]["familyStatusCounts"])
            self.assertFalse(audit["decision"]["fullSourceVintageReadiness"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertTrue(audit["decision"]["feasibilityRemediationPreregistrationAuthorized"])
            self.assertFalse(audit["protocol"]["seriesObservationDownloaded"])
            self.assertFalse(audit["protocol"]["datasetRead"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            status = {item["familyId"]: item["status"] for item in audit["familyAssessments"]}
            self.assertEqual("conditional", status["bank-balance-sheet-flow"])
            self.assertEqual("conditional", status["cross-dollar-shock"])
            self.assertEqual("conditional", status["cross-bank-flow-contraction"])
            self.assertEqual("blocked", status["broad-equity-drawdown"])
            self.assertEqual("blocked", status["funding-secured-repo-dislocation"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_reports_preregistered_history_shortfalls_without_relaxing_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_write(Path(directory) / "audit.json").read_text(encoding="utf-8"))
            families = {item["familyId"]: item for item in audit["familyAssessments"]}
            self.assertIn(
                "insufficient-causal-history:continental-illinois-1984:4-of-60",
                families["bank-loss-absorption"]["blockingReasons"],
            )
            self.assertIn(
                "insufficient-causal-history:russia-ltcm-1998:19-of-60",
                families["funding-unsecured-tiering"]["blockingReasons"],
            )
            self.assertIn(
                "insufficient-causal-history:repo-stress-2019:17-of-36",
                families["funding-secured-repo-dislocation"]["blockingReasons"],
            )
            self.assertTrue(families["funding-unsecured-tiering"]["retiredOnBlocked"])
            self.assertFalse(families["funding-unsecured-tiering"]["sourceAcquisitionAuthorized"])

    def test_rejects_evidence_reclassification_even_when_hash_is_updated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads(_evidence().read_text(encoding="utf-8"))
            evidence["sources"][2]["licensingStatus"] = "permitted-with-attribution"
            unsafe_evidence = root / "unsafe-evidence.json"
            unsafe_evidence.write_text(json.dumps(evidence), encoding="utf-8")
            contract = _contract_for_evidence(unsafe_evidence)
            unsafe_contract = root / "unsafe-contract.json"
            unsafe_contract.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "classifications differ"):
                _write(root / "out.json", contract=unsafe_contract, evidence=unsafe_evidence)

    def test_rejects_contract_that_opens_source_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["sourceAcquisitionAuthorized"] = True
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe)


def _contract() -> Path:
    return Path("models/e14-source-vintage-feasibility-contract-v1.json")


def _evidence() -> Path:
    return Path("models/e14-source-vintage-feasibility-evidence-v1.json")


def _contract_for_evidence(evidence: Path) -> dict:
    contract = json.loads(_contract().read_text(encoding="utf-8"))
    contract["inputHashes"]["feasibilityEvidenceV1Sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
    return contract


def _write(
    output: Path,
    contract: Path | None = None,
    evidence: Path | None = None,
) -> Path:
    return write_e14_source_vintage_feasibility_audit(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-new-information-hypothesis-contract-v1.json"),
        Path("models/e14-new-information-hypothesis-plan-v1.json"),
        Path("models/e14-new-information-hypothesis-schema-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-new-information-hypothesis-audit-v1.json"),
        evidence or _evidence(),
        Path("models/e14-source-vintage-feasibility-evidence-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
