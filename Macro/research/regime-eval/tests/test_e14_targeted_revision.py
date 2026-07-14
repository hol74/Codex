from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_targeted_revision import REVISION_IDS, write_e14_targeted_revision


class E14TargetedRevisionTests(unittest.TestCase):
    def test_revises_only_four_hashes_and_preserves_eight_accepts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_a, audit_a = _write(root / "a")
            queue_b, audit_b = _write(root / "b")
            queue = json.loads(queue_a.read_text(encoding="utf-8"))
            audit = json.loads(audit_a.read_text(encoding="utf-8"))

            self.assertEqual(queue_a.read_bytes(), queue_b.read_bytes())
            self.assertEqual(audit_a.read_bytes(), audit_b.read_bytes())
            self.assertEqual("TARGETED_REREVIEW_REQUIRED", queue["status"])
            self.assertEqual(8, audit["inventory"]["preservedAcceptedDossierCount"])
            self.assertEqual(4, audit["inventory"]["revisedDossierCount"])
            self.assertFalse(audit["protocol"]["acceptedDossierBytesChanged"])
            self.assertFalse(audit["decision"]["labelFoundationGateAuthorized"])

            changed = {item["dossierId"] for item in queue["dossiers"]
                       if item["reviewStatus"] == "awaiting-targeted-independent-rereview"}
            self.assertEqual(REVISION_IDS, changed)
            self.assertEqual(4, len(list((root / "a" / "revised").glob("*.json"))))
            for folder in ("dossiers", "worksheets", "receipt-templates"):
                self.assertEqual(4, len(list((root / "a" / "bundle" / folder).iterdir())))

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_attempt_to_change_an_accepted_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-targeted-dossier-revision-contract-v1.json").read_text())
            contract["revisions"][0]["dossierId"] = "e14-dossier-stock-market-break-1987-broad-market-repricing"
            unsafe = root / "contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "scope are invalid"):
                _write(root / "unsafe", unsafe)

    def test_rejects_revision_not_bound_to_current_base_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-targeted-dossier-revision-contract-v1.json").read_text())
            contract["revisions"][0]["baseSha256"] = "0" * 64
            unsafe = root / "contract.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "scope are invalid"):
                _write(root / "unsafe", unsafe)


def _write(root: Path, contract: Path = Path("models/e14-targeted-dossier-revision-contract-v1.json")):
    return write_e14_targeted_revision(
        contract,
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v3.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-review-ingestion-audit-v1.json"),
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2"),
        root / "revised",
        root / "bundle",
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
