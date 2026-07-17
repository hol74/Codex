from __future__ import annotations

import hashlib
import json
from typing import Any

from .dataset import DatasetValidationError


PINNED_CONTRACT_HASHES = {
    "e14-fdic-archive-producer-v5-runtime-test-contract-v1": "1483ee68f3d9af0cc5a086897ec53eb3e89950ead7a77dac6abdbdf1207e67fe"
}


def verify_pinned_contract_v5(raw: bytes) -> tuple[dict[str, Any], str]:
    try:
        contract = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetValidationError("E14.7as contract is invalid JSON.") from error
    digest = hashlib.sha256(raw).hexdigest(); contract_id = contract.get("contractId") if isinstance(contract, dict) else None
    if PINNED_CONTRACT_HASHES.get(contract_id) != digest:
        raise DatasetValidationError("E14.7as contract is not deployment-pinned.")
    if contract.get("executionMode") != "synthetic-test" or contract.get("authorizationPolicy", {}).get("providerNetworkCaptureAuthorized") is not False:
        raise DatasetValidationError("E14.7as provider network capture is not supported or authorized.")
    return contract, digest
