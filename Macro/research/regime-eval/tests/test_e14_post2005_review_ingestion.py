from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_review_ingestion import write_e14_post2005_review_ingestion


class E14Post2005ReviewIngestionTests(unittest.TestCase):
    def test_missing_receipts_fail_closed_without_scope_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, audit_path = _write(root / "a", root / "missing")
            queue_path_2, audit_path_2 = _write(root / "b", root / "missing")
            self.assertEqual(queue_path.read_bytes(), queue_path_2.read_bytes())
            self.assertEqual(audit_path.read_bytes(), audit_path_2.read_bytes())
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual("POST_2005_INDEPENDENT_REVIEW_INCOMPLETE", audit["status"])
            self.assertEqual(0, audit["inventory"]["receiptCount"])
            self.assertFalse(audit["decision"]["independentReviewComplete"])
            self.assertFalse(audit["decision"]["scopeActivated"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])

    def test_two_strict_synthetic_receipts_open_only_separate_activation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = root / "receipts"
            receipts.mkdir()
            queue = json.loads(_queue().read_text(encoding="utf-8"))
            for index, dossier in enumerate(queue["dossiers"], 1):
                payload = _receipt(dossier, f"independent-reviewer-{index}")
                (receipts / f"receipt-{index}.json").write_text(json.dumps(payload), encoding="utf-8")
            _, audit_path = _write(root / "out", receipts)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual("POST_2005_REVIEW_ACCEPTED_SEPARATE_ACTIVATION_GATE_REQUIRED", audit["status"])
            self.assertEqual(2, audit["inventory"]["acceptedCount"])
            self.assertTrue(audit["decision"]["separateActivationGateAuthorized"])
            self.assertFalse(audit["decision"]["scopeActivated"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])

    def test_rejects_receipt_with_wrong_dossier_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = root / "receipts"
            receipts.mkdir()
            dossier = json.loads(_queue().read_text(encoding="utf-8"))["dossiers"][0]
            payload = _receipt(dossier, "independent-reviewer")
            payload["dossierSha256"] = "0" * 64
            (receipts / "bad.json").write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "invalid or not independent"):
                _write(root / "out", receipts)
            self.assertFalse((root / "out" / "audit.json").exists())


def _queue() -> Path:
    return Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-review-queue-v1.json")


def _receipt(dossier: dict[str, object], reviewer: str) -> dict[str, object]:
    return {
        "schemaVersion": 2,
        "reviewId": f"e14-review-{reviewer}-{dossier['dossierId']}",
        "dossierId": dossier["dossierId"],
        "dossierSha256": dossier["sha256"],
        "reviewerId": reviewer,
        "reviewerAffiliation": "synthetic-test-only",
        "independenceDeclaration": "I did not author the dossier or its evidence pack and reviewed the cited evidence independently.",
        "reviewedAt": "2026-07-16",
        "decision": "accept",
        "rationale": "Synthetic test receipt used only to prove that strict acceptance opens a separate gate while scope activation and data acquisition remain closed.",
        "checks": {
            "sourceLocatorsOpened": True,
            "mechanismClaimSupported": True,
            "boundariesSupported": True,
            "counterEvidenceConsidered": True,
            "noModelOutputUsed": True
        }
    }


def _write(root: Path, receipts: Path) -> tuple[Path, Path]:
    return write_e14_post2005_review_ingestion(
        Path("models/e14-post2005-review-ingestion-contract-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-taxonomy-proposal-v1.json"),
        _queue(),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-taxonomy-proposal-audit-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-post2005-review-handoff-audit-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        receipts,
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
