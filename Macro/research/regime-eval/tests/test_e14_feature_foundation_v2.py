from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_feature_foundation_v2 import write_e14_feature_foundation_v2


class E14FeatureFoundationV2Tests(unittest.TestCase):
    def test_materializes_replacements_and_repairs_actual_structural_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_a = _write(root / "a")
            outputs_b = _write(root / "b")
            for left, right in zip(outputs_a, outputs_b):
                self.assertEqual(left.read_bytes(), right.read_bytes())

            foundation = json.loads(outputs_a[0].read_text(encoding="utf-8"))
            lock = json.loads(outputs_a[1].read_text(encoding="utf-8"))
            audit = json.loads(outputs_a[2].read_text(encoding="utf-8"))
            by_id = {item["seriesId"]: item for item in foundation["series"]}

            self.assertEqual(5, len(foundation["series"]))
            self.assertEqual(5, len(foundation["detectorBindings"]))
            self.assertEqual(4, len(foundation["retiredDetectorBindings"]))
            self.assertEqual(3437, sum(item["observationCount"] for item in foundation["series"]))
            self.assertEqual(69, by_id["e14-fdic-failed-assisted-assets-monthly"]["missingObservationCount"])
            self.assertEqual("2019-12-01", by_id["e14-twexbmth-monthly-absolute-change"]["coverageTo"])
            self.assertEqual("2025-12-01", by_id["e14-fedfunds-minus-tbill-monthly"]["coverageTo"])
            self.assertTrue(lock["structuralCoverageReady"])
            self.assertFalse(lock["strictVintageReady"])
            self.assertFalse(lock["candidateGenerationAuthorized"])
            self.assertTrue(audit["checks"]["fdicApiInventoryComplete"])
            self.assertTrue(audit["checks"]["actualStructuralCoverageReady"])
            self.assertFalse(audit["decision"]["revisionRiskClearedForStrictVintageUse"])
            self.assertFalse(audit["decision"]["candidateFittingAuthorized"])
            self.assertEqual(0, audit["protocol"]["outerFeatureRowCountUsed"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_contract_that_mutates_foundation_v1(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(_contract().read_text(encoding="utf-8"))
            contract["authorizationPolicy"]["foundationV1MutationAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out", contract=unsafe)

    def test_rejects_raw_snapshot_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            shutil.copytree(_raw_dir(), raw)
            with (raw / "fred-twexbmth.csv").open("ab") as stream:
                stream.write(b"tampered")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out", raw_dir=raw)


def _contract() -> Path:
    return Path("models/e14-mechanism-feature-foundation-contract-v2.json")


def _raw_dir() -> Path:
    return Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/raw")


def _write(
    root: Path,
    contract: Path | None = None,
    raw_dir: Path | None = None,
) -> tuple[Path, Path, Path]:
    return write_e14_feature_foundation_v2(
        contract or _contract(),
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json"),
        Path("models/e14-mechanism-feature-foundation-lock-v1.json"),
        Path("models/e14-structural-coverage-repair-plan-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-structural-coverage-repair-audit-v1.json"),
        Path("models/e14-mechanism-feature-foundation-schema-v2.json"),
        raw_dir or _raw_dir(),
        root / "foundation.json",
        root / "lock.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
