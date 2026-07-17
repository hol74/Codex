from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .dataset import DatasetValidationError


PINNED_TEST_RUNNER_PUBLIC_KEYS = {
    "e14-v5-synthetic-test-runner-v1": "e7f162a10bec559afea195e4dce84b69568d5d2cb0963eb446c0685e2b17f2f0"
}


def verify_pinned_test_receipt(receipt_raw: bytes, transcript_raw: bytes, expected_module: str, expected_file: str | Path) -> dict[str, Any]:
    try:
        receipt = json.loads(receipt_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError("E14 pinned test receipt is invalid JSON.") from error
    if not isinstance(receipt, dict):
        raise DatasetValidationError("E14 pinned test receipt must be an object.")
    signer_id = receipt.get("signerId")
    public_hex = PINNED_TEST_RUNNER_PUBLIC_KEYS.get(signer_id)
    if public_hex is None:
        raise DatasetValidationError("E14 test receipt signer is not deployment-pinned.")
    unsigned = dict(receipt); signature = unsigned.pop("signatureBase64", None)
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(base64.b64decode(signature, validate=True), _canonical(unsigned))
    except (InvalidSignature, ValueError, TypeError) as error:
        raise DatasetValidationError("E14 pinned test receipt signature is invalid.") from error
    expected_path = Path(expected_file).resolve()
    if receipt.get("executedModule") != expected_module or receipt.get("executedFile", {}).get("fileName") != expected_path.name:
        raise DatasetValidationError("E14 pinned test receipt module binding is invalid.")
    if receipt["executedFile"].get("sha256") != _sha(expected_path.read_bytes()):
        raise DatasetValidationError("E14 pinned test receipt file hash is invalid.")
    if receipt.get("transcript", {}).get("sha256") != _sha(transcript_raw) or receipt["transcript"].get("sizeBytes") != len(transcript_raw):
        raise DatasetValidationError("E14 pinned test receipt transcript binding is invalid.")
    return receipt


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
