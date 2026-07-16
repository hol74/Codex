from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_policy_redesign_review_ingestion import (
    write_e14_post2005_policy_redesign_review_ingestion,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025/challengers"
SOURCE_RECEIPTS = DATA / "completed-policy-redesign-receipts-v1"


class E14Post2005PolicyRedesignReviewIngestionTests(unittest.TestCase):
    def test_two_strict_accepts_create_reviewed_queue_without_activating_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _copy_receipts(root)
            queue_path, audit_path = _write(root / "out", receipts)
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual("e14-post2005-policy-redesign-reviewed-queue-v3", queue["queueId"])
            self.assertEqual("REVIEW_COMPLETE_ALL_ACCEPTED_SEPARATE_POLICY_ACTIVATION_GATE_REQUIRED", queue["status"])
            self.assertEqual(2, len(queue["receipts"]))
            self.assertEqual(2, audit["inventory"]["acceptedCount"])
            self.assertTrue(audit["decision"]["allDossiersAccepted"])
            self.assertTrue(audit["decision"]["separatePolicyActivationGateAuthorized"])
            self.assertFalse(audit["decision"]["policyActivated"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["decision"]["evaluationAuthorized"])
            for artifact in audit["receiptArtifacts"]:
                receipt = receipts / artifact["fileName"]
                self.assertEqual(artifact["sha256"], hashlib.sha256(receipt.read_bytes()).hexdigest())

    def test_rejects_wrong_dossier_hash_before_any_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _copy_receipts(root)
            receipt = next(receipts.glob("*cross-g5*.json"))
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["dossierSha256"] = "0" * 64
            _write_json(receipt, payload)
            with self.assertRaisesRegex(DatasetValidationError, "receipt is invalid"):
                _write(root / "out", receipts)
            self.assertFalse((root / "out" / "queue.json").exists())
            self.assertFalse((root / "out" / "audit.json").exists())

    def test_rejects_self_review_and_false_finding_on_accept(self) -> None:
        for mutation in ("self-review", "unsupported-accept"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                receipts = _copy_receipts(root)
                receipt = next(receipts.glob("*cross-g5*.json"))
                payload = json.loads(receipt.read_text(encoding="utf-8"))
                if mutation == "self-review":
                    payload["reviewerId"] = "codex-post2005-policy-redesign-2026-07-16"
                    old = receipt
                    receipt = receipts / f"e14-policy-redesign-review-cross-g5-monthly-release-replacement-v1-{payload['reviewerId']}.json"
                    old.rename(receipt)
                else:
                    payload["findingAssessments"][0]["supported"] = False
                _write_json(receipt, payload)
                with self.assertRaisesRegex(DatasetValidationError, "receipt is invalid"):
                    _write(root / "out", receipts)

    def test_rejects_missing_or_unexpected_receipt_file(self) -> None:
        for mutation in ("missing", "extra", "subdirectory"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                receipts = _copy_receipts(root)
                if mutation == "missing":
                    next(receipts.glob("*cross-g5*.json")).unlink()
                else:
                    if mutation == "extra":
                        (receipts / "unexpected.txt").write_text("unexpected", encoding="utf-8")
                    else:
                        (receipts / "unexpected-directory").mkdir()
                with self.assertRaisesRegex(DatasetValidationError, "exactly two JSON"):
                    _write(root / "out", receipts)

    def test_coordinated_plan_and_contract_rehash_cannot_activate_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _copy_receipts(root)
            plan = json.loads((MODEL / "e14-post2005-policy-redesign-review-ingestion-plan-v1.json").read_text(encoding="utf-8"))
            plan["authorizationPolicy"]["policyActivationPerformedByIngestion"] = True
            plan_path = _write_json(root / "plan.json", plan)
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-review-ingestion-contract-v1.json").read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["policyActivationPerformedByIngestion"] = True
            contract["inputHashes"]["ingestionPlanSha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", receipts, contract=contract_path, plan=plan_path)

    def test_outputs_are_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _copy_receipts(root)
            _write(root / "out", receipts)
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "out", receipts)

    def test_rejects_outputs_inside_receipts_dossiers_or_immutable_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _copy_receipts(root)
            protected = (
                receipts,
                DATA / "e14-post2005-policy-redesign-dossiers-v1",
                DATA / "e14-post2005-policy-redesign-review-handoff-v1",
            )
            for destination in protected:
                with self.subTest(destination=destination):
                    with self.assertRaisesRegex(DatasetValidationError, "overlaps an input"):
                        _write(root / "unused", receipts, outputs=(destination / "queue.json", destination / "audit.json"))

    def test_rejects_receipt_directory_inside_canonical_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            handoff = root / "audit-parent" / "e14-post2005-policy-redesign-review-handoff-audit-v1.json"
            handoff.parent.mkdir()
            handoff.write_bytes((DATA / handoff.name).read_bytes())
            bundle = handoff.parent / "e14-post2005-policy-redesign-review-handoff-v1"
            receipts = _copy_receipts(bundle)
            with self.assertRaisesRegex(DatasetValidationError, "overlaps immutable dossiers"):
                _write(root / "out", receipts, handoff=handoff)

    def test_second_write_failure_rolls_back_first_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = _copy_receipts(root)
            blocked_parent = root / "blocked-parent"
            blocked_parent.write_text("not a directory", encoding="utf-8")
            queue_output = root / "queue.json"
            with self.assertRaisesRegex(DatasetValidationError, "could not be published atomically"):
                _write(root / "unused", receipts, outputs=(queue_output, blocked_parent / "audit.json"))
            self.assertFalse(queue_output.exists())


def _copy_receipts(root: Path) -> Path:
    destination = root / "completed-policy-redesign-receipts-v1"
    destination.mkdir(parents=True)
    for source in SOURCE_RECEIPTS.glob("*.json"):
        (destination / source.name).write_bytes(source.read_bytes())
    return destination


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write(
    root: Path,
    receipts: Path,
    *,
    contract: Path | None = None,
    plan: Path | None = None,
    handoff: Path | None = None,
    outputs: tuple[Path, Path] | None = None,
) -> tuple[Path, Path]:
    queue_output, audit_output = outputs or (root / "queue.json", root / "audit.json")
    return write_e14_post2005_policy_redesign_review_ingestion(
        contract or MODEL / "e14-post2005-policy-redesign-review-ingestion-contract-v1.json",
        DATA / "e14-post2005-policy-redesign-proposal-v1.json",
        DATA / "e14-post2005-policy-redesign-review-queue-v2.json",
        DATA / "e14-post2005-policy-redesign-review-remediation-audit-v1.json",
        handoff or DATA / "e14-post2005-policy-redesign-review-handoff-audit-v1.json",
        DATA / "e14-post2005-policy-redesign-dossiers-v1",
        MODEL / "e14-post2005-policy-redesign-review-remediation-evidence-v1.json",
        MODEL / "e14-policy-redesign-independent-review-schema-v1.json",
        MODEL / "e14-post2005-policy-redesign-review-remediation-plan-v1.json",
        plan or MODEL / "e14-post2005-policy-redesign-review-ingestion-plan-v1.json",
        MODEL / "e14-post2005-policy-redesign-review-ingestion-schema-v1.json",
        receipts,
        queue_output,
        audit_output,
    )


if __name__ == "__main__":
    unittest.main()
