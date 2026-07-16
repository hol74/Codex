from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_policy_redesign_review_remediation import (
    DOSSIER_IDS,
    STATUS,
    _completed_accept_specimen,
    _validate_completed_receipt_contract,
    write_e14_post2005_policy_redesign_review_remediation,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025/challengers"


class E14Post2005PolicyRedesignReviewRemediationTests(unittest.TestCase):
    def test_versions_completable_review_contract_without_changing_dossiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path, audit_path = _write(root)
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            legacy_queue = json.loads((DATA / "e14-post2005-policy-redesign-review-queue-v1.json").read_text(encoding="utf-8"))
            self.assertEqual("e14-post2005-policy-redesign-review-queue-v2", queue["queueId"])
            self.assertEqual(legacy_queue["dossiers"], queue["dossiers"])
            self.assertEqual([], queue["receipts"])
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(0, audit["inventory"]["dossierBytesChanged"])
            self.assertEqual(7, audit["inventory"]["evidenceItemCount"])
            self.assertEqual(2, audit["inventory"]["counterEvidenceItemCount"])
            self.assertTrue(audit["checks"]["completedAcceptSpecimensPassDedicatedContract"])
            self.assertTrue(audit["checks"]["placeholderSpecimensFailDedicatedContract"])
            self.assertTrue(audit["decision"]["independentReviewHandoffAuthorized"])
            self.assertFalse(audit["decision"]["receiptIngestionAuthorized"])
            self.assertFalse(audit["decision"]["policyActivationAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse((root / "bundle").exists())
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root)

    def test_coordinated_plan_contract_rehash_cannot_open_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads((MODEL / "e14-post2005-policy-redesign-review-remediation-plan-v1.json").read_text(encoding="utf-8"))
            plan["authorizationPolicy"]["policyActivationAuthorized"] = True
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            contract = _contract_payload()
            contract["authorizationPolicy"]["policyActivationAuthorized"] = True
            contract["inputHashes"]["remediationPlanSha256"] = _sha(plan_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract_path, plan=plan_path)

    def test_rehashed_evidence_cannot_remove_required_locator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads((MODEL / "e14-post2005-policy-redesign-review-remediation-evidence-v1.json").read_text(encoding="utf-8"))
            evidence["reviewItems"][0]["evidenceItems"] = evidence["reviewItems"][0]["evidenceItems"][1:]
            evidence_path = _write_json(root / "evidence.json", evidence)
            contract = _contract_payload()
            contract["inputHashes"]["remediationEvidenceSha256"] = _sha(evidence_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract_path, evidence=evidence_path)

    def test_rehashed_schema_cannot_alias_dossier_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = json.loads((MODEL / "e14-policy-redesign-independent-review-schema-v1.json").read_text(encoding="utf-8"))
            schema["properties"]["dossierId"]["enum"][0] = "e14-dossier-alias"
            schema_path = _write_json(root / "schema.json", schema)
            contract = _contract_payload()
            contract["inputHashes"]["dedicatedReviewSchemaSha256"] = _sha(schema_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract_path, schema=schema_path)

    def test_rehashed_schema_cannot_remove_accept_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = json.loads((MODEL / "e14-policy-redesign-independent-review-schema-v1.json").read_text(encoding="utf-8"))
            schema["allOf"] = []
            schema_path = _write_json(root / "schema.json", schema)
            contract = _contract_payload()
            contract["inputHashes"]["dedicatedReviewSchemaSha256"] = _sha(schema_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract_path, schema=schema_path)

    def test_rehashed_evidence_cannot_remove_item_when_locator_remains_elsewhere(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = json.loads((MODEL / "e14-post2005-policy-redesign-review-remediation-evidence-v1.json").read_text(encoding="utf-8"))
            evidence["reviewItems"][0]["evidenceItems"] = [
                item for item in evidence["reviewItems"][0]["evidenceItems"]
                if item["role"] != "methodology-boundary"
            ]
            evidence_path = _write_json(root / "evidence.json", evidence)
            contract = _contract_payload()
            contract["inputHashes"]["remediationEvidenceSha256"] = _sha(evidence_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract_path, evidence=evidence_path)

    def test_completed_receipt_with_wrong_dossier_hash_is_not_completable(self) -> None:
        hashes = _contract_payload()["inputHashes"]
        specimen = _completed_accept_specimen(
            DOSSIER_IDS[0], "0" * 64, "1" * 64,
            hashes["remediationEvidenceSha256"], hashes["dedicatedReviewSchemaSha256"],
        )
        with self.assertRaisesRegex(DatasetValidationError, "not completable"):
            _validate_completed_receipt_contract(specimen, DOSSIER_IDS[0], "1" * 64, hashes)


def _contract_payload() -> dict:
    return json.loads((MODEL / "e14-post2005-policy-redesign-review-remediation-contract-v1.json").read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(
    root: Path,
    contract: Path | None = None,
    *,
    plan: Path | None = None,
    evidence: Path | None = None,
    schema: Path | None = None,
) -> tuple[Path, Path]:
    return write_e14_post2005_policy_redesign_review_remediation(
        contract or MODEL / "e14-post2005-policy-redesign-review-remediation-contract-v1.json",
        DATA / "e14-post2005-policy-redesign-proposal-v1.json",
        DATA / "e14-post2005-policy-redesign-review-queue-v1.json",
        DATA / "e14-post2005-policy-redesign-proposal-audit-v1.json",
        DATA / "e14-post2005-policy-redesign-handoff-audit-v1.json",
        MODEL / "e14-independent-review-schema-v2.json",
        schema or MODEL / "e14-policy-redesign-independent-review-schema-v1.json",
        DATA / "e14-post2005-policy-redesign-dossiers-v1",
        evidence or MODEL / "e14-post2005-policy-redesign-review-remediation-evidence-v1.json",
        plan or MODEL / "e14-post2005-policy-redesign-review-remediation-plan-v1.json",
        MODEL / "e14-post2005-policy-redesign-review-remediation-schema-v1.json",
        root / "queue.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
