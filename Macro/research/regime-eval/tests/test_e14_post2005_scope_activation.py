from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_scope_activation import write_e14_post2005_scope_activation


DATA = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14Post2005ScopeActivationTests(unittest.TestCase):
    def test_activates_only_separate_scope_and_keeps_downstream_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            taxonomy_path, audit_path = _write(root)
            taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual("us-financial-stress-post2005-v1", taxonomy["taxonomyId"])
            self.assertTrue(taxonomy["activation"]["active"])
            self.assertTrue(taxonomy["activation"]["labelsAccepted"])
            self.assertFalse(taxonomy["activation"]["sourceAcquisitionAuthorized"])
            self.assertFalse(taxonomy["activation"]["candidateGenerationAuthorized"])
            archegos = next(item for item in taxonomy["proposedBankingHardNegativeControls"] if "archegos" in item["independentEventId"])
            self.assertEqual("2021-06-01", archegos["lastMonth"])
            self.assertEqual("73953a3a52a08685d1b06c28f5f63f0bb1b6b962d9f1ebb2f5959d338e2d8230", archegos["dossier"]["sha256"])
            self.assertEqual(0, audit["protocol"]["observationsAcquired"])
            self.assertFalse(audit["protocol"]["outerOosAuthorized"])

    def test_fails_closed_if_review_is_not_all_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = json.loads((DATA / "e14-post2005-final-reviewed-queue-v1.json").read_text(encoding="utf-8"))
            queue["status"] = "TARGETED_REVIEW_COMPLETE_REVISIONS_REQUIRED"
            bad = root / "bad-queue.json"
            bad.write_text(json.dumps(queue), encoding="utf-8")
            contract = json.loads(Path("models/e14-post2005-scope-activation-contract-v1.json").read_text(encoding="utf-8"))
            import hashlib
            contract["inputHashes"]["finalReviewedQueueSha256"] = hashlib.sha256(bad.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "not fully accepted"):
                write_e14_post2005_scope_activation(
                    contract_path, DATA / "e14-post2005-taxonomy-proposal-v1.json", bad,
                    DATA / "e14-post2005-targeted-review-ingestion-audit-v1.json",
                    root / "taxonomy.json", root / "audit.json",
                )


def _write(root: Path) -> tuple[Path, Path]:
    return write_e14_post2005_scope_activation(
        Path("models/e14-post2005-scope-activation-contract-v1.json"),
        DATA / "e14-post2005-taxonomy-proposal-v1.json",
        DATA / "e14-post2005-final-reviewed-queue-v1.json",
        DATA / "e14-post2005-targeted-review-ingestion-audit-v1.json",
        root / "taxonomy.json", root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
