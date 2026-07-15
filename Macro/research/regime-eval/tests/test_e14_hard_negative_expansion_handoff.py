from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_hard_negative_expansion_handoff import (
    write_e14_hard_negative_expansion_handoff,
)


BASE = Path("../../data/historical-real-v12-2008-2025/challengers")


class E14HardNegativeExpansionHandoffTests(unittest.TestCase):
    def test_builds_deterministic_bundle_for_only_four_expansion_dossiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "a")
            second = _write(root / "b")
            report = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("EXPANSION_AWAITING_EXTERNAL_REVIEW", report["status"])
            self.assertEqual(12, report["inventory"]["preservedAcceptedDossierCount"])
            self.assertEqual(0, report["inventory"]["reopenedAcceptedDossierCount"])
            self.assertEqual(4, report["inventory"]["expansionDossierCount"])
            self.assertEqual(4, report["inventory"]["worksheetCount"])
            self.assertEqual(4, report["inventory"]["receiptTemplateCount"])
            self.assertEqual(0, report["inventory"]["independentReviewReceiptCount"])
            self.assertFalse(report["protocol"]["reviewPerformedByBundleGenerator"])
            self.assertFalse(report["decision"]["coverageAccepted"])
            self.assertFalse(report["decision"]["candidateGenerationAuthorized"])

            bundle = root / "a" / "bundle"
            for folder in ("dossiers", "worksheets", "receipt-templates"):
                self.assertEqual(4, len(list((bundle / folder).iterdir())))
            dossier_ids = {
                json.loads(path.read_text(encoding="utf-8"))["dossierId"]
                for path in (bundle / "dossiers").glob("*.json")
            }
            self.assertEqual(set(report["expansionDossierHashes"]), dossier_ids)
            self.assertTrue(all("hard-negative" in item for item in dossier_ids))

            template = json.loads(
                next((bundle / "receipt-templates").glob("*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(2, template["schemaVersion"])
            self.assertTrue(template["reviewerId"].startswith("__REQUIRED"))
            self.assertIsNone(template["checks"]["sourceLocatorsOpened"])
            self.assertIn(
                "12 previously accepted dossiers are deliberately excluded",
                (bundle / "README.md").read_text(encoding="utf-8"),
            )

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_expansion_dossier_hash_tampering_before_bundle_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = json.loads((BASE / "e14-independent-review-queue-v6.json").read_text())
            queue["dossiers"][-1]["sha256"] = "0" * 64
            queue_path = root / "queue.json"
            queue_path.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            contract = json.loads(
                Path("models/e14-hard-negative-expansion-handoff-contract-v1.json").read_text()
            )
            contract["inputHashes"]["reviewQueueV6Sha256"] = hashlib.sha256(
                queue_path.read_bytes()
            ).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "hash or content"):
                _write(root / "invalid", contract_path, queue_path)
            self.assertFalse((root / "invalid" / "bundle").exists())

    def test_rejects_contract_that_authorizes_review_by_generator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(
                Path("models/e14-hard-negative-expansion-handoff-contract-v1.json").read_text()
            )
            contract["authorizationPolicy"]["reviewByGeneratorAuthorized"] = True
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract"):
                _write(root / "invalid", contract_path)
            self.assertFalse((root / "invalid" / "bundle").exists())


def _write(
    root: Path,
    contract: Path = Path("models/e14-hard-negative-expansion-handoff-contract-v1.json"),
    queue: Path = BASE / "e14-independent-review-queue-v6.json",
) -> Path:
    return write_e14_hard_negative_expansion_handoff(
        contract,
        queue,
        BASE / "e14-hard-negative-expansion-curation-audit-v1.json",
        Path("models/e14-hard-negative-expansion-contract-v1.json"),
        Path("models/e14-independent-review-schema-v2.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        BASE / "e14-hard-negative-expansion-dossiers-v1",
        root / "bundle",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
