from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_hard_negative_targeted_review_ingestion import (
    write_e14_hard_negative_targeted_review_ingestion,
)


BASE = Path("../../data/historical-real-v12-2008-2025/challengers")
BUNDLE = BASE / "e14-hard-negative-expansion-targeted-review-bundle-v1"


class E14HardNegativeTargetedReviewIngestionTests(unittest.TestCase):
    def test_missing_receipts_keeps_coverage_gate_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue, audit_path = _write(root, root / "missing")
            audit = json.loads(audit_path.read_text())
            self.assertIsNone(queue)
            self.assertEqual("TARGETED_EXPANSION_REVIEW_INCOMPLETE", audit["status"])
            self.assertFalse(audit["decision"]["hardNegativeCoverageGateAuthorized"])
            self.assertFalse((root / "queue.json").exists())

    def test_two_strict_accepts_open_only_coverage_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, audit_path = _write(root / "run", _receipts(root / "receipts"))
            assert queue_path is not None
            queue = json.loads(queue_path.read_text())
            audit = json.loads(audit_path.read_text())
            base = json.loads((BASE / "e14-independent-review-queue-v8.json").read_text())
            self.assertEqual("EXPANSION_REVIEW_COMPLETE_ALL_ACCEPTED", queue["status"])
            self.assertEqual(base["dossiers"][:12], queue["dossiers"][:12])
            self.assertEqual(base["dossiers"][14:], queue["dossiers"][14:])
            self.assertEqual("READY_FOR_HARD_NEGATIVE_COVERAGE_GATE", audit["status"])
            self.assertEqual(6, audit["potentialCoverage"]["independentHardNegativeEpisodeCount"])
            self.assertEqual(2, audit["potentialCoverage"]["hardNegativeEpisodesPerMechanism"])
            self.assertTrue(audit["decision"]["hardNegativeCoverageGateAuthorized"])
            self.assertFalse(audit["decision"]["taxonomyUpdateAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])

    def test_accept_requires_all_strict_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _receipts(root / "receipts")
            path = next(receipts.glob("*.json"))
            payload = json.loads(path.read_text())
            payload["checks"]["mechanismClaimSupported"] = False
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(DatasetValidationError, "invalid or not independent"):
                _write(root / "run", receipts)

    def test_second_retry_accept_preserves_fifteen_and_reaches_six_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _receipts_from_bundle(
                root / "receipts-v2",
                BASE / "e14-hard-negative-expansion-targeted-review-bundle-v2",
            )
            queue_path, audit_path = write_e14_hard_negative_targeted_review_ingestion(
                Path("models/e14-hard-negative-targeted-review-ingestion-contract-v2.json"),
                BASE / "e14-independent-review-queue-v10.json",
                BASE / "e14-hard-negative-targeted-revision-audit-v2.json",
                Path("models/e14-hard-negative-targeted-revision-pack-v2.json"),
                Path("models/e14-independent-review-schema-v2.json"),
                receipts, root / "queue.json", root / "audit.json",
            )
            assert queue_path is not None
            audit = json.loads(audit_path.read_text())
            self.assertEqual(15, audit["inventory"]["preservedAcceptedDossierCount"])
            self.assertEqual(6, audit["potentialCoverage"]["independentHardNegativeEpisodeCount"])
            self.assertTrue(audit["decision"]["hardNegativeCoverageGateAuthorized"])


def _receipts(destination: Path) -> Path:
    return _receipts_from_bundle(destination, BUNDLE)


def _receipts_from_bundle(destination: Path, bundle: Path) -> Path:
    destination.mkdir(parents=True)
    for template_path in sorted((bundle / "receipt-templates").glob("*.json")):
        receipt = json.loads(template_path.read_text())
        receipt.update({
            "reviewerId": "independent-targeted-fixture",
            "reviewerAffiliation": "independent-test-fixture",
            "reviewedAt": "2026-07-15", "decision": "accept",
            "rationale": "Independent fixture opened every source and confirms the mechanism-specific hard negative, exact boundary, affirmative evidence and explicit counterevidence.",
        })
        receipt["checks"] = {key: True for key in receipt["checks"]}
        path = destination / template_path.name.replace("-reviewer.json", "-fixture.json")
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return destination


def _write(root: Path, receipts: Path):
    return write_e14_hard_negative_targeted_review_ingestion(
        Path("models/e14-hard-negative-targeted-review-ingestion-contract-v1.json"),
        BASE / "e14-independent-review-queue-v8.json",
        BASE / "e14-hard-negative-targeted-revision-audit-v1.json",
        Path("models/e14-hard-negative-targeted-revision-pack-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        receipts, root / "queue.json", root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
