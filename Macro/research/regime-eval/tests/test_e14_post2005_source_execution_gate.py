from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.e14_post2005_source_execution_gate import (
    BLOCKED,
    READY,
    write_e14_post2005_source_execution_gate,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
KEY = "a" * 32


class E14Post2005SourceExecutionGateTests(unittest.TestCase):
    def test_all_metadata_probes_authorize_only_raw_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _write(Path(directory) / "audit.json", {"FRED_API_KEY": KEY}, _passing_probe)
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(READY, audit["status"])
            self.assertEqual(7, audit["inventory"]["passedProbeCount"])
            self.assertTrue(audit["decision"]["sourceAcquisitionExecutionAuthorized"])
            self.assertFalse(audit["decision"]["featureTransformationAuthorized"])
            self.assertEqual(0, audit["protocol"]["observationsAcquired"])
            self.assertNotIn(KEY, output.read_text(encoding="utf-8"))

    def test_missing_credential_blocks_all_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _write(Path(directory) / "audit.json", {}, _passing_probe)
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertFalse(audit["decision"]["sourceAcquisitionExecutionAuthorized"])
            self.assertEqual(4, audit["inventory"]["failedProbeCount"])
            self.assertEqual(3, audit["protocol"]["networkRequestsMade"])

    def test_off_allowlist_redirect_fails_closed(self) -> None:
        def redirected(url: str, marker: str, timeout: int, maximum: int) -> dict[str, object]:
            result = _passing_probe(url, marker, timeout, maximum)
            if "DGS2" in url:
                result["finalUrl"] = "https://example.invalid/redirect"
            return result

        with tempfile.TemporaryDirectory() as directory:
            output = _write(Path(directory) / "audit.json", {"FRED_API_KEY": KEY}, redirected)
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertEqual(1, audit["inventory"]["failedProbeCount"])
            self.assertFalse(audit["decision"]["sourceAcquisitionExecutionAuthorized"])


def _passing_probe(url: str, marker: str, timeout: int, maximum: int) -> dict[str, object]:
    return {"statusCode": 200, "finalUrl": url, "contentType": "application/json", "bytesInspected": min(maximum, 512), "expectedMarkerFound": True}


def _write(path: Path, environment: dict[str, str], probe) -> Path:
    return write_e14_post2005_source_execution_gate(
        Path("models/e14-post2005-source-execution-gate-contract-v1.json"),
        DATA / "e14-post2005-source-acquisition-manifest-v1.json",
        DATA / "e14-post2005-source-acquisition-preregistration-audit-v1.json",
        Path("models/e14-post2005-source-execution-gate-plan-v1.json"),
        Path("models/e14-post2005-source-execution-gate-schema-v1.json"),
        path,
        environment=environment,
        probe=probe,
        executed_at_utc="2026-07-16T12:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()
