"""Contract ABIs and helpers."""

import json
from pathlib import Path
from typing import Any


def load_abi(name: str) -> list[dict[str, Any]]:
    """Load ABI from JSON file in abis directory."""
    abi_path = Path(__file__).parent.parent.parent / "abis" / f"{name}.json"
    with open(abi_path) as f:
        return json.load(f)


# Load ABIs at module level for easy import
CSMODULE_ABI = load_abi("CSModule")
CSACCOUNTING_ABI = load_abi("CSAccounting")
CSFEEDISTRIBUTOR_ABI = load_abi("CSFeeDistributor")
STETH_ABI = load_abi("stETH")
