from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.preregistration import write_preregistration_manifest


class PreregistrationTests(unittest.TestCase):
    def test_writes_deterministic_write_once_manifest_for_exactly_three_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gate = _copy_json(Path("models/e11-shadow-candidate-gate-v1.json"), root / "gate.json")
            configs = [
                _copy_json(Path("models/baseline-v1-5-dimensional.json"), root / "baseline.json"),
                _copy_json(Path("models/changepoint-duration-v1.json"), root / "changepoint.json"),
                _copy_json(Path("models/rare-event-logit-v1.json"), root / "logit.json"),
            ]
            first = write_preregistration_manifest(gate, configs, root / "manifest.json")
            second = write_preregistration_manifest(gate, reversed(configs), root / "manifest-2.json")
            report = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual("preregistered", report["status"])
            self.assertEqual(3, report["candidateCount"])
            self.assertEqual("shadow-candidate", report["promotionBoundary"]["maximumBeforeFreshOutcomes"])
            with self.assertRaisesRegex(DatasetValidationError, "Immutable preregistration manifest exists"):
                write_preregistration_manifest(gate, configs, first)

    def test_rejects_outer_oos_selection_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gate = _copy_json(Path("models/e11-shadow-candidate-gate-v1.json"), root / "gate.json")
            configs = [
                _copy_json(Path("models/baseline-v1-5-dimensional.json"), root / "baseline.json"),
                _copy_json(Path("models/changepoint-duration-v1.json"), root / "changepoint.json"),
                _copy_json(Path("models/rare-event-logit-v1.json"), root / "logit.json"),
            ]
            changed = json.loads(configs[0].read_text(encoding="utf-8"))
            changed["outerOosPolicy"] = "Allowed for model selection."
            configs[0].write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "leakage/selection policy"):
                write_preregistration_manifest(gate, configs, root / "manifest.json")


def _copy_json(source: Path, destination: Path) -> Path:
    destination.write_bytes(source.read_bytes())
    return destination


if __name__ == "__main__":
    unittest.main()
