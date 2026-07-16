from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_source_acquisition_execution import (
    STATUS,
    write_e14_post2005_atomic_source_snapshot,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
KEY = "a" * 32


class E14Post2005SourceAcquisitionExecutionTests(unittest.TestCase):
    def test_publishes_all_eleven_artifacts_by_atomic_rename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, index_path, audit_path = _write(root, _fake_download)
            self.assertTrue(snapshot.is_dir())
            self.assertFalse((snapshot.parent / f".{snapshot.name}.staging").exists())
            index = json.loads(index_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, index["status"])
            self.assertEqual(23, index["inventory"]["artifactCount"])
            self.assertEqual(7, index["inventory"]["sourceCount"])
            self.assertTrue(index["checks"]["publishedAtomically"])
            self.assertFalse(index["authorizationPolicy"]["featureTransformationAuthorized"])
            self.assertEqual(16, index["inventory"]["eventTimeReadyArtifactCount"])
            self.assertEqual(0, audit["protocol"]["featuresTransformed"])
            self.assertNotIn(KEY, index_path.read_text(encoding="utf-8"))

    def test_download_failure_removes_staging_and_publishes_nothing(self) -> None:
        calls = 0

        def failing(url: str, destination: Path, maximum: int) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError("synthetic provider failure")
            return _fake_download(url, destination, maximum)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(DatasetValidationError, "synthetic provider failure"):
                _write(root, failing)
            snapshot = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v1"
            self.assertFalse(snapshot.exists())
            self.assertFalse((snapshot.parent / f".{snapshot.name}.staging").exists())

    def test_invalid_payload_fails_before_publish(self) -> None:
        def invalid(url: str, destination: Path, maximum: int) -> dict[str, object]:
            result = _fake_download(url, destination, maximum)
            if destination.name.startswith("initial-release-"):
                destination.write_text('{"observations": []}', encoding="utf-8")
            return result

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(DatasetValidationError, "metadata or window is invalid"):
                _write(root, invalid)


def _fake_download(url: str, destination: Path, maximum: int) -> dict[str, object]:
    if destination.suffix in {".zip", ".xlsx"}:
        destination.write_bytes(b"PK\x03\x04synthetic")
    elif destination.name == "release-index.html":
        destination.write_text("Assets and Liabilities of Commercial Banks", encoding="utf-8")
    elif destination.name == "past-qbp-index.html":
        destination.write_text("Quarterly Banking Profile", encoding="utf-8")
    elif destination.name == "about.html":
        destination.write_text("Foreign Exchange Rates", encoding="utf-8")
    else:
        query = parse_qs(urlparse(url).query)
        realtime = query["realtime_start"][0]
        destination.write_text(json.dumps({"observations": [{"realtime_start": realtime, "realtime_end": realtime, "date": realtime, "value": "1.0"}]}), encoding="utf-8")
    return {"statusCode": 200, "finalUrl": f"https://{urlparse(url).hostname}/download", "contentType": "application/octet-stream"}


def _write(root: Path, downloader) -> tuple[Path, Path, Path]:
    return write_e14_post2005_atomic_source_snapshot(
        Path("models/e14-post2005-source-acquisition-execution-contract-v1.json"),
        DATA / "e14-post2005-source-acquisition-manifest-v1.json",
        DATA / "e14-post2005-source-execution-gate-audit-v1.json",
        Path("models/e14-post2005-source-acquisition-requests-v1.json"),
        Path("models/e14-post2005-source-snapshot-schema-v1.json"),
        root,
        environment={"FRED_API_KEY": KEY},
        downloader=downloader,
        retrieved_at_utc="2026-07-16T12:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()
