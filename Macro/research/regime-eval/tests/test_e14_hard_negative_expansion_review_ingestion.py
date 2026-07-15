from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_hard_negative_expansion_review_ingestion import (
    write_e14_hard_negative_expansion_review_ingestion,
)


BASE = Path("../../data/historical-real-v12-2008-2025/challengers")
BUNDLE = BASE / "e14-hard-negative-expansion-review-bundle-v1"


class E14HardNegativeExpansionReviewIngestionTests(unittest.TestCase):
    def test_missing_receipts_write_only_deterministic_readiness_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_a, audit_a = _write(root / "a", root / "missing")
            queue_b, audit_b = _write(root / "b", root / "missing")
            report = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertIsNone(queue_a)
            self.assertIsNone(queue_b)
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual("EXPANSION_REVIEW_INCOMPLETE", report["status"])
            self.assertEqual(0, report["inventory"]["receivedExpansionReceiptCount"])
            self.assertEqual(4, report["inventory"]["missingExpansionReceiptCount"])
            self.assertFalse(report["decision"]["independentReviewComplete"])
            self.assertFalse(report["decision"]["hardNegativeCoverageGateAuthorized"])
            self.assertFalse(report["decision"]["candidateGenerationAuthorized"])
            self.assertFalse((root / "a" / "queue.json").exists())

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a", root / "missing")

    def test_four_strict_accepts_preserve_prior_manifests_and_authorize_only_coverage_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _receipts(root / "receipts")
            queue_path, audit_path = _write(root / "run", receipts)
            self.assertIsNotNone(queue_path)
            assert queue_path is not None
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            base_queue = json.loads((BASE / "e14-independent-review-queue-v6.json").read_text())

            self.assertEqual("READY_FOR_HARD_NEGATIVE_COVERAGE_GATE", audit["status"])
            self.assertEqual(4, audit["inventory"]["receivedExpansionReceiptCount"])
            self.assertEqual(4, audit["inventory"]["acceptedExpansionCount"])
            self.assertTrue(audit["decision"]["independentReviewComplete"])
            self.assertTrue(audit["decision"]["allExpansionDossiersAccepted"])
            self.assertTrue(audit["decision"]["hardNegativeCoverageGateAuthorized"])
            self.assertFalse(audit["decision"]["taxonomyUpdateAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])
            self.assertEqual("EXPANSION_REVIEW_COMPLETE_ALL_ACCEPTED", queue["status"])
            self.assertEqual(base_queue["dossiers"][:12], queue["dossiers"][:12])
            self.assertTrue(
                all(
                    item["reviewStatus"] == "accept-by-expansion-independent-receipt"
                    for item in queue["dossiers"][12:]
                )
            )

    def test_rejects_accept_with_unopened_sources_before_writing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _receipts(root / "receipts")
            path = next(receipts.glob("*.json"))
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["checks"]["sourceLocatorsOpened"] = False
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "invalid or not independent"):
                _write(root / "invalid", receipts)
            self.assertFalse((root / "invalid" / "queue.json").exists())
            self.assertFalse((root / "invalid" / "audit.json").exists())


def _receipts(destination: Path) -> Path:
    destination.mkdir(parents=True)
    for template_path in sorted((BUNDLE / "receipt-templates").glob("*.json")):
        receipt = json.loads(template_path.read_text(encoding="utf-8"))
        receipt["reviewerId"] = "independent-fixture-reviewer"
        receipt["reviewerAffiliation"] = "independent-test-fixture"
        receipt["reviewedAt"] = "2026-07-15"
        receipt["decision"] = "accept"
        receipt["rationale"] = (
            "Independent test fixture confirms the cited mechanism claim and exact monthly "
            "boundary after opening every locator and considering the documented counterevidence."
        )
        receipt["checks"]["sourceLocatorsOpened"] = True
        receipt["checks"]["mechanismClaimSupported"] = True
        receipt["checks"]["boundariesSupported"] = True
        output = destination / template_path.name.replace("-reviewer.json", "-fixture.json")
        output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _write(root: Path, receipt_dir: Path) -> tuple[Path | None, Path]:
    return write_e14_hard_negative_expansion_review_ingestion(
        Path("models/e14-hard-negative-expansion-review-ingestion-contract-v1.json"),
        BASE / "e14-independent-review-queue-v6.json",
        BASE / "e14-hard-negative-expansion-curation-audit-v1.json",
        BASE / "e14-hard-negative-expansion-handoff-audit-v1.json",
        Path("models/e14-hard-negative-expansion-handoff-contract-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        receipt_dir,
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
