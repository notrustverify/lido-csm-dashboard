"""Fetch and parse the rewards merkle tree from GitHub."""

import httpx

from ..core.config import get_settings
from ..core.types import RewardsInfo
from .cache import cached


class RewardsTreeProvider:
    """Fetches rewards data from the csm-rewards repository."""

    def __init__(self):
        self.settings = get_settings()

    @cached(ttl=3600)  # Cache for 1 hour since tree updates infrequently
    async def fetch_rewards_data(self) -> dict:
        """
        Fetch the proofs.json file which contains:
        {
            "CSM Operator 0": {
                "cumulativeFeeShares": 304687403773285400,
                "proof": ["0x...", "0x...", ...]
            },
            ...
        }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.settings.rewards_proofs_url)
            response.raise_for_status()
            return response.json()

    async def get_operator_rewards(self, operator_id: int) -> RewardsInfo | None:
        """Get rewards info for a specific operator."""
        data = await self.fetch_rewards_data()
        key = f"CSM Operator {operator_id}"

        if key not in data:
            return None

        entry = data[key]
        return RewardsInfo(
            cumulative_fee_shares=entry["cumulativeFeeShares"],
            proof=entry["proof"],
        )

    async def get_all_operators_with_rewards(self) -> list[int]:
        """Get list of all operator IDs that have rewards."""
        data = await self.fetch_rewards_data()
        operator_ids = []
        for key in data.keys():
            if key.startswith("CSM Operator "):
                try:
                    op_id = int(key.replace("CSM Operator ", ""))
                    operator_ids.append(op_id)
                except ValueError:
                    continue
        return sorted(operator_ids)
