from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e13_generator import write_e13_candidate_manifest


class E13CandidateGeneratorTests(unittest.TestCase):
    def test_generates_finite_deterministic_task_separated_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = Path("models/e13-candidate-generation-protocol-v1.json")
            first = write_e13_candidate_manifest(protocol, root / "first.json")
            second = write_e13_candidate_manifest(protocol, root / "second.json")
            payload = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(16, payload["candidateCount"])
            self.assertFalse(payload["outerOosOpened"])
            self.assertEqual(16, len({item["candidateId"] for item in payload["candidates"]}))
            self.assertEqual(
                {"financial-stress-signal", "recession-signal"},
                {item["task"] for item in payload["candidates"]},
            )
            self.assertTrue(all(item["lifecycleStatus"] == "research-generated" for item in payload["candidates"]))

            with self.assertRaisesRegex(DatasetValidationError, "Immutable E13"):
                write_e13_candidate_manifest(protocol, first)

    def test_rejects_outer_selection_or_cross_task_fusion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = json.loads(Path("models/e13-candidate-generation-protocol-v1.json").read_text(encoding="utf-8"))
            protocol["selectionPolicy"]["outerOos"] = "Allowed for ranking."
            protocol["constraints"]["crossTaskFusion"] = True
            changed = root / "unsafe.json"
            changed.write_text(json.dumps(protocol), encoding="utf-8")

            with self.assertRaisesRegex(DatasetValidationError, "controls are incomplete"):
                write_e13_candidate_manifest(changed, root / "manifest.json")


if __name__ == "__main__":
    unittest.main()
