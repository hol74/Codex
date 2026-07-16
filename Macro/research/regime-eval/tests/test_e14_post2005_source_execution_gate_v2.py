from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_source_execution_gate_v2 import BLOCKED, READY, write_e14_post2005_source_execution_gate_v2


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
KEY = "a" * 32


class E14Post2005SourceExecutionGateV2Tests(unittest.TestCase):
    def test_all_metadata_probes_authorize_only_separate_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _write(Path(directory) / "audit.json", {"FRED_API_KEY": KEY}, _passing_probe)
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(READY, audit["status"])
            self.assertEqual(7, audit["inventory"]["passedProbeCount"])
            self.assertEqual(11, audit["inventory"]["requestTemplateCount"])
            self.assertTrue(audit["decision"]["separateSourceAcquisitionExecutionAuthorized"])
            self.assertEqual(0, audit["protocol"]["requestTemplatesExecuted"])
            self.assertEqual(0, audit["protocol"]["observationsAcquired"])
            self.assertNotIn(KEY, output.read_text(encoding="utf-8"))

    def test_missing_credential_blocks_four_fred_probes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_write(Path(directory) / "audit.json", {}, _passing_probe).read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertEqual(4, audit["inventory"]["failedProbeCount"])
            self.assertEqual(3, audit["protocol"]["networkRequestsMade"])

    def test_off_allowlist_redirect_fails_closed(self) -> None:
        def redirected(url: str, marker: str, timeout: int, maximum: int) -> dict[str, object]:
            result = _passing_probe(url, marker, timeout, maximum)
            if "DGS2" in url:
                result["finalUrl"] = "https://example.invalid/redirect"
            return result
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_write(Path(directory) / "audit.json", {"FRED_API_KEY": KEY}, redirected).read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertEqual(1, audit["inventory"]["failedProbeCount"])
            self.assertFalse(audit["checks"]["redirectsStayedOnAllowlist"])

    def test_off_allowlist_intermediate_redirect_fails_even_if_final_host_is_allowed(self) -> None:
        def bounced(url: str, marker: str, timeout: int, maximum: int) -> dict[str, object]:
            result = _passing_probe(url, marker, timeout, maximum)
            if "DGS2" in url:
                result["redirectChain"] = [url, "https://example.invalid/bounce", url]
            return result
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_write(Path(directory) / "audit.json", {"FRED_API_KEY": KEY}, bounced).read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertFalse(audit["checks"]["redirectsStayedOnAllowlist"])

    def test_marker_failure_blocks_g5(self) -> None:
        def missing_marker(url: str, marker: str, timeout: int, maximum: int) -> dict[str, object]:
            result = _passing_probe(url, marker, timeout, maximum)
            if "releaseDates" in url:
                result["expectedMarkerFound"] = False
            return result
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_write(Path(directory) / "audit.json", {"FRED_API_KEY": KEY}, missing_marker).read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertEqual("federal-reserve-g5-release-archive", next(item["sourceId"] for item in audit["probeResults"] if not item["passed"]))

    def test_unexpected_content_type_fails_closed(self) -> None:
        def wrong_type(url: str, marker: str, timeout: int, maximum: int) -> dict[str, object]:
            result = _passing_probe(url, marker, timeout, maximum)
            if "DGS2" in url:
                result["contentType"] = "text/html"
            return result
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_write(Path(directory) / "audit.json", {"FRED_API_KEY": KEY}, wrong_type).read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])

    def test_canonical_snapshot_root_is_protected_when_manifest_is_copied(self) -> None:
        protected = Path(__file__).resolve().parents[3] / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2/gate-audit.json"
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "manifest.json"
            copied.write_bytes((DATA / "e14-post2005-source-acquisition-manifest-v2.json").read_bytes())
            with self.assertRaises(DatasetValidationError):
                write_e14_post2005_source_execution_gate_v2(
                    Path("models/e14-post2005-source-execution-gate-contract-v2.json"), copied,
                    DATA / "e14-post2005-source-acquisition-requests-v2.json", DATA / "e14-post2005-source-acquisition-preregistration-audit-v2.json",
                    Path("models/e14-post2005-source-execution-gate-plan-v2.json"), Path("models/e14-post2005-source-execution-gate-schema-v2.json"),
                    protected, environment={"FRED_API_KEY": KEY}, probe=_passing_probe,
                )

    def test_output_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            _write(output, {"FRED_API_KEY": KEY}, _passing_probe)
            with self.assertRaises(DatasetValidationError):
                _write(output, {"FRED_API_KEY": KEY}, _passing_probe)

    def test_v3_retry_changes_only_g5_marker_and_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = write_e14_post2005_source_execution_gate_v2(
                Path("models/e14-post2005-source-execution-gate-contract-v3.json"),
                DATA / "e14-post2005-source-acquisition-manifest-v2.json", DATA / "e14-post2005-source-acquisition-requests-v2.json",
                DATA / "e14-post2005-source-acquisition-preregistration-audit-v2.json", Path("models/e14-post2005-source-execution-gate-plan-v3.json"),
                Path("models/e14-post2005-source-execution-gate-schema-v2.json"), Path(directory) / "audit-v3.json",
                environment={"FRED_API_KEY": KEY}, probe=_passing_probe, executed_at_utc="2026-07-16T17:00:00Z",
            )
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(READY, audit["status"])
            plan_v2 = json.loads(Path("models/e14-post2005-source-execution-gate-plan-v2.json").read_text(encoding="utf-8"))
            plan_v3 = json.loads(Path("models/e14-post2005-source-execution-gate-plan-v3.json").read_text(encoding="utf-8"))
            self.assertEqual("releaseDate", plan_v2["probes"][4]["expectedMarker"])
            self.assertEqual("MonthValue", plan_v3["probes"][4]["expectedMarker"])


def _passing_probe(url: str, marker: str, timeout: int, maximum: int) -> dict[str, object]:
    content_type = "application/json" if "api.stlouisfed.org" in url or "releaseDates.json" in url else "text/html; charset=utf-8"
    return {"statusCode": 200, "finalUrl": url, "contentType": content_type, "bytesInspected": min(maximum, 512), "expectedMarkerFound": True}


def _write(path: Path, environment: dict[str, str], probe) -> Path:
    return write_e14_post2005_source_execution_gate_v2(
        Path("models/e14-post2005-source-execution-gate-contract-v2.json"),
        DATA / "e14-post2005-source-acquisition-manifest-v2.json",
        DATA / "e14-post2005-source-acquisition-requests-v2.json",
        DATA / "e14-post2005-source-acquisition-preregistration-audit-v2.json",
        Path("models/e14-post2005-source-execution-gate-plan-v2.json"),
        Path("models/e14-post2005-source-execution-gate-schema-v2.json"),
        path, environment=environment, probe=probe, executed_at_utc="2026-07-16T16:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()
