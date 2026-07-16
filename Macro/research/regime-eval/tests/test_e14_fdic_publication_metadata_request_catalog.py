from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_publication_metadata_request_catalog import STATUS, write_e14_fdic_publication_metadata_request_catalog


DATA = Path("../../data/historical-real-v12-2008-2025")


class E14FdicPublicationMetadataRequestCatalogTests(unittest.TestCase):
    def test_preregisters_exact_79_quarter_catalog_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog_path, audit_path = _call(Path(directory))
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, catalog["status"])
            self.assertEqual(79, len(catalog["quarterRequests"]))
            self.assertEqual("2006Q1", catalog["quarterRequests"][0]["quarterId"])
            self.assertEqual("2025Q3", catalog["quarterRequests"][-1]["quarterId"])
            self.assertEqual(["www.fdic.gov", "archive.fdic.gov"], catalog["allowedHostsProposed"])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertFalse(audit["decision"]["metadataNetworkCollectionAuthorized"])
            self.assertFalse(audit["decision"]["archiveHostExtensionAuthorized"])

    def test_templates_are_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog_path, _ = _call(Path(directory))
            templates = json.loads(catalog_path.read_text(encoding="utf-8"))["requestTemplates"]
            self.assertEqual(3, len(templates))
            self.assertTrue(all(len(item["templateSha256"]) == 64 for item in templates))

    def test_outputs_are_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _call(root)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(root)

    def test_mutated_snapshot_is_rejected_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = root / "past-qbp-index.html"
            snapshot.write_bytes((DATA / "post2005-source-snapshots-v1/fdic/qbp/past-qbp-index.html").read_bytes() + b"\n")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(root / "outputs", snapshot=snapshot)

    def test_existing_catalog_v3_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forbidden = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
            forbidden.parent.mkdir(parents=True)
            forbidden.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "catalog v3"):
                _call(root / "outputs", repository_root=root)


def _call(output_root: Path, *, snapshot: Path | None = None, repository_root: Path = Path("../..")) -> tuple[Path, Path]:
    return write_e14_fdic_publication_metadata_request_catalog(
        Path("models/e14-fdic-publication-metadata-request-catalog-contract-v1.json"),
        DATA / "challengers/e14-fdic-publication-metadata-collection-preflight-audit-v1.json",
        DATA / "challengers/e14-fdic-publication-metadata-preregistration-audit-v1.json",
        snapshot or DATA / "post2005-source-snapshots-v1/fdic/qbp/past-qbp-index.html",
        Path("models/e14-fdic-publication-metadata-request-catalog-plan-v1.json"),
        Path("models/e14-fdic-publication-metadata-request-catalog-schema-v1.json"),
        Path("models/e14-fdic-publication-metadata-request-catalog-audit-schema-v1.json"),
        repository_root,
        output_root / "catalog.json",
        output_root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
