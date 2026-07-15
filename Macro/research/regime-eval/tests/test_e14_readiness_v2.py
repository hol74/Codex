from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_readiness_v2 import write_e14_readiness_v2


class E14ReadinessV2Tests(unittest.TestCase):
    def test_builds_eligible_28_entry_roster_without_generating_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_a = _write(root / "a")
            outputs_b = _write(root / "b")
            for left, right in zip(outputs_a, outputs_b):
                self.assertEqual(left.read_bytes(), right.read_bytes())

            roster = json.loads(outputs_a[0].read_text(encoding="utf-8"))
            audit = json.loads(outputs_a[1].read_text(encoding="utf-8"))
            preserved = [
                item for item in roster["candidates"]
                if item["identityPolicy"] == "preserved-exactly-from-candidate-manifest-v1"
            ]
            new = [item for item in roster["candidates"] if "-v2-" in item["candidateId"]]

            self.assertEqual(28, roster["candidateCount"])
            self.assertEqual(16, len(preserved))
            self.assertEqual(12, len(new))
            self.assertEqual(24, len(roster["retiredCandidateIds"]))
            self.assertTrue(all(item["eligibility"]["structurallyEligible"] for item in roster["candidates"]))
            self.assertTrue(all(item["lifecycleStatus"] == "readiness-planned-not-generated-not-fit" for item in roster["candidates"]))
            self.assertEqual(
                {"positive": 3, "hardNegative": 2},
                audit["episodeCoverage"]["funding-liquidity"],
            )
            self.assertEqual(
                1,
                audit["inventory"]["availabilityLagMonthsBySeries"]["e14-fedfunds-minus-tbill-monthly"],
            )
            self.assertFalse(audit["decision"]["candidateManifestGenerationAuthorized"])
            self.assertFalse(audit["decision"]["candidateFittingAuthorized"])
            self.assertTrue(audit["decision"]["protocolV2DesignAuthorized"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_policy_that_opens_candidate_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = json.loads(_policy().read_text(encoding="utf-8"))
            policy["authorizationPolicy"]["candidateManifestGenerationAuthorized"] = True
            unsafe = root / "unsafe-policy.json"
            unsafe.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out", policy=unsafe)

    def test_rejects_contract_that_reuses_retired_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["transitionPolicy"]["retiredIdReuseForbidden"] = False
            unsafe = root / "unsafe-contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out", contract=unsafe)


def _contract() -> Path:
    return Path("models/e14-four-detector-readiness-contract-v2.json")


def _policy() -> Path:
    return Path("models/e14-four-detector-readiness-policy-v2.json")


def _write(
    root: Path,
    contract: Path | None = None,
    policy: Path | None = None,
) -> tuple[Path, Path]:
    return write_e14_readiness_v2(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/e14-mechanism-feature-foundation-v2.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v2.json"),
        Path("models/e14-generated-four-detector-candidates-v1.json"),
        Path("models/e14-structural-coverage-repair-plan-v1.json"),
        policy or _policy(),
        Path("models/e14-four-detector-readiness-policy-schema-v2.json"),
        Path("models/e14-four-detector-readiness-roster-schema-v2.json"),
        root / "roster.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
