from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_post2005_vintage_fitness import (
    PARTIAL,
    _fred_assessment,
    _validate_schema_instance,
    write_e14_post2005_vintage_fitness_audit,
)


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "research/regime-eval/models"
DATA = ROOT / "data/historical-real-v12-2008-2025"
SNAPSHOT = DATA / "post2005-source-snapshots-v1"
CHALLENGERS = DATA / "challengers"


class E14Post2005VintageFitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls._temporary.name) / "fitness-audit.json"
        write_e14_post2005_vintage_fitness_audit(
            MODEL / "e14-post2005-vintage-fitness-audit-contract-v1.json",
            SNAPSHOT / "snapshot-index.json",
            SNAPSHOT / "acquisition-audit.json",
            MODEL / "e14-post2005-scope-feasibility-plan-v1.json",
            MODEL / "e14-post2005-vintage-fitness-audit-plan-v1.json",
            MODEL / "e14-post2005-vintage-fitness-audit-schema-v1.json",
            SNAPSHOT,
            cls.output,
        )
        cls.audit = json.loads(cls.output.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def test_real_snapshot_is_partial_and_keeps_transformation_closed(self) -> None:
        self.assertEqual(PARTIAL, self.audit["status"])
        self.assertEqual(
            ["broad-market-repricing", "funding-liquidity"],
            self.audit["decision"]["readyMechanisms"],
        )
        self.assertEqual(
            ["banking-credit", "cross-border-growth"],
            self.audit["decision"]["blockedMechanisms"],
        )
        self.assertFalse(self.audit["decision"]["featureTransformationAuthorized"])
        self.assertEqual(0, self.audit["protocol"]["featuresTransformed"])
        self.assertFalse(self.audit["protocol"]["outerOosRead"])

    def test_real_inventory_and_event_time_boundaries_are_exact(self) -> None:
        self.assertEqual(23, self.audit["inventory"]["artifactCount"])
        self.assertEqual(20810, self.audit["inventory"]["fredObservationCount"])
        self.assertEqual(2, self.audit["inventory"]["vintageFitFamilyCount"])
        sources = {item["sourceId"]: item for item in self.audit["sourceAssessments"]}
        self.assertTrue(sources["fred-dgs2"]["eventTimeFit"])
        self.assertTrue(sources["fred-dcpf3m"]["eventTimeFit"])
        self.assertFalse(sources["federal-reserve-h8-release-archive"]["eventTimeFit"])
        self.assertFalse(sources["federal-reserve-h10-release-archive"]["eventTimeFit"])
        self.assertEqual("2011-12-31", sources["fdic-qbp-archive"]["coverageEnd"])

    def test_raw_artifact_tamper_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "snapshot"
            shutil.copytree(SNAPSHOT, copied)
            target = copied / "federal-reserve/h8/releases/release-index.html"
            target.write_bytes(target.read_bytes() + b"tamper")
            with self.assertRaisesRegex(DatasetValidationError, "artifact hash mismatch"):
                write_e14_post2005_vintage_fitness_audit(
                    MODEL / "e14-post2005-vintage-fitness-audit-contract-v1.json",
                    copied / "snapshot-index.json",
                    copied / "acquisition-audit.json",
                    MODEL / "e14-post2005-scope-feasibility-plan-v1.json",
                    MODEL / "e14-post2005-vintage-fitness-audit-plan-v1.json",
                    MODEL / "e14-post2005-vintage-fitness-audit-schema-v1.json",
                    copied,
                    Path(directory) / "must-not-exist.json",
                )

    def test_output_schema_rejects_incomplete_payload(self) -> None:
        schema = json.loads((MODEL / "e14-post2005-vintage-fitness-audit-schema-v1.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(DatasetValidationError, "required-property"):
            _validate_schema_instance({"schemaVersion": 1}, schema)

    def test_fred_release_lag_violation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "fred/test/chunk.json"
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "realtime_start": "2006-01-01", "realtime_end": "2011-12-31",
                "observation_start": "2006-01-01", "observation_end": "2025-12-31",
                "output_type": 4, "offset": 0, "count": 1, "limit": 100000,
                "observations": [{"date": "2006-01-01", "realtime_start": "2006-02-20", "realtime_end": "2006-02-20", "value": "1"}],
            }), encoding="utf-8")
            item = {
                "relativePath": relative, "realtimeChunk": ["2006-01-01", "2011-12-31"],
                "observationCount": 1, "observationStart": "2006-01-01", "observationEnd": "2006-01-01",
                "usageBoundary": "event-time-initial-release",
            }
            with self.assertRaisesRegex(DatasetValidationError, "initial-release chronology"):
                _fred_assessment(root, "fred-test", [item], 10)


if __name__ == "__main__":
    unittest.main()
