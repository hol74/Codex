from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_hard_negative_targeted_revision import write_e14_hard_negative_targeted_revision


BASE = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14HardNegativeTargetedRevisionTests(unittest.TestCase):
    def test_preserves_fourteen_accepts_and_replaces_unsupported_mechanism(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, audit_path = _write(root)
            queue = json.loads(queue_path.read_text())
            audit = json.loads(audit_path.read_text())
            base = json.loads((BASE / "e14-independent-review-queue-v7.json").read_text())

            self.assertEqual("EXPANSION_TARGETED_REREVIEW_REQUIRED", queue["status"])
            self.assertEqual(16, len(queue["dossiers"]))
            self.assertEqual(base["dossiers"][:12], queue["dossiers"][:12])
            self.assertEqual(base["dossiers"][14:], queue["dossiers"][14:])
            self.assertNotIn("e14-dossier-repo-stress-2019-cross-border-growth-hard-negative",
                             {item["dossierId"] for item in queue["dossiers"]})
            self.assertIn("e14-dossier-flash-crash-2010-cross-border-growth-hard-negative",
                          {item["dossierId"] for item in queue["dossiers"]})
            self.assertEqual(14, audit["inventory"]["preservedAcceptedDossierCount"])
            self.assertEqual(1, audit["inventory"]["revisedDossierCount"])
            self.assertEqual(1, audit["inventory"]["replacedDossierCount"])
            self.assertTrue(audit["checks"]["fourteenAcceptedManifestsPreservedByteIdentically"])
            self.assertFalse(audit["decision"]["hardNegativeCoverageGateAuthorized"])

    def test_outputs_are_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root)

    def test_second_revision_changes_only_remaining_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, audit_path = write_e14_hard_negative_targeted_revision(
                Path("models/e14-hard-negative-targeted-revision-pack-v2.json"),
                BASE / "e14-independent-review-queue-v9.json",
                BASE / "e14-hard-negative-targeted-review-ingestion-audit-v1.json",
                Path("models/e14-episode-dossier-schema-v1.json"),
                Path("models/e14-independent-review-schema-v2.json"),
                BASE / "e14-hard-negative-expansion-revised-dossiers-v1",
                root / "dossiers", root / "bundle", root / "queue.json", root / "audit.json",
            )
            queue = json.loads(queue_path.read_text())
            audit = json.loads(audit_path.read_text())
            base = json.loads((BASE / "e14-independent-review-queue-v9.json").read_text())
            changed = {"e14-dossier-flash-crash-2010-cross-border-growth-hard-negative"}
            for item in base["dossiers"]:
                if item["dossierId"] not in changed:
                    self.assertEqual(item, next(value for value in queue["dossiers"]
                                                if value["dossierId"] == item["dossierId"]))
            self.assertEqual(15, audit["inventory"]["preservedAcceptedDossierCount"])
            self.assertTrue(audit["checks"]["allAcceptedManifestsPreservedByteIdentically"])


def _write(root: Path) -> tuple[Path, Path]:
    return write_e14_hard_negative_targeted_revision(
        Path("models/e14-hard-negative-targeted-revision-pack-v1.json"),
        BASE / "e14-independent-review-queue-v7.json",
        BASE / "e14-hard-negative-expansion-review-ingestion-audit-v2.json",
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        BASE / "e14-hard-negative-expansion-dossiers-v1",
        root / "dossiers", root / "bundle", root / "queue.json", root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
