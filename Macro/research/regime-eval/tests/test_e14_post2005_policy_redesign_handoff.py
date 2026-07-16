from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_policy_redesign_handoff import (
    STATUS,
    write_e14_post2005_policy_redesign_handoff_audit,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025/challengers"


class E14Post2005PolicyRedesignHandoffTests(unittest.TestCase):
    def test_blocks_non_completable_schema_v2_handoff_without_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "first.json")
            second = _write(root / "second.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            audit = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, audit["status"])
            self.assertEqual(2, audit["inventory"]["schemaIncompatibleDossierCount"])
            self.assertEqual(0, audit["inventory"]["bundleArtifactCount"])
            self.assertEqual(0, audit["inventory"]["receiptTemplateCount"])
            self.assertFalse(audit["decision"]["handoffReady"])
            self.assertFalse(audit["decision"]["bundlePublicationAuthorized"])
            self.assertFalse(audit["decision"]["policyActivationAuthorized"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertFalse(audit["decision"]["featureTransformationAuthorized"])
            self.assertTrue(all(not item["completedSchemaV2ReceiptPossible"] for item in audit["compatibilityAssessments"]))
            self.assertEqual([], list(root.glob("**/receipt-templates")))
            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(first)

    def test_updated_hash_cannot_hide_schema_pattern_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = json.loads((MODEL / "e14-independent-review-schema-v2.json").read_text(encoding="utf-8"))
            schema["properties"]["dossierId"]["pattern"] = "^e14-[a-z0-9-]+$"
            schema_path = root / "schema.json"
            schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-handoff-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["reviewSchemaV2Sha256"] = hashlib.sha256(schema_path.read_bytes()).hexdigest()
            contract["expectedReviewSchemaDossierIdPattern"] = "^e14-[a-z0-9-]+$"
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "audit.json", contract_path, schema_path)
            self.assertFalse((root / "audit.json").exists())

    def test_rejects_dossier_hash_tampering_even_with_rehashed_queue_and_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = json.loads((DATA / "e14-post2005-policy-redesign-review-queue-v1.json").read_text(encoding="utf-8"))
            queue["dossiers"][0]["sha256"] = "0" * 64
            queue_path = root / "queue.json"
            queue_path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-handoff-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["reviewQueueSha256"] = hashlib.sha256(queue_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "dossier hash or content"):
                _write(root / "audit.json", contract_path, None, queue_path)

    def test_coordinated_contract_plan_rehash_cannot_open_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads((MODEL / "e14-post2005-policy-redesign-handoff-plan-v1.json").read_text(encoding="utf-8"))
            plan["authorizationPolicy"]["bundlePublicationAuthorized"] = True
            plan["nextAllowedAction"] = "ACTIVATE POLICY"
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-handoff-contract-v1.json").read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["bundlePublicationAuthorized"] = True
            contract["nextAllowedAction"] = "ACTIVATE POLICY"
            contract["inputHashes"]["handoffPlanSha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "audit.json", contract_path, None, None, plan_path)

    def test_rehashed_proposal_audit_cannot_omit_dossier_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal_audit = json.loads((DATA / "e14-post2005-policy-redesign-proposal-audit-v1.json").read_text(encoding="utf-8"))
            proposal_audit["outputs"]["dossiers"] = []
            proposal_audit_path = root / "proposal-audit.json"
            proposal_audit_path.write_text(json.dumps(proposal_audit, indent=2) + "\n", encoding="utf-8")
            contract = json.loads((MODEL / "e14-post2005-policy-redesign-handoff-contract-v1.json").read_text(encoding="utf-8"))
            contract["inputHashes"]["proposalAuditSha256"] = hashlib.sha256(proposal_audit_path.read_bytes()).hexdigest()
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "audit.json", contract_path, None, None, None, proposal_audit_path)


def _write(
    output: Path,
    contract: Path | None = None,
    schema: Path | None = None,
    queue: Path | None = None,
    plan: Path | None = None,
    proposal_audit: Path | None = None,
) -> Path:
    return write_e14_post2005_policy_redesign_handoff_audit(
        contract or MODEL / "e14-post2005-policy-redesign-handoff-contract-v1.json",
        DATA / "e14-post2005-policy-redesign-proposal-v1.json",
        queue or DATA / "e14-post2005-policy-redesign-review-queue-v1.json",
        proposal_audit or DATA / "e14-post2005-policy-redesign-proposal-audit-v1.json",
        schema or MODEL / "e14-independent-review-schema-v2.json",
        DATA / "e14-post2005-policy-redesign-dossiers-v1",
        MODEL / "e14-post2005-policy-redesign-handoff-evidence-v1.json",
        plan or MODEL / "e14-post2005-policy-redesign-handoff-plan-v1.json",
        MODEL / "e14-post2005-policy-redesign-handoff-schema-v1.json",
        output,
    )


if __name__ == "__main__":
    unittest.main()
