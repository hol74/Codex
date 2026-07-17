from __future__ import annotations
from pathlib import Path
from typing import Any
from .dataset import DatasetValidationError
from .e14_external_monotonic_authority import verify_provisioned_authority

STATUS = "FDIC_ARCHIVE_PRODUCER_V7_EXTERNAL_AUTHORITY_REQUIRED"

def publish_bundle_v7(*, authority_contract_raw: bytes, target_dir: str | Path, payload: dict[str, Any] | None = None) -> Path:
    verify_provisioned_authority(authority_contract_raw)
    raise DatasetValidationError("E14.7aw production publication remains blocked pending an independently reviewed external authority adapter.")
