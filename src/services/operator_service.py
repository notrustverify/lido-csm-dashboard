"""Main service for computing operator rewards."""

from ..core.types import OperatorRewards
from ..data.onchain import OnChainDataProvider
from ..data.rewards_tree import RewardsTreeProvider


class OperatorService:
    """Orchestrates data from multiple sources to compute final rewards."""

    def __init__(self, rpc_url: str | None = None):
        self.onchain = OnChainDataProvider(rpc_url)
        self.rewards_tree = RewardsTreeProvider()

    async def get_operator_by_address(self, address: str) -> OperatorRewards | None:
        """
        Main entry point: get complete rewards data for an address.
        Returns None if address is not a CSM operator.
        """
        # Step 1: Find operator ID by address
        operator_id = await self.onchain.find_operator_by_address(address)
        if operator_id is None:
            return None

        return await self.get_operator_by_id(operator_id)

    async def get_operator_by_id(self, operator_id: int) -> OperatorRewards | None:
        """Get complete rewards data for an operator ID."""

        # Step 1: Get operator info
        try:
            operator = await self.onchain.get_node_operator(operator_id)
        except Exception:
            return None

        # Step 2: Get bond summary
        bond = await self.onchain.get_bond_summary(operator_id)

        # Step 3: Get rewards from merkle tree
        rewards_info = await self.rewards_tree.get_operator_rewards(operator_id)

        # Step 4: Get already distributed (claimed) shares
        distributed = await self.onchain.get_distributed_shares(operator_id)

        # Step 5: Calculate unclaimed
        cumulative_shares = (
            rewards_info.cumulative_fee_shares if rewards_info else 0
        )
        unclaimed_shares = max(0, cumulative_shares - distributed)

        # Step 6: Convert shares to ETH
        unclaimed_eth = await self.onchain.shares_to_eth(unclaimed_shares)

        # Step 7: Calculate total claimable
        total_claimable = bond.excess_bond_eth + unclaimed_eth

        return OperatorRewards(
            node_operator_id=operator_id,
            manager_address=operator.manager_address,
            reward_address=operator.reward_address,
            current_bond_eth=bond.current_bond_eth,
            required_bond_eth=bond.required_bond_eth,
            excess_bond_eth=bond.excess_bond_eth,
            cumulative_rewards_shares=cumulative_shares,
            distributed_shares=distributed,
            unclaimed_shares=unclaimed_shares,
            unclaimed_eth=unclaimed_eth,
            total_claimable_eth=total_claimable,
            total_validators=operator.total_deposited_keys,
            active_validators=operator.total_deposited_keys - operator.total_exited_keys,
            exited_validators=operator.total_exited_keys,
        )

    async def get_all_operators_with_rewards(self) -> list[int]:
        """Get list of all operator IDs that have rewards in the tree."""
        return await self.rewards_tree.get_all_operators_with_rewards()
