from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_vintage_remediation import (
    STATUS,
    write_e14_post2005_vintage_remediation_audit,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025"
SNAPSHOT = DATA / "post2005-source-snapshots-v1"
CHALLENGERS = DATA / "challengers"


class E14Post2005VintageRemediationTests(unittest.TestCase):
    def test_structural_gaps_require_policy_redesign_and_keep_acquisition_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            _write(output)
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(31, audit["inventory"]["h10MissingReleaseMonthCount"])
            self.assertEqual("2025Q3", audit["inventory"]["fdicLatestEligibleQuarterAtCutoff"])
            self.assertFalse(audit["decision"]["targetedAcquisitionPreregistrationAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["decision"]["featureTransformationAuthorized"])
            mechanisms = {item["mechanism"]: item for item in audit["mechanismAssessments"]}
            self.assertEqual("VINTAGE_FIT_PRESERVED", mechanisms["broad-market-repricing"]["status"])
            self.assertEqual("POLICY_REDESIGN_REQUIRED", mechanisms["cross-border-growth"]["status"])

    def test_updated_hash_cannot_hide_h10_gap_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads((MODEL / "e14-post2005-vintage-remediation-evidence-v1.json").read_text(encoding="utf-8"))
            h10 = next(item for item in evidence["sources"] if item["sourceId"] == "federal-reserve-h10-release-archive")
            h10["missingReleaseMonthsBeforeTaper"] = []
            evidence_path = root / "evidence.json"
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            contract = json.loads((MODEL / "e14-post2005-vintage-remediation-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["remediationEvidenceSha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "must-not-exist.json", contract_path, evidence_path)

    def test_output_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            _write(output)
            with self.assertRaisesRegex(DatasetValidationError, "Immutable"):
                _write(output)


def _write(output: Path, contract: Path | None = None, evidence: Path | None = None) -> Path:
    return write_e14_post2005_vintage_remediation_audit(
        contract or MODEL / "e14-post2005-vintage-remediation-contract-v1.json",
        CHALLENGERS / "e14-post2005-vintage-fitness-audit-v1.json",
        SNAPSHOT / "snapshot-index.json",
        SNAPSHOT / "acquisition-audit.json",
        MODEL / "e14-post2005-scope-feasibility-plan-v1.json",
        MODEL / "e14-post2005-vintage-fitness-audit-plan-v1.json",
        CHALLENGERS / "e14-post2005-source-acquisition-manifest-v1.json",
        evidence or MODEL / "e14-post2005-vintage-remediation-evidence-v1.json",
        MODEL / "e14-post2005-vintage-remediation-plan-v1.json",
        MODEL / "e14-post2005-vintage-remediation-schema-v1.json",
        output,
    )


if __name__ == "__main__":
    unittest.main()
