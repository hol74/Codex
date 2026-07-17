from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .dataset import DatasetValidationError


def run_test_receipt(test_module: str, test_files: list[str | Path], output_path: str | Path) -> Path:
    output = Path(output_path).resolve()
    if output.exists(): raise DatasetValidationError("Immutable hash-bound test receipt already exists.")
    command = [sys.executable, "-m", "unittest", test_module]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    transcript = (result.stdout + result.stderr).encode()
    match = re.search(r"Ran (\d+) tests?", transcript.decode(errors="replace"))
    payload = {
        "schemaVersion": 1, "artifactType": "E14HashBoundTestExecutionReceipt",
        "executedAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": command, "runner": {"executable": sys.executable, "pythonVersion": platform.python_version()},
        "testArtifacts": [{"fileName": Path(path).name, "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()} for path in test_files],
        "exitCode": result.returncode, "transcriptSha256": hashlib.sha256(transcript).hexdigest(),
        "transcriptSizeBytes": len(transcript), "testsRun": int(match.group(1)) if match else 0,
        "passed": result.returncode == 0,
    }
    if result.returncode != 0: raise DatasetValidationError("E14 hash-bound test execution failed.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())
    return output
