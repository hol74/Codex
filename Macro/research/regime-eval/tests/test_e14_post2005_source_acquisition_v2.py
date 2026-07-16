from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_source_acquisition_v2 import (
    STATUS,
    _validate_outputs,
    write_e14_post2005_source_acquisition_v2,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025/challengers"
SNAPSHOT_V1 = ROOT / "data/historical-real-v12-2008-2025/post2005-source-snapshots-v1/snapshot-index.json"


class E14Post2005SourceAcquisitionV2Tests(unittest.TestCase):
    def test_freezes_seven_source_manifest_and_catalog_without_network(self) -> None:
        legacy_hash = _hash(DATA / "e14-post2005-source-acquisition-manifest-v1.json")
        snapshot_hash = _hash(SNAPSHOT_V1)
        with tempfile.TemporaryDirectory() as directory:
            manifest_path, catalog_path, audit_path = _write(Path(directory))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(STATUS, manifest["status"])
            self.assertEqual("e14-post2005-source-acquisition-manifest-v2", manifest["manifestId"])
            self.assertEqual(7, len(manifest["sources"]))
            self.assertNotIn("federal-reserve-h10-release-archive", json.dumps(manifest))
            self.assertIn("federal-reserve-g5-release-archive", [item["sourceId"] for item in manifest["sources"]])
            self.assertEqual(11, len(catalog["requests"]))
            self.assertNotIn("federal-reserve-h10-release-archive", json.dumps(catalog))
            g5 = next(item for item in catalog["requests"] if item["requestId"] == "g5-dated-release-expansion-v2")
            fdic = next(item for item in catalog["requests"] if item["requestId"] == "fdic-qbp-publication-expansion-v2")
            self.assertEqual(240, g5["expansionPolicy"]["expectedUniqueMonthCount"])
            self.assertTrue(g5["expansionPolicy"]["duplicateOrCorrectionReleaseRequiresAdjudication"])
            self.assertEqual(79, fdic["expansionPolicy"]["expectedEligibleQuarterCount"])
            self.assertEqual("2025Q3", fdic["expansionPolicy"]["lastEligibleQuarter"])
            self.assertEqual("2025Q4", fdic["expansionPolicy"]["excludedQuarter"])
            self.assertEqual(0, audit["protocol"]["networkRequestsMade"])
            self.assertFalse(audit["decision"]["sourceAcquisitionExecutionAuthorized"])
        self.assertEqual(legacy_hash, _hash(DATA / "e14-post2005-source-acquisition-manifest-v1.json"))
        self.assertEqual(snapshot_hash, _hash(SNAPSHOT_V1))

    def test_coordinated_plan_contract_rehash_cannot_reintroduce_h10(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _load(MODEL / "e14-post2005-source-acquisition-plan-v2.json")
            plan["sources"][4]["sourceId"] = "federal-reserve-h10-release-archive"
            plan["featureFamilies"][2]["sourceIds"] = ["federal-reserve-h10-release-archive"]
            plan["requests"][6]["sourceId"] = "federal-reserve-h10-release-archive"
            plan_path = _write_json(root / "plan.json", plan)
            contract = _contract()
            contract["inputHashes"]["sourceAcquisitionPlanV2Sha256"] = _hash(plan_path)
            contract["expectedSourceIds"][4] = "federal-reserve-h10-release-archive"
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract=contract_path, plan=plan_path)

    def test_rejects_fdic_quarter_end_or_g5_backcast_relaxation(self) -> None:
        for mutation in ("fdic", "g5"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                plan = _load(MODEL / "e14-post2005-source-acquisition-plan-v2.json")
                if mutation == "fdic":
                    plan["requests"][3]["expansionPolicy"]["quarterEndCannotSubstituteForPublicationDate"] = False
                else:
                    plan["sources"][4]["methodologyRegimes"][-1] = "allow-cross-regime-backcast-and-splice"
                plan_path = _write_json(root / "plan.json", plan)
                contract = _contract()
                contract["inputHashes"]["sourceAcquisitionPlanV2Sha256"] = _hash(plan_path)
                contract_path = _write_json(root / "contract.json", contract)
                with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                    _write(root / "out", contract=contract_path, plan=plan_path)

    def test_rejects_not_ready_evidence_and_activation_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = _load(MODEL / "e14-post2005-source-acquisition-evidence-v2.json")
            evidence["sources"][4]["vintageProofComplete"] = False
            evidence_path = _write_json(root / "evidence.json", evidence)
            contract = _contract()
            contract["inputHashes"]["sourceAcquisitionEvidenceV2Sha256"] = _hash(evidence_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract=contract_path, evidence=evidence_path)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit = _load(DATA / "e14-post2005-policy-redesign-activation-audit-v1.json")
            audit["decision"]["sourceAcquisitionAuthorized"] = True
            audit_path = _write_json(root / "activation.json", audit)
            contract = _contract()
            contract["inputHashes"]["policyActivationAuditSha256"] = _hash(audit_path)
            contract_path = _write_json(root / "contract.json", contract)
            with self.assertRaisesRegex(DatasetValidationError, "inputs are invalid"):
                _write(root / "out", contract=contract_path, activation=audit_path)

    def test_outputs_are_write_once_protected_and_rollback_as_a_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root)
            with self.assertRaisesRegex(DatasetValidationError, "occupied"):
                _write(root)

        protected = DATA / "completed-policy-redesign-receipts-v1"
        with self.assertRaisesRegex(DatasetValidationError, "overlaps protected"):
            _write(Path("unused"), outputs=(protected / "e14-post2005-source-acquisition-manifest-v2.json", protected / "e14-post2005-source-acquisition-requests-v2.json", protected / "e14-post2005-source-acquisition-preregistration-audit-v2.json"))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blocked = root / "blocked"
            blocked.write_text("not a directory", encoding="utf-8")
            first = root / "e14-post2005-source-acquisition-manifest-v2.json"
            second = root / "e14-post2005-source-acquisition-requests-v2.json"
            with self.assertRaisesRegex(DatasetValidationError, "could not be published atomically"):
                _write(root, outputs=(first, second, blocked / "e14-post2005-source-acquisition-preregistration-audit-v2.json"))
            self.assertFalse(first.exists())
            self.assertFalse(second.exists())

    def test_closed_output_contract_rejects_execution_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path, catalog_path, audit_path = _write(Path(directory))
            manifest = _load(manifest_path)
            catalog = _load(catalog_path)
            audit = _load(audit_path)
            audit["decision"]["sourceAcquisitionExecutionAuthorized"] = True
            with self.assertRaisesRegex(DatasetValidationError, "closed preregistration contract"):
                _validate_outputs(manifest, catalog, audit)

    def test_closed_nested_contract_rejects_extra_readiness_and_expansion_fields(self) -> None:
        for mutation in ("readiness", "expansion"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                manifest_path, catalog_path, audit_path = _write(Path(directory))
                manifest = _load(manifest_path)
                catalog = _load(catalog_path)
                audit = _load(audit_path)
                if mutation == "readiness":
                    manifest["sources"][0]["readinessEvidence"]["unexpected"] = True
                else:
                    catalog["requests"][7]["expansionPolicy"]["unexpected"] = True
                with self.assertRaisesRegex(DatasetValidationError, "closed preregistration contract"):
                    _validate_outputs(manifest, catalog, audit)

    def test_bound_schemas_close_critical_nested_objects(self) -> None:
        manifest_schema = _load(MODEL / "e14-post2005-source-acquisition-manifest-schema-v2.json")
        request_schema = _load(MODEL / "e14-post2005-source-acquisition-requests-schema-v2.json")
        audit_schema = _load(MODEL / "e14-post2005-source-acquisition-preregistration-schema-v2.json")
        self.assertFalse(manifest_schema["$defs"]["source"]["properties"]["readinessEvidence"]["additionalProperties"])
        self.assertFalse(manifest_schema["properties"]["integrityPolicy"]["additionalProperties"])
        self.assertFalse(request_schema["properties"]["atomicityPolicy"]["additionalProperties"])
        self.assertEqual(4, len(request_schema["$defs"]["request"]["properties"]["expansionPolicy"]["oneOf"]))
        self.assertFalse(audit_schema["properties"]["inputs"]["additionalProperties"])
        self.assertEqual(11, len(audit_schema["properties"]["inputs"]["required"]))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _contract() -> dict:
    return _load(MODEL / "e14-post2005-source-acquisition-contract-v2.json")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write(root: Path, *, contract: Path | None = None, plan: Path | None = None, evidence: Path | None = None, activation: Path | None = None, outputs: tuple[Path, Path, Path] | None = None) -> tuple[Path, Path, Path]:
    targets = outputs or (root / "e14-post2005-source-acquisition-manifest-v2.json", root / "e14-post2005-source-acquisition-requests-v2.json", root / "e14-post2005-source-acquisition-preregistration-audit-v2.json")
    return write_e14_post2005_source_acquisition_v2(
        contract or MODEL / "e14-post2005-source-acquisition-contract-v2.json",
        DATA / "e14-post2005-active-source-vintage-policy-v2.json",
        activation or DATA / "e14-post2005-policy-redesign-activation-audit-v1.json",
        DATA / "us-financial-stress-post2005-v1.json",
        DATA / "e14-post2005-scope-activation-audit-v1.json",
        DATA / "e14-post2005-source-acquisition-manifest-v1.json",
        evidence or MODEL / "e14-post2005-source-acquisition-evidence-v2.json",
        plan or MODEL / "e14-post2005-source-acquisition-plan-v2.json",
        MODEL / "e14-post2005-source-acquisition-manifest-schema-v2.json",
        MODEL / "e14-post2005-source-acquisition-requests-schema-v2.json",
        MODEL / "e14-post2005-source-acquisition-preregistration-schema-v2.json",
        *targets,
    )


if __name__ == "__main__":
    unittest.main()
