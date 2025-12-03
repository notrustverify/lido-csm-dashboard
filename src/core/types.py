"""Data models for CSM Dashboard."""

from decimal import Decimal

from pydantic import BaseModel


class NodeOperator(BaseModel):
    """Node operator data from CSModule contract."""

    node_operator_id: int
    total_added_keys: int
    total_withdrawn_keys: int
    total_deposited_keys: int
    total_vetted_keys: int
    stuck_validators_count: int
    depositable_validators_count: int
    target_limit: int
    target_limit_mode: int
    total_exited_keys: int
    enqueued_count: int
    manager_address: str
    proposed_manager_address: str
    reward_address: str
    proposed_reward_address: str
    extended_manager_permissions: bool


class BondSummary(BaseModel):
    """Bond information for an operator."""

    current_bond_wei: int
    required_bond_wei: int
    current_bond_eth: Decimal
    required_bond_eth: Decimal
    excess_bond_eth: Decimal


class RewardsInfo(BaseModel):
    """Rewards data from merkle tree."""

    cumulative_fee_shares: int
    proof: list[str]


class OperatorRewards(BaseModel):
    """Complete rewards summary for display."""

    node_operator_id: int
    manager_address: str
    reward_address: str

    # Bond information
    current_bond_eth: Decimal
    required_bond_eth: Decimal
    excess_bond_eth: Decimal

    # Rewards information
    cumulative_rewards_shares: int
    distributed_shares: int
    unclaimed_shares: int
    unclaimed_eth: Decimal

    # Total claimable
    total_claimable_eth: Decimal

    # Validator counts
    total_validators: int
    active_validators: int
    exited_validators: int
