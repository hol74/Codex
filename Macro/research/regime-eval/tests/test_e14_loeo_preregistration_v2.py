from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_loeo_preregistration_v2 import write_e14_loeo_preregistration_audit_v2


class E14LoeoPreregistrationV2Tests(unittest.TestCase):
    def test_freezes_140_inner_folds_and_opens_only_inner_fit_and_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit_a = _write(root / "a.json")
            audit_b = _write(root / "b.json")
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual(28, audit["inventory"]["eligibleCandidateCount"])
            self.assertEqual(140, audit["inventory"]["candidateFoldAssignmentCount"])
            self.assertEqual(
                {"banking-credit": 12, "broad-market-repricing": 96,
                 "cross-border-growth": 20, "funding-liquidity": 12},
                audit["inventory"]["candidateFoldAssignmentCountByMechanism"],
            )
            self.assertTrue(audit["decision"]["innerFeatureTransformationAuthorized"])
            self.assertTrue(audit["decision"]["innerCandidateFittingAuthorized"])
            self.assertTrue(audit["decision"]["innerLoeoEvaluationAuthorized"])
            self.assertFalse(audit["decision"]["candidateRankingAuthorized"])
            self.assertFalse(audit["decision"]["outerOosAuthorized"])
            self.assertFalse(audit["protocol"]["candidateFittingPerformed"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])
            self.assertTrue(all(
                item["heldOutLabelsAvailableToTransformOrThreshold"] is False
                and item["outerRowsAvailable"] is False
                for item in audit["candidateFoldAssignments"]
            ))

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a.json")

    def test_rejects_policy_that_opens_outer_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prereg = json.loads(_preregistration().read_text(encoding="utf-8"))
            prereg["authorizationPolicy"]["outerOosAuthorized"] = True
            unsafe = root / "unsafe-preregistration.json"
            unsafe.write_text(json.dumps(prereg), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or policy are invalid"):
                _write(root / "out.json", preregistration=unsafe)

    def test_rejects_manifest_eligibility_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = json.loads(_manifest().read_text(encoding="utf-8"))
            manifest["candidates"][0]["eligibility"]["plannedLeaveOneOutFoldCount"] = 5
            unsafe = root / "unsafe-manifest.json"
            unsafe.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or policy are invalid"):
                _write(root / "out.json", manifest=unsafe)


def _contract() -> Path:
    return Path("models/e14-four-detector-loeo-readiness-contract-v2.json")


def _preregistration() -> Path:
    return Path("models/e14-four-detector-loeo-preregistration-v2.json")


def _manifest() -> Path:
    return Path("models/e14-generated-four-detector-candidates-v2.json")


def _write(
    output: Path,
    preregistration: Path | None = None,
    manifest: Path | None = None,
) -> Path:
    return write_e14_loeo_preregistration_audit_v2(
        _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        manifest or _manifest(),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-candidate-manifest-audit-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/e14-mechanism-feature-foundation-v2.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v2.json"),
        Path("models/e14-four-detector-candidate-generation-protocol-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-protocol-readiness-audit-v2.json"),
        preregistration or _preregistration(),
        Path("models/e14-four-detector-loeo-preregistration-schema-v2.json"),
        output,
    )


if __name__ == "__main__":
    unittest.main()
