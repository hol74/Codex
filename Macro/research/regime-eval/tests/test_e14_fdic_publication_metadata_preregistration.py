from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_publication_metadata_preregistration import (
    STATUS,
    write_e14_fdic_publication_metadata_preregistration,
)
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14FdicPublicationMetadataPreregistrationTests(unittest.TestCase):
    def test_preregisters_exact_79_quarter_metadata_collection_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = _call(Path(directory) / "audit.json")
            audit = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(79, len(audit["quarterIds"]))
            self.assertEqual("2006Q1", audit["quarterIds"][0])
            self.assertEqual("2025Q3", audit["quarterIds"][-1])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertEqual(0, audit["protocol"]["metadataRowsCollected"])
            self.assertTrue(audit["decision"]["metadataOnlyExecutionReviewAuthorized"])
            self.assertFalse(audit["decision"]["metadataNetworkCollectionAuthorized"])
            self.assertFalse(audit["decision"]["requestCatalogV3MaterializationAuthorized"])

    def test_output_is_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            _call(output)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(output)

    def test_noncanonical_review_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = json.loads((DATA / "e14-post2005-acquisition-remediation-independent-review-v1.json").read_text(encoding="utf-8"))
            review["decision"] = "reject"
            mutated = root / "review.json"
            mutated.write_text(json.dumps(review), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(root / "audit.json", review_path=mutated)

    def test_existing_catalog_v3_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "catalog v3"):
                _call(root / "audit.json", repository_root=root)

    def test_output_inside_snapshot_v2_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2/audit.json"
            with self.assertRaisesRegex(DatasetValidationError, "inside snapshot"):
                _call(output, repository_root=root)

    def test_schema_rejects_unexpected_nested_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_call(Path(directory) / "audit.json").read_text(encoding="utf-8"))
            audit["decision"]["unexpected"] = True
            schema = json.loads(Path("models/e14-fdic-publication-metadata-preregistration-audit-schema-v1.json").read_text(encoding="utf-8"))
            with self.assertRaisesRegex(DatasetValidationError, "closed schema"):
                _validate_schema_value(audit, schema, schema, "$")


def _call(
    output: Path,
    review_path: Path | None = None,
    repository_root: Path = Path("../.."),
) -> Path:
    return write_e14_fdic_publication_metadata_preregistration(
        Path("models/e14-fdic-publication-metadata-preregistration-contract-v1.json"),
        DATA / "e14-post2005-acquisition-remediation-proposal-v1.json",
        DATA / "e14-post2005-acquisition-remediation-audit-v1.json",
        review_path or DATA / "e14-post2005-acquisition-remediation-independent-review-v1.json",
        Path("models/e14-acquisition-remediation-independent-review-schema-v1.json"),
        Path("models/e14-fdic-publication-metadata-preregistration-plan-v1.json"),
        Path("models/e14-fdic-publication-metadata-preregistration-audit-schema-v1.json"),
        repository_root,
        output,
    )


if __name__ == "__main__":
    unittest.main()
