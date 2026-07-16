from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_acquisition_remediation import STATUS, write_e14_post2005_acquisition_remediation
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14Post2005AcquisitionRemediationTests(unittest.TestCase):
    def test_materializes_review_first_docket_without_catalog_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outputs = _write(Path(directory))
            proposal, dossier, queue, audit = [json.loads(path.read_text(encoding="utf-8")) for path in outputs]
            self.assertEqual(STATUS, proposal["status"])
            self.assertEqual(1042, proposal["catalogRemediation"][0]["expectedProviderDiscoveredReleaseCount"])
            self.assertEqual(79, proposal["catalogRemediation"][1]["expectedEligibleQuarterCount"])
            self.assertFalse(proposal["openRequirements"][0]["satisfied"])
            self.assertEqual(["20240807", "20241003"], [item["correction"]["effectiveFrom"] for item in dossier["pairs"]])
            self.assertTrue(all(item["bothRawPayloadsMustBeRetained"] and item["noRetroactiveApplication"] for item in dossier["pairs"]))
            self.assertEqual(3, len(queue["items"]))
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertFalse(audit["decision"]["requestCatalogV3MaterializationAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])

    def test_outputs_are_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root)
            with self.assertRaises(DatasetValidationError):
                _write(root)

    def test_output_inside_snapshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = Path(__file__).resolve().parents[3] / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2"
            outputs = [snapshot / name for name in ("e14-post2005-acquisition-remediation-proposal-v1.json", "e14-g5-duplicate-release-adjudication-dossier-v1.json", "e14-post2005-acquisition-remediation-review-queue-v1.json", "e14-post2005-acquisition-remediation-audit-v1.json")]
            with self.assertRaisesRegex(DatasetValidationError, "snapshot"):
                _call(outputs)
            self.assertFalse(root.joinpath("unused").exists())

    def test_noncanonical_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads(Path("models/e14-post2005-acquisition-remediation-evidence-v1.json").read_text(encoding="utf-8"))
            evidence["providerPrimaryEvidence"]["h8ReleaseCalendar"]["windowReleaseCount"] = 1043
            mutated = root / "evidence.json"
            mutated.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(_outputs(root), evidence_path=mutated)

    def test_existing_catalog_v3_in_output_directory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "e14-post2005-source-acquisition-requests-v3.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "catalog v3 already exists"):
                _write(root)

    def test_nested_schema_rejects_extra_authorization_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proposal_path = _write(Path(directory))[0]
            proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
            proposal["authorizationPolicy"]["unexpected"] = True
            schema = json.loads(Path("models/e14-post2005-acquisition-remediation-proposal-schema-v1.json").read_text(encoding="utf-8"))
            with self.assertRaisesRegex(DatasetValidationError, "closed schema"):
                _validate_schema_value(proposal, schema, schema, "$")


def _outputs(root: Path) -> list[Path]:
    return [root / name for name in ("e14-post2005-acquisition-remediation-proposal-v1.json", "e14-g5-duplicate-release-adjudication-dossier-v1.json", "e14-post2005-acquisition-remediation-review-queue-v1.json", "e14-post2005-acquisition-remediation-audit-v1.json")]


def _write(root: Path) -> tuple[Path, Path, Path, Path]:
    return _call(_outputs(root))


def _call(outputs: list[Path], evidence_path: Path | None = None) -> tuple[Path, Path, Path, Path]:
    return write_e14_post2005_acquisition_remediation(
        Path("models/e14-post2005-acquisition-remediation-contract-v1.json"),
        DATA / "e14-post2005-source-acquisition-execution-preflight-audit-v2.json",
        DATA / "e14-post2005-source-acquisition-manifest-v2.json",
        DATA / "e14-post2005-source-acquisition-requests-v2.json",
        DATA / "e14-post2005-active-source-vintage-policy-v2.json",
        evidence_path or Path("models/e14-post2005-acquisition-remediation-evidence-v1.json"),
        Path("models/e14-post2005-acquisition-remediation-plan-v1.json"),
        Path("models/e14-post2005-acquisition-remediation-proposal-schema-v1.json"),
        Path("models/e14-g5-duplicate-adjudication-dossier-schema-v1.json"),
        Path("models/e14-post2005-acquisition-remediation-review-queue-schema-v1.json"),
        Path("models/e14-acquisition-remediation-independent-review-schema-v1.json"),
        Path("models/e14-post2005-acquisition-remediation-audit-schema-v1.json"),
        *outputs,
    )


if __name__ == "__main__":
    unittest.main()
