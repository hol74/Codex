from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_fdic_archive_atomic_producer_v5 import LEDGER_FILE_NAME
from regime_eval.e14_fdic_archive_atomic_producer_v6 import ANCHOR_ROOT, LOCK_PATH, STATE_ROOT, publish_bundle_v6, recover_publication_v6
import tests.test_e14_fdic_archive_atomic_producer_v5 as v5_tests


class E14FdicArchiveAtomicProducerV6Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._clean_state(); self.fixture = v5_tests.E14FdicArchiveAtomicProducerV5Tests(); self.fixture.setUp()

    def tearDown(self) -> None:
        self._clean_state()

    def test_cross_parent_replay_uses_one_deployment_pinned_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self.fixture._bundle(envelopes)
            publish_bundle_v6(self.fixture.contract_raw, mapping, manifest, envelopes, receipt, root / "a" / "bundle", inputs=self.fixture.inputs)
            with self.assertRaisesRegex(DatasetValidationError, "already consumed|trusted ledger head"):
                publish_bundle_v6(self.fixture.contract_raw, mapping, manifest, envelopes, receipt, root / "b" / "bundle", inputs=self.fixture.inputs)
            self.assertFalse((root / "b" / "bundle").exists()); self.assertTrue((STATE_ROOT / LEDGER_FILE_NAME).exists())

    def test_ledger_deletion_is_detected_by_separate_monotonic_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self.fixture._bundle(envelopes)
            publish_bundle_v6(self.fixture.contract_raw, mapping, manifest, envelopes, receipt, root / "first", inputs=self.fixture.inputs)
            (STATE_ROOT / LEDGER_FILE_NAME).unlink()
            with self.assertRaisesRegex(DatasetValidationError, "deletion or rollback"):
                publish_bundle_v6(self.fixture.contract_raw, mapping, manifest, envelopes, receipt, root / "second", inputs=self.fixture.inputs)

    def test_valid_prefix_rollback_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self.fixture._bundle(envelopes)
            publish_bundle_v6(self.fixture.contract_raw, mapping, manifest, envelopes, receipt, root / "first", inputs=self.fixture.inputs)
            empty = {"schemaVersion": 1, "artifactType": "E14FdicArchiveReceiptLedger", "headReceiptSha256": None, "entries": []}
            (STATE_ROOT / LEDGER_FILE_NAME).write_text(json.dumps(empty))
            with self.assertRaisesRegex(DatasetValidationError, "rollback or anchor mismatch"):
                recover_publication_v6()

    def test_pending_transaction_recovers_after_inner_publish_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); envelopes = root / "env"; envelopes.mkdir(); mapping, manifest, receipt = self.fixture._bundle(envelopes); target = root / "recovered"
            with self.assertRaisesRegex(DatasetValidationError, "injected crash"):
                publish_bundle_v6(self.fixture.contract_raw, mapping, manifest, envelopes, receipt, target, inputs=self.fixture.inputs, fail_after_inner_publish=True)
            self.assertFalse(target.exists()); self.assertTrue((ANCHOR_ROOT / "00000001.json").exists())
            self.assertEqual(target, recover_publication_v6()); self.assertTrue(target.exists())
            self.assertEqual("committed", json.loads((STATE_ROOT / "transaction.json").read_text())["status"])

    def test_dead_owner_lock_is_recovered(self) -> None:
        STATE_ROOT.mkdir(parents=True); LOCK_PATH.write_text(json.dumps({"schemaVersion": 1, "pid": 99999999, "createdAtUtc": "2026-07-17T00:00:00Z"}))
        self.assertIsNone(recover_publication_v6()); self.assertFalse(LOCK_PATH.exists())

    def _clean_state(self) -> None:
        workspace_tmp = (STATE_ROOT.parents[0]).resolve()
        for path in (STATE_ROOT, ANCHOR_ROOT):
            resolved = path.resolve()
            if resolved.parent != workspace_tmp:
                raise AssertionError("E14 v6 test cleanup escaped the pinned .tmp root")
            if resolved.exists(): shutil.rmtree(resolved)


if __name__ == "__main__": unittest.main()
