from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .dataset import DatasetValidationError


def run_signed_test_receipt(test_module: str, private_key_raw: bytes, run_nonce: str, receipt_output: str | Path, transcript_output: str | Path) -> Path:
    receipt_path, transcript_path = Path(receipt_output).resolve(), Path(transcript_output).resolve()
    if receipt_path.exists() or transcript_path.exists(): raise DatasetValidationError("Immutable E14 signed test receipt or transcript already exists.")
    spec = importlib.util.find_spec(test_module)
    if spec is None or spec.origin is None: raise DatasetValidationError("E14 test module cannot be resolved to one file.")
    test_path = Path(spec.origin).resolve(); command = [sys.executable, "-m", "unittest", test_module]
    result = subprocess.run(command, text=False, capture_output=True, check=False); transcript = result.stdout + result.stderr
    if result.returncode != 0: raise DatasetValidationError("E14 signed test execution failed.")
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_raw)
    public_raw = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    transcript_path.parent.mkdir(parents=True, exist_ok=True); transcript_path.write_bytes(transcript)
    payload = {"schemaVersion": 2, "artifactType": "E14SignedTestExecutionReceipt", "executedAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "runNonce": run_nonce, "command": command, "executedModule": test_module, "executedFile": {"fileName": test_path.name, "sha256": _sha(test_path.read_bytes())}, "runner": {"fileName": Path(__file__).name, "sourceSha256": _sha(Path(__file__).read_bytes()), "executable": sys.executable, "pythonVersion": platform.python_version(), "platform": platform.platform()}, "transcript": {"fileName": transcript_path.name, "sha256": _sha(transcript), "sizeBytes": len(transcript)}, "exitCode": result.returncode, "passed": True, "publicKeyHex": public_raw.hex()}
    payload["signatureBase64"] = base64.b64encode(private_key.sign(_canonical(payload))).decode()
    receipt_path.parent.mkdir(parents=True, exist_ok=True); receipt_path.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())
    return receipt_path


def _canonical(value: dict) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
def _sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
