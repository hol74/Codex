from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_source_acquisition import (
    STATUS,
    write_e14_post2005_source_acquisition_manifest,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14Post2005SourceAcquisitionTests(unittest.TestCase):
    def test_freezes_seven_sources_without_acquiring_observations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path, audit_path = _write(root / "one")
            manifest_path_2, audit_path_2 = _write(root / "two")
            self.assertEqual(manifest_path.read_bytes(), manifest_path_2.read_bytes())
            self.assertEqual(audit_path.read_bytes(), audit_path_2.read_bytes())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, manifest["status"])
            self.assertEqual(7, len(manifest["sources"]))
            self.assertEqual(4, len(manifest["featureFamilies"]))
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertEqual(0, audit["protocol"]["observationsAcquired"])
            self.assertFalse(audit["decision"]["sourceAcquisitionExecutionAuthorized"])
            self.assertFalse(audit["decision"]["featureTransformationAuthorized"])
            self.assertFalse(audit["decision"]["outerOosAuthorized"])

    def test_fails_closed_when_a_source_is_not_metadata_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads(Path("models/e14-post2005-source-feasibility-evidence-v1.json").read_text(encoding="utf-8"))
            evidence["sources"][0]["vintageProofComplete"] = False
            evidence_path = root / "evidence.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            contract = json.loads(Path("models/e14-post2005-source-acquisition-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["sourceFeasibilityEvidenceSha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract_path=contract_path, evidence_path=evidence_path)

    def test_rejects_plan_that_authorizes_network_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(Path("models/e14-post2005-source-acquisition-plan-v1.json").read_text(encoding="utf-8"))
            plan["authorizationPolicy"]["sourceAcquisitionExecutionAuthorized"] = True
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            contract = json.loads(Path("models/e14-post2005-source-acquisition-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["sourceAcquisitionPlanSha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract_path=contract_path, plan_path=plan_path)


def _write(
    root: Path,
    contract_path: Path = Path("models/e14-post2005-source-acquisition-contract-v1.json"),
    evidence_path: Path = Path("models/e14-post2005-source-feasibility-evidence-v1.json"),
    plan_path: Path = Path("models/e14-post2005-source-acquisition-plan-v1.json"),
) -> tuple[Path, Path]:
    return write_e14_post2005_source_acquisition_manifest(
        contract_path,
        DATA / "us-financial-stress-post2005-v1.json",
        DATA / "e14-post2005-scope-activation-audit-v1.json",
        Path("models/e14-post2005-scope-feasibility-plan-v1.json"),
        evidence_path,
        plan_path,
        Path("models/e14-post2005-source-acquisition-schema-v1.json"),
        root / "manifest.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
