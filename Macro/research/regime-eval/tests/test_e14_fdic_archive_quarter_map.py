from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_quarter_map import (
    STATUS,
    UNRESOLVED_REASON,
    write_e14_fdic_archive_quarter_map,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")
MODELS = Path("models")


class E14FdicArchiveQuarterMapTests(unittest.TestCase):
    def test_materializes_exact_offline_79_entry_map(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            map_path, audit_path = _call(Path(directory))
            mapping = json.loads(map_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, mapping["status"])
            self.assertEqual(79, len(mapping["entries"]))
            self.assertEqual("2006Q1", mapping["entries"][0]["quarterId"])
            self.assertEqual("2025Q3", mapping["entries"][-1]["quarterId"])
            self.assertTrue(all(item["unresolvedReason"] == UNRESOLVED_REASON for item in mapping["entries"]))
            self.assertTrue(all(item["runtimeDiscoveryAuthorized"] is False for item in mapping["entries"]))
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertEqual(79, audit["inventory"]["unresolvedEntryCount"])
            self.assertFalse(audit["decision"]["replacementExecutionGateAuthorized"])

    def test_source_roster_and_urls_are_preserved_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            map_path, _ = _call(Path(directory))
            mapping = json.loads(map_path.read_text(encoding="utf-8"))
            source = json.loads((DATA / "e14-fdic-publication-metadata-requests-v1.json").read_text(encoding="utf-8"))
            expected = [(item["quarterId"], item["providerPrimaryUrl"]) for item in source["quarterRequests"]]
            actual = [(item["quarterId"], item["providerPrimaryUrl"]) for item in mapping["entries"]]
            self.assertEqual(expected, actual)

    def test_outputs_are_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _call(root)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(root)

    def test_mutated_catalog_is_rejected_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.json"
            catalog.write_bytes((DATA / "e14-fdic-publication-metadata-requests-v1.json").read_bytes() + b"\n")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(root / "outputs", request_catalog=catalog)

    def test_existing_catalog_v3_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forbidden = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
            forbidden.parent.mkdir(parents=True)
            forbidden.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "catalog v3"):
                _call(root / "outputs", repository_root=root)


def _call(
    output_root: Path,
    *,
    request_catalog: Path | None = None,
    repository_root: Path = Path("../.."),
) -> tuple[Path, Path]:
    return write_e14_fdic_archive_quarter_map(
        MODELS / "e14-fdic-archive-quarter-map-contract-v1.json",
        request_catalog or DATA / "e14-fdic-publication-metadata-requests-v1.json",
        DATA / "e14-fdic-publication-metadata-request-catalog-independent-review-v1.json",
        MODELS / "e14-fdic-archive-quarter-map-plan-v1.json",
        MODELS / "e14-fdic-archive-quarter-map-schema-v1.json",
        MODELS / "e14-fdic-archive-quarter-map-audit-schema-v1.json",
        repository_root,
        output_root / "map.json",
        output_root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
