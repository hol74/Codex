from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_policy_redesign_activation import (
    STATUS,
    _validate_activation_audit,
    write_e14_post2005_policy_redesign_activation,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025/challengers"
SNAPSHOT = ROOT / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v1/snapshot-index.json"


class E14Post2005PolicyRedesignActivationTests(unittest.TestCase):
    def test_activates_separate_policy_overlay_and_only_opens_preregistration(self) -> None:
        old_manifest_hash = _hash(DATA / "e14-post2005-source-acquisition-manifest-v1.json")
        old_snapshot_hash = _hash(SNAPSHOT)
        with tempfile.TemporaryDirectory() as directory:
            policy_path, audit_path = _write(Path(directory))
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual("e14-post2005-active-source-vintage-policy-v2", policy["policyId"])
            self.assertEqual(STATUS, policy["status"])
            self.assertTrue(policy["authorization"]["active"])
            self.assertTrue(policy["authorization"]["requestCatalogGenerationAuthorized"])
            self.assertFalse(policy["authorization"]["requestCatalogGenerated"])
            self.assertFalse(policy["authorization"]["sourceAcquisitionAuthorized"])
            self.assertFalse(policy["authorization"]["featureTransformationAuthorized"])
            self.assertEqual(2, len(policy["activePolicyItems"]))
            cross = policy["activePolicyItems"][0]
            bank = policy["activePolicyItems"][1]
            self.assertEqual(["federal-reserve-h10-release-archive"], cross["retiredSourceIds"])
            self.assertIn("No cross-regime percentile history", cross["methodologyPolicy"])
            self.assertIn("actual publication date", bank["availabilityPolicy"]["fdic"])
            self.assertTrue(audit["decision"]["post2005PolicyRedesignActivated"])
            self.assertFalse(audit["decision"]["sourceAcquisitionAuthorized"])
            self.assertEqual(0, audit["protocol"]["observationsAcquired"])
        self.assertEqual(old_manifest_hash, _hash(DATA / "e14-post2005-source-acquisition-manifest-v1.json"))
        self.assertEqual(old_snapshot_hash, _hash(SNAPSHOT))

    def test_coordinated_proposal_contract_rehash_cannot_change_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = json.loads((DATA / "e14-post2005-policy-redesign-proposal-v1.json").read_text(encoding="utf-8"))
            proposal["proposalItems"][0]["methodologyPolicy"] = "Allow a silent cross-regime splice."
            proposal_path = _write_json(root / "proposal.json", proposal)
            contract = _contract()
            contract["inputHashes"]["policyRedesignProposalSha256"] = _hash(proposal_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", proposal=proposal_path, contract=contract_path)

    def test_queue_or_ingestion_escalation_fails_even_when_rehashed(self) -> None:
        mutations = ("queue", "ingestion")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                contract = _contract()
                queue_path = None
                ingestion_path = None
                if mutation == "queue":
                    queue = json.loads((DATA / "e14-post2005-policy-redesign-reviewed-queue-v3.json").read_text(encoding="utf-8"))
                    queue["receipts"][0]["decision"] = "reject"
                    queue_path = _write_json(root / "queue.json", queue)
                    contract["inputHashes"]["reviewedQueueV3Sha256"] = _hash(queue_path)
                else:
                    audit = json.loads((DATA / "e14-post2005-policy-redesign-review-ingestion-audit-v1.json").read_text(encoding="utf-8"))
                    audit["decision"]["sourceAcquisitionAuthorized"] = True
                    ingestion_path = _write_json(root / "ingestion.json", audit)
                    contract["inputHashes"]["reviewIngestionAuditSha256"] = _hash(ingestion_path)
                contract_path = _write_json(root / "contract.json", contract)
                with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                    _write(root / "out", contract=contract_path, queue=queue_path, ingestion=ingestion_path)

    def test_base_taxonomy_tamper_and_authorization_escalation_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            taxonomy = json.loads((DATA / "us-financial-stress-post2005-v1.json").read_text(encoding="utf-8"))
            taxonomy["activation"]["labelsAccepted"] = False
            taxonomy_path = _write_json(root / "taxonomy.json", taxonomy)
            contract = _contract()
            contract["inputHashes"]["baseActiveTaxonomySha256"] = _hash(taxonomy_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract=contract_path, taxonomy=taxonomy_path)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = json.loads((MODEL / "e14-post2005-policy-redesign-activation-plan-v1.json").read_text(encoding="utf-8"))
            plan["authorizationPolicy"]["sourceAcquisitionAuthorized"] = True
            plan_path = _write_json(root / "plan.json", plan)
            contract = _contract()
            contract["authorizationPolicy"]["sourceAcquisitionAuthorized"] = True
            contract["inputHashes"]["activationPlanSha256"] = _hash(plan_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract=contract_path, plan=plan_path)

    def test_outputs_are_write_once_and_cannot_overlap_protected_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root)
            with self.assertRaisesRegex(DatasetValidationError, "occupied"):
                _write(root)

        protected = DATA / "completed-policy-redesign-receipts-v1"
        with self.assertRaisesRegex(DatasetValidationError, "overlaps protected evidence"):
            _write(
                Path("unused"),
                outputs=(
                    protected / "e14-post2005-active-source-vintage-policy-v2.json",
                    protected / "e14-post2005-policy-redesign-activation-audit-v1.json",
                ),
            )

    def test_second_write_failure_rolls_back_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blocked = root / "blocked"
            blocked.write_text("not a directory", encoding="utf-8")
            policy = root / "e14-post2005-active-source-vintage-policy-v2.json"
            with self.assertRaisesRegex(DatasetValidationError, "could not be published atomically"):
                _write(
                    root,
                    outputs=(policy, blocked / "e14-post2005-policy-redesign-activation-audit-v1.json"),
                )
            self.assertFalse(policy.exists())

    def test_closed_audit_contract_rejects_authorization_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, audit_path = _write(Path(directory))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            audit["decision"]["sourceAcquisitionAuthorized"] = True
            with self.assertRaisesRegex(DatasetValidationError, "closed schema contract"):
                _validate_activation_audit(audit)


def _contract() -> dict:
    return json.loads((MODEL / "e14-post2005-policy-redesign-activation-contract-v1.json").read_text(encoding="utf-8"))


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write(
    root: Path,
    *,
    contract: Path | None = None,
    proposal: Path | None = None,
    queue: Path | None = None,
    ingestion: Path | None = None,
    taxonomy: Path | None = None,
    plan: Path | None = None,
    outputs: tuple[Path, Path] | None = None,
) -> tuple[Path, Path]:
    policy_output, audit_output = outputs or (
        root / "e14-post2005-active-source-vintage-policy-v2.json",
        root / "e14-post2005-policy-redesign-activation-audit-v1.json",
    )
    return write_e14_post2005_policy_redesign_activation(
        contract or MODEL / "e14-post2005-policy-redesign-activation-contract-v1.json",
        proposal or DATA / "e14-post2005-policy-redesign-proposal-v1.json",
        DATA / "e14-post2005-policy-redesign-proposal-audit-v1.json",
        queue or DATA / "e14-post2005-policy-redesign-reviewed-queue-v3.json",
        ingestion or DATA / "e14-post2005-policy-redesign-review-ingestion-audit-v1.json",
        taxonomy or DATA / "us-financial-stress-post2005-v1.json",
        DATA / "e14-post2005-scope-activation-audit-v1.json",
        MODEL / "e14-post2005-policy-redesign-plan-v1.json",
        plan or MODEL / "e14-post2005-policy-redesign-activation-plan-v1.json",
        MODEL / "e14-post2005-policy-redesign-activation-schema-v1.json",
        policy_output,
        audit_output,
    )


if __name__ == "__main__":
    unittest.main()
