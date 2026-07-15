from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_candidate_protocol_v2 import write_e14_candidate_protocol_v2


class E14CandidateProtocolV2Tests(unittest.TestCase):
    def test_freezes_exact_28_id_protocol_without_generating_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_a = _write(root / "a")
            outputs_b = _write(root / "b")
            for left, right in zip(outputs_a, outputs_b):
                self.assertEqual(left.read_bytes(), right.read_bytes())

            protocol = json.loads(outputs_a[0].read_text(encoding="utf-8"))
            audit = json.loads(outputs_a[1].read_text(encoding="utf-8"))
            roster = json.loads(Path("models/e14-four-detector-readiness-roster-v2.json").read_text())

            self.assertEqual(28, protocol["candidateBudget"])
            self.assertEqual(
                [item["candidateId"] for item in roster["candidates"]],
                protocol["candidateIds"],
            )
            self.assertEqual(7, sum(item["profileCount"] for item in protocol["detectors"].values()))
            self.assertEqual(
                protocol["fundingBoundarySensitivity"],
                json.loads(Path("models/e14-four-detector-readiness-policy-v2.json").read_text())["fundingBoundarySensitivity"],
            )
            self.assertTrue(audit["checks"]["candidateIdRecomputationAbsent"])
            self.assertTrue(audit["decision"]["candidateManifestGenerationAuthorized"])
            self.assertFalse(audit["decision"]["candidateFittingAuthorized"])
            self.assertFalse(audit["decision"]["outerOosAuthorized"])
            self.assertFalse(audit["protocol"]["candidateManifestGenerated"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_plan_that_opens_fitting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(_plan().read_text(encoding="utf-8"))
            plan["authorizationPolicy"]["candidateFittingAuthorized"] = True
            unsafe = root / "unsafe-plan.json"
            unsafe.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out", plan=unsafe)

    def test_rejects_roster_id_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            roster = json.loads(_roster().read_text(encoding="utf-8"))
            roster["candidates"][0]["candidateId"] = "e14-broad-mutated"
            unsafe = root / "unsafe-roster.json"
            unsafe.write_text(json.dumps(roster), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or governance are invalid"):
                _write(root / "out", roster=unsafe)


def _contract() -> Path:
    return Path("models/e14-four-detector-protocol-readiness-contract-v2.json")


def _plan() -> Path:
    return Path("models/e14-four-detector-candidate-protocol-plan-v2.json")


def _roster() -> Path:
    return Path("models/e14-four-detector-readiness-roster-v2.json")


def _write(
    root: Path,
    plan: Path | None = None,
    roster: Path | None = None,
) -> tuple[Path, Path]:
    return write_e14_candidate_protocol_v2(
        _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/e14-mechanism-feature-foundation-v2.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v2.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v2.json"),
        roster or _roster(),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-readiness-audit-v2.json"),
        Path("models/e14-four-detector-readiness-policy-v2.json"),
        plan or _plan(),
        Path("models/e14-four-detector-candidate-protocol-schema-v2.json"),
        root / "protocol.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
