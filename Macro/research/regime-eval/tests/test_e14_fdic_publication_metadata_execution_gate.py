from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_publication_metadata_execution_gate import (
    STATUS,
    write_e14_fdic_publication_metadata_execution_gate,
)
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14FdicPublicationMetadataExecutionGateTests(unittest.TestCase):
    def test_gate_authorizes_only_bounded_metadata_collection_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_call(Path(directory) / "gate.json").read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(["www.fdic.gov"], audit["limits"]["allowedHosts"])
            self.assertEqual(158, audit["limits"]["maximumLogicalRequests"])
            self.assertEqual(316, audit["limits"]["maximumPhysicalRequests"])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertTrue(audit["decision"]["metadataNetworkCollectionAuthorized"])
            self.assertFalse(audit["decision"]["requestCatalogV3MaterializationAuthorized"])

    def test_output_is_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "gate.json"
            _call(output)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _call(output)

    def test_noncanonical_review_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = json.loads((DATA / "e14-fdic-publication-metadata-independent-review-v1.json").read_text(encoding="utf-8"))
            review["decision"] = "reject"
            mutated = root / "review.json"
            mutated.write_text(json.dumps(review), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(root / "gate.json", review_path=mutated)

    def test_mutated_network_budget_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads(Path("models/e14-fdic-publication-metadata-execution-plan-v1.json").read_text(encoding="utf-8"))
            plan["networkPolicy"]["maximumLogicalRequests"] = 159
            mutated = root / "plan.json"
            mutated.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs"):
                _call(root / "gate.json", plan_path=mutated)

    def test_existing_catalog_v3_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data/historical-real-v12-2008-2025/challengers/e14-post2005-source-acquisition-requests-v3.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "catalog v3"):
                _call(root / "gate.json", repository_root=root)

    def test_output_inside_snapshot_v2_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v2/gate.json"
            with self.assertRaisesRegex(DatasetValidationError, "inside snapshot"):
                _call(output, repository_root=root)

    def test_schema_rejects_unexpected_decision_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit = json.loads(_call(Path(directory) / "gate.json").read_text(encoding="utf-8"))
            audit["decision"]["unexpected"] = True
            schema = json.loads(Path("models/e14-fdic-publication-metadata-execution-gate-schema-v1.json").read_text(encoding="utf-8"))
            with self.assertRaisesRegex(DatasetValidationError, "closed schema"):
                _validate_schema_value(audit, schema, schema, "$")


def _call(
    output: Path,
    review_path: Path | None = None,
    plan_path: Path | None = None,
    repository_root: Path = Path("../.."),
) -> Path:
    return write_e14_fdic_publication_metadata_execution_gate(
        Path("models/e14-fdic-publication-metadata-execution-gate-contract-v1.json"),
        Path("models/e14-fdic-publication-metadata-preregistration-contract-v1.json"),
        DATA / "e14-fdic-publication-metadata-preregistration-audit-v1.json",
        review_path or DATA / "e14-fdic-publication-metadata-independent-review-v1.json",
        Path("models/e14-fdic-publication-metadata-independent-review-schema-v1.json"),
        plan_path or Path("models/e14-fdic-publication-metadata-execution-plan-v1.json"),
        Path("models/e14-fdic-publication-metadata-execution-gate-schema-v1.json"),
        repository_root,
        output,
    )


if __name__ == "__main__":
    unittest.main()
