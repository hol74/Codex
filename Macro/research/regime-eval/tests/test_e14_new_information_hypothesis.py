from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_new_information_hypothesis import (
    write_e14_new_information_hypothesis_audit,
)


class E14NewInformationHypothesisTests(unittest.TestCase):
    def test_preregisters_exact_episode_signatures_and_opens_only_feasibility(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(4, audit["inventory"]["mechanismCount"])
            self.assertEqual(8, audit["inventory"]["featureFamilyCount"])
            self.assertEqual(17, audit["inventory"]["episodeSignatureCount"])
            self.assertEqual(
                {"banking-credit": 3, "broad-market-repricing": 6,
                 "cross-border-growth": 5, "funding-liquidity": 3},
                audit["inventory"]["episodeSignatureCountByMechanism"],
            )
            self.assertTrue(audit["checks"]["priorCandidateFamilyClosedNoGo"])
            self.assertTrue(audit["checks"]["everyFrozenLoeoEpisodeHasOneSignature"])
            self.assertTrue(audit["decision"]["sourceFeasibilityAuditAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])
            self.assertFalse(audit["decision"]["candidateEvaluationAuthorized"])
            self.assertFalse(audit["decision"]["outerOosAuthorized"])
            self.assertFalse(audit["protocol"]["datasetRead"])
            self.assertFalse(audit["protocol"]["sourceDownloaded"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_rejects_plan_and_contract_that_open_source_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["authorizations"]["sourceAcquisitionAuthorized"] = True
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            contract = _contract_for_plan(unsafe_plan)
            contract["authorizationPolicy"]["sourceAcquisitionAuthorized"] = True
            unsafe_contract = root / "unsafe-contract.json"
            unsafe_contract.write_text(json.dumps(contract), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out.json", contract=unsafe_contract, plan=unsafe_plan)

    def test_rejects_episode_signature_missing_from_frozen_loeo_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["mechanisms"][0]["episodeSignatures"].pop()
            unsafe_plan = root / "unsafe-plan.json"
            unsafe_plan.write_text(json.dumps(plan), encoding="utf-8")
            contract = _contract_for_plan(unsafe_plan)
            unsafe_contract = root / "unsafe-contract.json"
            unsafe_contract.write_text(json.dumps(contract), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "episode signatures"):
                _write(root / "out.json", contract=unsafe_contract, plan=unsafe_plan)


def _contract() -> Path:
    return Path("models/e14-new-information-hypothesis-contract-v1.json")


def _plan() -> Path:
    return Path("models/e14-new-information-hypothesis-plan-v1.json")


def _contract_for_plan(plan: Path) -> dict:
    contract = json.loads(_contract().read_text(encoding="utf-8"))
    contract["inputHashes"]["hypothesisPlanV1Sha256"] = hashlib.sha256(plan.read_bytes()).hexdigest()
    return contract


def _write(
    output: Path,
    contract: Path | None = None,
    plan: Path | None = None,
) -> Path:
    return write_e14_new_information_hypothesis_audit(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        Path("models/e14-historical-source-catalog-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-loeo-no-go-diagnostic-v1.json"),
        plan or _plan(),
        Path("models/e14-new-information-hypothesis-schema-v1.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
