"""Shared pytest fixtures for CSM Dashboard tests."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.core.types import (
    APYMetrics,
    BondSummary,
    DistributionFrame,
    HealthStatus,
    OperatorRewards,
    StrikeSummary,
    WithdrawalEvent,
)


@pytest.fixture
def sample_bond_summary():
    """Sample bond summary data."""
    return BondSummary(
        current_bond_wei=26269317414398397106,
        required_bond_wei=26200000000000000000,
        current_bond_eth=Decimal("26.269317414398397106"),
        required_bond_eth=Decimal("26.2"),
        excess_bond_eth=Decimal("0.069317414398397106"),
    )


@pytest.fixture
def sample_strike_summary():
    """Sample strike summary data."""
    return StrikeSummary(
        total_validators_with_strikes=2,
        validators_at_risk=1,
        validators_near_ejection=1,
        total_strikes=5,
        max_strikes=3,
        strike_threshold=3,
    )


@pytest.fixture
def sample_health_status(sample_strike_summary):
    """Sample health status data."""
    return HealthStatus(
        bond_healthy=True,
        bond_deficit_eth=Decimal("0"),
        stuck_validators_count=0,
        slashed_validators_count=0,
        validators_at_risk_count=0,
        strikes=sample_strike_summary,
    )


@pytest.fixture
def sample_apy_metrics():
    """Sample APY metrics data."""
    return APYMetrics(
        current_distribution_eth=0.5,
        current_distribution_apy=2.77,
        current_bond_eth=0.3,
        current_bond_apr=2.56,
        previous_distribution_eth=0.45,
        previous_distribution_apy=2.65,
        lifetime_reward_apy=2.80,
        lifetime_bond_apy=2.60,
        lifetime_net_apy=5.40,
    )


@pytest.fixture
def sample_operator_rewards(sample_bond_summary, sample_health_status, sample_apy_metrics):
    """Sample operator rewards data."""
    return OperatorRewards(
        node_operator_id=333,
        manager_address="0x6ac683C503CF210CCF88193ec7ebDe2c993f63a4",
        reward_address="0x55915Cf2115c4D6e9085e94c8dAD710cabefef31",
        curve_id=2,
        operator_type="Permissionless",
        current_bond_eth=sample_bond_summary.current_bond_eth,
        required_bond_eth=sample_bond_summary.required_bond_eth,
        excess_bond_eth=sample_bond_summary.excess_bond_eth,
        cumulative_rewards_shares=1234567890,
        cumulative_rewards_eth=Decimal("10.96"),
        distributed_shares=1000000000,
        distributed_eth=Decimal("9.61"),
        unclaimed_shares=234567890,
        unclaimed_eth=Decimal("1.35"),
        total_claimable_eth=Decimal("1.419317414398397106"),
        total_validators=500,
        active_validators=500,
        exited_validators=0,
        health=sample_health_status,
        apy=sample_apy_metrics,
    )


@pytest.fixture
def sample_withdrawal_event():
    """Sample withdrawal event data."""
    return WithdrawalEvent(
        block_number=21278373,
        timestamp="2024-12-15T10:30:00",
        shares=126100000000000000,
        eth_value=0.1261,
        tx_hash="0x59efb01ebbc20103d4a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3",
    )
