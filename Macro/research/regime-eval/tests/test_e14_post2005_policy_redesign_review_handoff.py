from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_policy_redesign_review_handoff import (
    STATUS,
    write_e14_post2005_policy_redesign_review_handoff,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025/challengers"


class E14Post2005PolicyRedesignReviewHandoffTests(unittest.TestCase):
    def test_builds_deterministic_complete_bundle_without_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first")
            second = _write(root / "second")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(12, audit["inventory"]["bundleArtifactCount"])
            self.assertEqual(2, audit["inventory"]["worksheetCount"])
            self.assertEqual(2, audit["inventory"]["receiptTemplateCount"])
            self.assertEqual(0, audit["inventory"]["independentReviewReceiptCount"])
            self.assertTrue(audit["decision"]["handoffReady"])
            self.assertFalse(audit["decision"]["receiptIngestionAuthorized"])
            self.assertFalse(audit["decision"]["policyActivationAuthorized"])
            bundle = root / "first" / "bundle"
            self.assertEqual(12, len([path for path in bundle.rglob("*") if path.is_file()]))
            self.assertEqual(
                (DATA / "e14-post2005-policy-redesign-review-queue-v2.json").read_bytes(),
                next((bundle / "queue").glob("*.json")).read_bytes(),
            )
            for manifest in json.loads((DATA / "e14-post2005-policy-redesign-review-queue-v2.json").read_text())["dossiers"]:
                self.assertEqual((DATA / "e14-post2005-policy-redesign-dossiers-v1" / manifest["fileName"]).read_bytes(), (bundle / "dossiers" / manifest["fileName"]).read_bytes())
            template = json.loads(next((bundle / "receipt-templates").glob("*.json")).read_text())
            self.assertTrue(template["reviewId"].startswith("__REQUIRED"))
            self.assertIsNone(template["checks"]["providerPrimaryLocatorsOpened"])
            self.assertEqual([], list(bundle.rglob("*receipt.json")))
            for item in audit["bundleArtifacts"]:
                path = bundle / item["relativePath"]
                self.assertTrue(path.is_file())
                self.assertEqual(item["sizeBytes"], len(path.read_bytes()))
                self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "first")

    def test_rejects_traversal_filename_before_writing_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = json.loads((DATA / "e14-post2005-policy-redesign-review-queue-v2.json").read_text(encoding="utf-8"))
            queue["dossiers"][0]["fileName"] = "../escape.json"
            queue_path = _write_json(root / "queue.json", queue)
            with self.assertRaisesRegex(DatasetValidationError, "path is invalid"):
                _write(root / "out", queue=queue_path)
            self.assertFalse((root / "out" / "bundle").exists())

    def test_coordinated_plan_contract_rehash_cannot_open_ingestion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads((MODEL / "e14-post2005-policy-redesign-review-handoff-plan-v1.json").read_text(encoding="utf-8"))
            plan["authorizationPolicy"]["receiptIngestionAuthorized"] = True
            plan_path = _write_json(root / "plan.json", plan)
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-review-handoff-contract-v1.json").read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["receiptIngestionAuthorized"] = True
            contract["inputHashes"]["handoffPlanSha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract=contract_path, plan=plan_path)

    def test_rejects_audit_output_inside_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(DatasetValidationError, "topology overlaps"):
                _write(root, audit_inside_bundle=True)
            self.assertFalse((root / "bundle").exists())

    def test_contract_cannot_redirect_completed_receipts_into_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-review-handoff-contract-v1.json").read_text(encoding="utf-8"))
            contract["receiptOutputConvention"]["directory"] = "bundle/receipt-templates/"
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract=contract_path)


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write(
    root: Path,
    *,
    contract: Path | None = None,
    queue: Path | None = None,
    plan: Path | None = None,
    audit_inside_bundle: bool = False,
) -> Path:
    bundle = root / "bundle"
    audit = bundle / "audit.json" if audit_inside_bundle else root / "audit.json"
    return write_e14_post2005_policy_redesign_review_handoff(
        contract or MODEL / "e14-post2005-policy-redesign-review-handoff-contract-v1.json",
        DATA / "e14-post2005-policy-redesign-proposal-v1.json",
        queue or DATA / "e14-post2005-policy-redesign-review-queue-v2.json",
        DATA / "e14-post2005-policy-redesign-review-remediation-audit-v1.json",
        DATA / "e14-post2005-policy-redesign-dossiers-v1",
        MODEL / "e14-post2005-policy-redesign-review-remediation-evidence-v1.json",
        MODEL / "e14-policy-redesign-independent-review-schema-v1.json",
        MODEL / "e14-post2005-policy-redesign-review-remediation-plan-v1.json",
        plan or MODEL / "e14-post2005-policy-redesign-review-handoff-plan-v1.json",
        MODEL / "e14-post2005-policy-redesign-review-handoff-schema-v1.json",
        bundle,
        audit,
    )


if __name__ == "__main__":
    unittest.main()
