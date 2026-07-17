from __future__ import annotations
import hashlib, json
from typing import Any
from .dataset import DatasetValidationError

# Deliberately empty: provisioning is a separate externally authorized action.
PINNED_PRODUCTION_AUTHORITIES: dict[str, str] = {}

def verify_provisioned_authority(raw: bytes) -> dict[str, Any]:
    try: value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error: raise DatasetValidationError("E14.7aw invalid external authority contract.") from error
    authority_id = value.get("authorityId") if isinstance(value, dict) else None
    if PINNED_PRODUCTION_AUTHORITIES.get(authority_id) != hashlib.sha256(raw).hexdigest():
        raise DatasetValidationError("E14.7aw no deployment-pinned external monotonic authority is provisioned.")
    return value
