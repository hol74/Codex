from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dataset import DatasetValidationError
from .e14_fdic_archive_atomic_producer import _json_bytes
from .e14_fdic_archive_atomic_producer_v5 import LEDGER_FILE_NAME, _validate_ledger_semantics, publish_bundle_v5


STATUS = "FDIC_ARCHIVE_ATOMIC_PRODUCER_V6_IMPLEMENTED_INDEPENDENT_REVIEW_REQUIRED"
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
STATE_ROOT = WORKSPACE_ROOT / ".tmp" / "e14-v6-deployment-state"
ANCHOR_ROOT = WORKSPACE_ROOT / ".tmp" / "e14-v6-monotonic-anchor"
LOCK_PATH = STATE_ROOT / "publisher.lock"
TRANSACTION_PATH = STATE_ROOT / "transaction.json"
INTERNAL_TARGET = STATE_ROOT / "bundle-pending"


def publish_bundle_v6(contract_raw: bytes, map_payload: dict[str, Any], evidence_manifest: dict[str, Any], envelope_root: str | Path, collector_receipt_raw: bytes, target_dir: str | Path, *, inputs: dict[str, bytes], fail_after_inner_publish: bool = False) -> Path:
    target = Path(target_dir).resolve()
    if target.exists():
        raise DatasetValidationError("E14.7au target already exists.")
    _acquire_lock()
    try:
        _recover_pending_locked(); _assert_anchor_consistency()
        if INTERNAL_TARGET.exists():
            raise DatasetValidationError("E14.7au internal transaction target already exists.")
        receipt_hash = _sha(collector_receipt_raw)
        transaction = {"schemaVersion": 1, "artifactType": "E14FdicArchivePublicationTransaction", "status": "pending", "targetPath": str(target), "receiptSha256": receipt_hash, "createdAtUtc": _utc_now(), "committedAtUtc": None}
        _write_atomic(TRANSACTION_PATH, transaction)
        publish_bundle_v5(contract_raw, map_payload, evidence_manifest, envelope_root, collector_receipt_raw, INTERNAL_TARGET, inputs=inputs)
        _seal_current_ledger_head(receipt_hash)
        if fail_after_inner_publish:
            raise DatasetValidationError("E14.7au injected crash after inner publication.")
        _commit_target(transaction, target)
        return target
    finally:
        if LOCK_PATH.exists():
            LOCK_PATH.unlink()


def recover_publication_v6() -> Path | None:
    _acquire_lock()
    try:
        return _recover_pending_locked()
    finally:
        if LOCK_PATH.exists():
            LOCK_PATH.unlink()


def _recover_pending_locked() -> Path | None:
    if not TRANSACTION_PATH.exists():
        _assert_anchor_consistency(); return None
    transaction = _read_json(TRANSACTION_PATH)
    if transaction.get("status") == "committed":
        _assert_anchor_consistency(); return Path(transaction["targetPath"])
    if transaction.get("status") != "pending":
        raise DatasetValidationError("E14.7au transaction status is invalid.")
    ledger_path = STATE_ROOT / LEDGER_FILE_NAME; target = Path(transaction["targetPath"])
    if not INTERNAL_TARGET.exists():
        if not ledger_path.exists():
            TRANSACTION_PATH.unlink(); _assert_anchor_consistency(); return None
        raise DatasetValidationError("E14.7au pending transaction lost its internal bundle after ledger consumption.")
    ledger = _read_json(ledger_path); _validate_ledger_semantics(ledger)
    if ledger["headReceiptSha256"] != transaction["receiptSha256"]:
        raise DatasetValidationError("E14.7au pending transaction and ledger head disagree.")
    _seal_current_ledger_head(transaction["receiptSha256"])
    if target.exists():
        raise DatasetValidationError("E14.7au recovery target already exists.")
    _commit_target(transaction, target); return target


def _commit_target(transaction: dict[str, Any], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True); os.replace(INTERNAL_TARGET, target)
    committed = dict(transaction); committed["status"] = "committed"; committed["committedAtUtc"] = _utc_now(); _write_atomic(TRANSACTION_PATH, committed)


def _seal_current_ledger_head(expected_receipt: str) -> None:
    ledger_path = STATE_ROOT / LEDGER_FILE_NAME
    if not ledger_path.exists():
        raise DatasetValidationError("E14.7au cannot anchor a missing ledger.")
    ledger = _read_json(ledger_path); _validate_ledger_semantics(ledger)
    if ledger["headReceiptSha256"] != expected_receipt:
        raise DatasetValidationError("E14.7au ledger head differs from the transaction receipt.")
    sequence, head = _anchor_head()
    if head == expected_receipt:
        return
    if sequence != len(ledger["entries"]) - 1:
        raise DatasetValidationError("E14.7au monotonic anchor sequence cannot advance from current state.")
    ANCHOR_ROOT.mkdir(parents=True, exist_ok=True); marker = ANCHOR_ROOT / f"{sequence + 1:08d}.json"
    payload = {"schemaVersion": 1, "sequence": sequence + 1, "receiptSha256": expected_receipt, "previousReceiptSha256": head}
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError as error:
        raise DatasetValidationError("E14.7au monotonic anchor append failed.") from error
    with os.fdopen(fd, "wb") as stream:
        stream.write(_json_bytes(payload)); stream.flush(); os.fsync(stream.fileno())


def _assert_anchor_consistency() -> None:
    ledger_path = STATE_ROOT / LEDGER_FILE_NAME; sequence, anchor_head = _anchor_head()
    if not ledger_path.exists():
        if sequence != 0:
            raise DatasetValidationError("E14.7au ledger deletion or rollback detected by monotonic anchor.")
        return
    ledger = _read_json(ledger_path); _validate_ledger_semantics(ledger)
    if sequence != len(ledger["entries"]) or anchor_head != ledger["headReceiptSha256"]:
        raise DatasetValidationError("E14.7au ledger rollback or anchor mismatch detected.")


def _anchor_head() -> tuple[int, str | None]:
    if not ANCHOR_ROOT.exists():
        return 0, None
    markers = sorted(ANCHOR_ROOT.glob("*.json")); previous = None
    for index, marker in enumerate(markers, start=1):
        if marker.name != f"{index:08d}.json":
            raise DatasetValidationError("E14.7au monotonic anchor sequence has a gap.")
        payload = _read_json(marker)
        if payload != {"schemaVersion": 1, "sequence": index, "receiptSha256": payload.get("receiptSha256"), "previousReceiptSha256": previous} or not _is_sha(payload.get("receiptSha256")):
            raise DatasetValidationError("E14.7au monotonic anchor marker is invalid.")
        previous = payload["receiptSha256"]
    return len(markers), previous


def _acquire_lock() -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    for attempt in range(2):
        try:
            fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "wb") as stream:
                stream.write(_json_bytes({"schemaVersion": 1, "pid": os.getpid(), "createdAtUtc": _utc_now()})); stream.flush(); os.fsync(stream.fileno())
            return
        except FileExistsError:
            lock = _read_json(LOCK_PATH); pid = lock.get("pid")
            if attempt == 0 and isinstance(pid, int) and not _pid_alive(pid):
                LOCK_PATH.unlink(); continue
            raise DatasetValidationError("E14.7au deployment-pinned publisher state is locked.")
    raise DatasetValidationError("E14.7au deployment-pinned publisher lock could not be acquired.")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0); return True
    except OSError:
        return False


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); temp = path.with_name(path.name + ".tmp")
    if temp.exists():
        temp.unlink()
    with temp.open("wb") as stream:
        stream.write(_json_bytes(payload)); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"E14.7au invalid state JSON: {path.name}.") from error
    if not isinstance(value, dict):
        raise DatasetValidationError("E14.7au state JSON must be an object.")
    return value


def _is_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _sha(raw: bytes) -> str:
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
