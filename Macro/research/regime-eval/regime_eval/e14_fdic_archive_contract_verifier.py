from __future__ import annotations

import hashlib
import json
from typing import Any

from .dataset import DatasetValidationError


PINNED_CONTRACT_HASHES = {
    "e14-fdic-archive-producer-v4-runtime-test-contract-v1": "6ac6850f7009816161dc000182674b60fc5aba68dc2aec3b7712874c9bb3935c"
}


def verify_pinned_contract(contract_raw: bytes) -> tuple[dict[str, Any], str]:
    try: contract = json.loads(contract_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error: raise DatasetValidationError("E14.7aq contract is not valid JSON.") from error
    contract_id = contract.get("contractId") if isinstance(contract, dict) else None
    digest = hashlib.sha256(contract_raw).hexdigest()
    if PINNED_CONTRACT_HASHES.get(contract_id) != digest:
        raise DatasetValidationError("E14.7aq contract is not present in the deployment-pinned registry.")
    return contract, digest
