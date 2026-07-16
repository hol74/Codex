from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_publication_metadata_collection_preflight import STATUS, write_e14_fdic_publication_metadata_collection_preflight


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14FdicPublicationMetadataCollectionPreflightTests(unittest.TestCase):
    def test_missing_request_catalog_blocks_before_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_call(Path(directory) / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(["EXACT_SEED_URLS_NOT_FROZEN", "REQUEST_TEMPLATES_NOT_HASH_BOUND"], audit["blockers"])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertFalse(audit["decision"]["metadataNetworkCollectionAuthorized"])
            self.assertTrue(audit["decision"]["requestCatalogRemediationAuthorized"])

    def test_output_is_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            _call(output)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(output)

    def test_mutated_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(Path("models/e14-fdic-publication-metadata-execution-plan-v1.json").read_text(encoding="utf-8"))
            plan["exactSeedUrls"] = ["https://www.fdic.gov/unfrozen"]
            mutated = root / "plan.json"
            mutated.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(root / "audit.json", plan_path=mutated)

    def test_existing_catalog_v3_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "catalog v3"):
                _call(root / "audit.json", repository_root=root)

    def test_output_inside_snapshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2/audit.json"
            with self.assertRaisesRegex(DatasetValidationError, "inside snapshot"):
                _call(output, repository_root=root)


def _call(output: Path, plan_path: Path | None = None, repository_root: Path = Path("../..")) -> Path:
    return write_e14_fdic_publication_metadata_collection_preflight(
        Path("models/e14-fdic-publication-metadata-collection-preflight-contract-v1.json"),
        Path("models/e14-fdic-publication-metadata-execution-gate-contract-v1.json"),
        DATA / "e14-fdic-publication-metadata-execution-gate-audit-v1.json",
        plan_path or Path("models/e14-fdic-publication-metadata-execution-plan-v1.json"),
        Path("models/e14-fdic-publication-metadata-collection-preflight-schema-v1.json"),
        repository_root,
        output,
    )


if __name__ == "__main__":
    unittest.main()
