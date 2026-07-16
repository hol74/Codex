from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_targeted_revision import (
    TARGET_ID,
    write_e14_post2005_targeted_revision,
    write_e14_post2005_targeted_review_ingestion,
)


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14Post2005TargetedRevisionTests(unittest.TestCase):
    def test_changes_only_archegos_and_preserves_accepted_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, audit_path = _revise(root)
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            original = json.loads((DATA / "e14-post2005-reviewed-queue-v1.json").read_text(encoding="utf-8"))
            revised = {item["dossierId"]: item for item in queue["dossiers"]}
            prior = {item["dossierId"]: item for item in original["dossiers"]}
            self.assertNotEqual(prior[TARGET_ID]["sha256"], revised[TARGET_ID]["sha256"])
            self.assertEqual(prior["e14-dossier-post2005-london-whale-contained-2012-banking-credit"], revised["e14-dossier-post2005-london-whale-contained-2012-banking-credit"])
            dossier = json.loads((root / "revised" / revised[TARGET_ID]["fileName"]).read_text(encoding="utf-8"))
            self.assertEqual("2021-06-01", dossier["lastMonth"])
            self.assertTrue(any(item["locator"].endswith("/qbp.pdf") for item in dossier["evidenceItems"]))
            self.assertFalse(audit["protocol"]["scopeActivated"])

    def test_strict_targeted_acceptance_opens_only_separate_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, revision_audit = _revise(root)
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            target = next(item for item in queue["dossiers"] if item["dossierId"] == TARGET_ID)
            receipts = root / "receipts"
            receipts.mkdir()
            receipt = _receipt(target)
            (receipts / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            _, audit_path = write_e14_post2005_targeted_review_ingestion(
                queue_path, revision_audit, Path("models/e14-independent-review-schema-v2.json"),
                receipts, root / "accepted-queue.json", root / "ingestion.json",
            )
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertTrue(audit["decision"]["allDossiersAccepted"])
            self.assertTrue(audit["decision"]["separateActivationGateAuthorized"])
            self.assertFalse(audit["decision"]["scopeActivated"])

    def test_rejects_targeted_receipt_from_revision_author(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, revision_audit = _revise(root)
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            target = next(item for item in queue["dossiers"] if item["dossierId"] == TARGET_ID)
            receipts = root / "receipts"
            receipts.mkdir()
            receipt = _receipt(target)
            receipt["reviewerId"] = queue["dossierAuthor"]
            (receipts / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "not independent"):
                write_e14_post2005_targeted_review_ingestion(
                    queue_path, revision_audit, Path("models/e14-independent-review-schema-v2.json"),
                    receipts, root / "bad-queue.json", root / "bad-audit.json",
                )


def _revise(root: Path) -> tuple[Path, Path]:
    return write_e14_post2005_targeted_revision(
        Path("models/e14-post2005-targeted-revision-contract-v1.json"),
        DATA / "e14-post2005-reviewed-queue-v1.json",
        DATA / "e14-post2005-review-ingestion-audit-v1.json",
        Path("models/e14-episode-dossier-schema-v1.json"),
        DATA / "e14-post2005-dossiers-v1",
        root / "revised", root / "bundle", root / "queue.json", root / "audit.json",
    )


def _receipt(manifest: dict[str, object]) -> dict[str, object]:
    return {
        "schemaVersion": 2,
        "reviewId": "e14-review-post2005-archegos-targeted-independent-test",
        "dossierId": TARGET_ID,
        "dossierSha256": manifest["sha256"],
        "reviewerId": "independent-targeted-test-reviewer",
        "reviewerAffiliation": "synthetic-test-only",
        "independenceDeclaration": "I did not author the dossier or its evidence pack and reviewed the cited evidence independently.",
        "reviewedAt": "2026-07-16",
        "decision": "accept",
        "rationale": "Synthetic strict targeted receipt proving that acceptance authorizes only a separate scope gate and cannot activate or acquire data.",
        "checks": {
            "sourceLocatorsOpened": True,
            "mechanismClaimSupported": True,
            "boundariesSupported": True,
            "counterEvidenceConsidered": True,
            "noModelOutputUsed": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
