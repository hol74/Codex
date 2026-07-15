from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_feature_foundation import write_e14_feature_foundation


class E14FeatureFoundationTests(unittest.TestCase):
    def test_materializes_hash_bound_series_without_splicing_or_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs_a = _write(root / "a")
            outputs_b = _write(root / "b")
            for left, right in zip(outputs_a, outputs_b):
                self.assertEqual(left.read_bytes(), right.read_bytes())

            foundation = json.loads(outputs_a[0].read_text(encoding="utf-8"))
            lock = json.loads(outputs_a[1].read_text(encoding="utf-8"))
            audit = json.loads(outputs_a[2].read_text(encoding="utf-8"))
            counts = {item["seriesId"]: item["observationCount"] for item in foundation["series"]}

            self.assertEqual(5, len(foundation["series"]))
            self.assertEqual(6, len(foundation["detectorBindings"]))
            self.assertEqual(1812, sum(counts.values()))
            self.assertEqual("2022-01-01", _series(foundation, "e14-tedrate-monthly-maximum")["coverageTo"])
            self.assertEqual("2019-12-01", _series(foundation, "e14-dtwexb-monthly-maximum-absolute-change")["coverageTo"])
            self.assertEqual("2025Q3", _series(foundation, "e14-fdic-noncurrent-loan-rate-quarterly")["coverageTo"])
            self.assertTrue(all(
                item["status"] == "populated-manifested"
                for item in foundation["detectorBindings"]
            ))
            self.assertFalse(lock["strictVintageReady"])
            self.assertFalse(lock["candidateGenerationAuthorized"])
            self.assertEqual("FEATURE_FOUNDATION_MATERIALIZED_WITH_VINTAGE_LIMITATIONS", audit["status"])
            self.assertTrue(audit["decision"]["taxonomyV5ProtocolDesignAuthorized"])
            self.assertFalse(audit["decision"]["candidateGenerationAuthorized"])
            self.assertEqual(0, audit["inventory"]["observationsAfterCutoff"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "a")

    def test_rejects_contract_that_opens_candidate_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = json.loads(Path("models/e14-mechanism-feature-foundation-contract-v1.json").read_text())
            contract["authorizationPolicy"]["candidateGenerationAuthorized"] = True
            unsafe = root / "unsafe.json"
            unsafe.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out", unsafe)

    def test_rejects_raw_snapshot_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            shutil.copytree(_raw_dir(), raw)
            with (raw / "fred-tedrate.csv").open("ab") as stream:
                stream.write(b"tampered")
            with self.assertRaisesRegex(DatasetValidationError, "inputs or contract are invalid"):
                _write(root / "out", raw_dir=raw)


def _series(foundation: dict, series_id: str) -> dict:
    return next(item for item in foundation["series"] if item["seriesId"] == series_id)


def _raw_dir() -> Path:
    return Path("../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/raw")


def _write(
    root: Path,
    contract: Path = Path("models/e14-mechanism-feature-foundation-contract-v1.json"),
    raw_dir: Path | None = None,
) -> tuple[Path, Path, Path]:
    return write_e14_feature_foundation(
        contract,
        Path("ground-truth/us-financial-stress-v5.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-candidate-readiness-gate-audit-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        Path("models/e14-historical-source-catalog-v1.json"),
        Path("models/e14-mechanism-feature-foundation-schema-v1.json"),
        raw_dir or _raw_dir(),
        root / "foundation.json",
        root / "lock.json",
        root / "audit.json",
    )


if __name__ == "__main__":
    unittest.main()
