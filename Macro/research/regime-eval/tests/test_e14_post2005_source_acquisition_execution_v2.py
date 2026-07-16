from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_source_acquisition_execution_v2 import BLOCKED, READY, _AllowlistRedirectHandler, write_e14_post2005_source_acquisition_execution_preflight_v2


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14Post2005SourceAcquisitionExecutionV2Tests(unittest.TestCase):
    def test_realistic_discovery_gaps_block_before_event_time_and_remove_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = _write(root, root / "audit.json", _blocked_fetch)
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertEqual(4, audit["inventory"]["blockerCount"])
            self.assertEqual(["202408", "202410"], next(item["observed"] for item in audit["blockers"] if item["code"] == "G5_DUPLICATE_MONTHS_REQUIRE_ADJUDICATION"))
            self.assertEqual(3, audit["protocol"]["networkRequestsMade"])
            self.assertEqual(0, audit["protocol"]["eventTimeRequestsMade"])
            self.assertEqual(0, audit["protocol"]["fredRequestsMade"])
            self.assertFalse((root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2").exists())
            self.assertFalse((root / "data/historical-real-v12-2008-2025/.post2005-source-snapshots-v2.discovery-staging").exists())

    def test_complete_preregistered_discovery_can_authorize_only_full_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit = json.loads(_write(root, root / "audit.json", _ready_fetch).read_text(encoding="utf-8"))
            self.assertEqual(READY, audit["status"])
            self.assertTrue(audit["decision"]["fullAtomicAcquisitionAuthorized"])
            self.assertFalse(audit["decision"]["featureTransformationAuthorized"])
            self.assertEqual(0, audit["protocol"]["rawArtifactsPublished"])

    def test_off_allowlist_redirect_is_rejected_and_staging_removed(self) -> None:
        def redirected(url: str, maximum: int) -> dict[str, object]:
            result = _ready_fetch(url, maximum)
            result["redirectChain"] = [url, "https://example.invalid/bounce", result["finalUrl"]]
            return result
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(DatasetValidationError, "redirect chain"):
                _write(root, root / "audit.json", redirected)
            self.assertFalse((root / "data/historical-real-v12-2008-2025/.post2005-source-snapshots-v2.discovery-staging").exists())
            self.assertFalse((root / "audit.json").exists())

    def test_output_is_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "audit.json"
            _write(root, output, _blocked_fetch)
            with self.assertRaises(DatasetValidationError):
                _write(root, output, _blocked_fetch)

    def test_output_inside_staging_is_rejected_without_recreating_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "data/historical-real-v12-2008-2025/.post2005-source-snapshots-v2.discovery-staging"
            with self.assertRaisesRegex(DatasetValidationError, "topology"):
                _write(root, stage / "audit.json", _blocked_fetch)
            self.assertFalse(stage.exists())

    def test_fdic_pre_quarter_end_dates_do_not_count_as_publication_proof(self) -> None:
        def invalid_dates(url: str, maximum: int) -> dict[str, object]:
            result = _ready_fetch(url, maximum)
            if "fdic" in url:
                result["raw"] = result["raw"].replace(b"data-publication-date=\"", b"data-publication-date=\"2000-01-01\" data-ignored=\"")
            return result
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit = json.loads(_write(root, root / "audit.json", invalid_dates).read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertEqual(0, audit["inventory"]["fdicActualPublicationProofCount"])

    def test_h8_wrong_weekday_fails_coverage_despite_exact_count(self) -> None:
        def saturday(url: str, maximum: int) -> dict[str, object]:
            result = _ready_fetch(url, maximum)
            if "h8" in url:
                result["raw"] = result["raw"].replace(b"20060106", b"20060107")
            return result
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit = json.loads(_write(root, root / "audit.json", saturday).read_text(encoding="utf-8"))
            self.assertEqual(BLOCKED, audit["status"])
            self.assertIn("H8_DIRECT_DATED_RELEASE_VALUES_INCOMPLETE", [item["code"] for item in audit["blockers"]])

    def test_redirect_handler_refuses_off_provider_before_follow(self) -> None:
        handler = _AllowlistRedirectHandler("https://www.federalreserve.gov/releases/h8/default.htm")
        with self.assertRaisesRegex(DatasetValidationError, "before follow"):
            handler.redirect_request(None, None, 302, "Found", {}, "https://www.fdic.gov/quarterly-banking-profile")


def _blocked_fetch(url: str, maximum: int) -> dict[str, object]:
    if "h8" in url:
        raw = b'<script>$.getJSON("releaseDates.json", function(data) {})</script><h1>Assets and Liabilities of Commercial Banks</h1>'
    elif "fdic" in url:
        raw = b'<h1>Quarterly Banking Profile</h1><a href="/quarterly-banking-profile/past-quarterly-banking-profiles">Past profiles</a>'
    else:
        dates = _monthly_dates()
        dates[(2024 - 2006) * 12 + 7].append("20240807")
        dates[(2024 - 2006) * 12 + 9].append("20241003")
        raw = json.dumps(_g5_payload(dates)).encode()
    return _outcome(url, raw)


def _ready_fetch(url: str, maximum: int) -> dict[str, object]:
    if "h8" in url:
        start = date(2006, 1, 6)
        links = [f'<a href="/releases/h8/{(start + timedelta(days=index * 7)).strftime("%Y%m%d")}/">release</a>' for index in range(1043)]
        raw = ("Assets and Liabilities of Commercial Banks" + "".join(links)).encode()
    elif "fdic" in url:
        links = []
        for year in range(2006, 2026):
            for quarter in range(1, 5):
                if year == 2025 and quarter == 4:
                    continue
                quarter_end = date(year, quarter * 3, 31 if quarter in (1, 4) else 30)
                published = quarter_end + timedelta(days=60)
                links.append(f'<a data-publication-date="{published.isoformat()}" href="/quarterly-banking-profile/quarterly-banking-profile-q{quarter}-{year}">Q{quarter}</a>')
        raw = ("Quarterly Banking Profile" + "".join(links)).encode()
    else:
        raw = json.dumps(_g5_payload(_monthly_dates())).encode()
    return _outcome(url, raw)


def _monthly_dates() -> list[list[str]]:
    return [[f"{year}{month:02d}01"] for year in range(2006, 2026) for month in range(1, 13)]


def _g5_payload(dates: list[list[str]]) -> list[dict[str, object]]:
    years = []
    for year in range(2006, 2026):
        months = []
        for month in range(1, 13):
            index = (year - 2006) * 12 + month - 1
            months.append({"MonthName": str(month), "MonthValue": f"{year}{month:02d}", "Dates": dates[index]})
        years.append({"yearValue": str(year), "Months": months})
    return years


def _outcome(url: str, raw: bytes) -> dict[str, object]:
    return {"raw": raw, "statusCode": 200, "finalUrl": url, "redirectChain": [url], "contentType": "application/json" if url.endswith(".json") else "text/html"}


def _write(root: Path, output: Path, fetch) -> Path:
    return write_e14_post2005_source_acquisition_execution_preflight_v2(
        Path("models/e14-post2005-source-acquisition-execution-contract-v2.json"),
        DATA / "e14-post2005-source-acquisition-manifest-v2.json",
        DATA / "e14-post2005-source-acquisition-requests-v2.json",
        DATA / "e14-post2005-source-execution-gate-audit-v3.json",
        Path("models/e14-post2005-source-acquisition-execution-plan-v2.json"),
        Path("models/e14-post2005-source-acquisition-execution-preflight-schema-v2.json"),
        root, output, fetch=fetch, executed_at_utc="2026-07-16T18:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()
