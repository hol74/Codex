from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_dossier_curation import write_e14_positive_dossier_curation


class E14DossierCurationTests(unittest.TestCase):
    def test_curates_deterministic_reviewed_dossiers_without_accepting_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = _write(root / "dossiers-a", root / "audit-a.json")
            second = _write(root / "dossiers-b", root / "audit-b.json")
            report = json.loads(first.read_text(encoding="utf-8"))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            first_dossiers = sorted((root / "dossiers-a").glob("*.json"))
            second_dossiers = sorted((root / "dossiers-b").glob("*.json"))
            self.assertEqual(8, len(first_dossiers))
            self.assertEqual(
                [item.read_bytes() for item in first_dossiers],
                [item.read_bytes() for item in second_dossiers],
            )
            self.assertEqual("SECOND_REVIEW_AND_HARD_NEGATIVES_REQUIRED", report["status"])
            self.assertEqual(8, report["inventory"]["reviewedDossierCount"])
            self.assertEqual(0, report["inventory"]["acceptedDossierCount"])
            self.assertEqual(0, report["inventory"]["hardNegativeDossierCount"])
            self.assertEqual(0, report["protocol"]["outerFeatureRowCountUsed"])
            self.assertTrue(report["findings"]["vix1987CoverageMismatchDetected"])
            self.assertFalse(report["findings"]["frozenCatalogMutated"])
            self.assertFalse(report["decision"]["groundTruthMutationAuthorized"])

            with self.assertRaisesRegex(DatasetValidationError, "already exists"):
                _write(root / "dossiers-a", root / "audit-a.json")

    def test_rejects_dossier_without_two_independent_providers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = json.loads(Path("models/e14-positive-dossier-pack-v1.json").read_text(encoding="utf-8"))
            pack["dossierBlueprints"][0]["evidenceIds"] = [
                "continental-fed-quantitative", "continental-fed-counter"
            ]
            unsafe = root / "unsafe-pack.json"
            unsafe.write_text(json.dumps(pack, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "independent providers"):
                _write(root / "dossiers", root / "audit.json", unsafe)


def _write(dossier_dir: Path, output: Path, pack: Path = Path("models/e14-positive-dossier-pack-v1.json")) -> Path:
    return write_e14_positive_dossier_curation(
        pack,
        Path("models/e14-episode-dossier-schema-v1.json"),
        Path("models/e14-mechanism-detector-contract-v1.json"),
        Path("models/e14-historical-source-catalog-v1.json"),
        Path("../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-contract-audit-v1.json"),
        dossier_dir,
        output,
    )


if __name__ == "__main__":
    unittest.main()
