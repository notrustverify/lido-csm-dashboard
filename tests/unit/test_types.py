"""Tests for the core types module."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from src.core.types import (
    APYMetrics,
    BondSummary,
    DistributionFrame,
    HealthStatus,
    OperatorRewards,
    StrikeSummary,
    WithdrawalEvent,
)


class TestBondSummary:
    """Tests for the BondSummary model."""

    def test_bond_summary_creation(self, sample_bond_summary):
        """Test creating a BondSummary instance."""
        assert sample_bond_summary.current_bond_wei == 26269317414398397106
        assert sample_bond_summary.current_bond_eth == Decimal("26.269317414398397106")
        assert sample_bond_summary.excess_bond_eth == Decimal("0.069317414398397106")

    def test_bond_summary_decimal_precision(self):
        """Test that Decimal values maintain full precision."""
        bond = BondSummary(
            current_bond_wei=26269317414398397106,
            required_bond_wei=26200000000000000000,
            current_bond_eth=Decimal("26.269317414398397106"),
            required_bond_eth=Decimal("26.200000000000000000"),
            excess_bond_eth=Decimal("0.069317414398397106"),
        )

        # Verify full precision is maintained
        assert str(bond.current_bond_eth) == "26.269317414398397106"
        assert str(bond.excess_bond_eth) == "0.069317414398397106"


class TestStrikeSummary:
    """Tests for the StrikeSummary model."""

    def test_strike_summary_defaults(self):
        """Test that StrikeSummary has sensible defaults."""
        summary = StrikeSummary()

        assert summary.total_validators_with_strikes == 0
        assert summary.validators_at_risk == 0
        assert summary.validators_near_ejection == 0
        assert summary.total_strikes == 0
        assert summary.max_strikes == 0
        assert summary.strike_threshold == 3  # Default threshold

    def test_strike_summary_with_ics_threshold(self):
        """Test StrikeSummary with ICS threshold (4 strikes)."""
        summary = StrikeSummary(
            total_validators_with_strikes=5,
            validators_at_risk=2,
            validators_near_ejection=2,
            total_strikes=15,
            max_strikes=4,
            strike_threshold=4,  # ICS threshold
        )

        assert summary.strike_threshold == 4
        assert summary.validators_at_risk == 2

    def test_strike_summary_with_permissionless_threshold(self):
        """Test StrikeSummary with Permissionless threshold (3 strikes)."""
        summary = StrikeSummary(
            total_validators_with_strikes=5,
            validators_at_risk=3,
            validators_near_ejection=1,
            total_strikes=12,
            max_strikes=3,
            strike_threshold=3,  # Permissionless threshold
        )

        assert summary.strike_threshold == 3
        assert summary.validators_at_risk == 3


class TestHealthStatus:
    """Tests for the HealthStatus model."""

    def test_health_status_defaults(self):
        """Test that HealthStatus has sensible defaults."""
        health = HealthStatus()

        assert health.bond_healthy is True
        assert health.bond_deficit_eth == Decimal(0)
        assert health.stuck_validators_count == 0
        assert health.slashed_validators_count == 0
        assert health.validators_at_risk_count == 0
        assert health.strikes.strike_threshold == 3

    def test_has_issues_property_no_issues(self):
        """Test has_issues returns False when no issues."""
        health = HealthStatus()
        assert health.has_issues is False

    def test_has_issues_property_with_bond_deficit(self):
        """Test has_issues returns True when bond is unhealthy."""
        health = HealthStatus(
            bond_healthy=False,
            bond_deficit_eth=Decimal("1.5"),
        )
        assert health.has_issues is True

    def test_has_issues_property_with_slashed(self):
        """Test has_issues returns True when validators are slashed."""
        health = HealthStatus(slashed_validators_count=1)
        assert health.has_issues is True

    def test_has_issues_property_with_strikes(self):
        """Test has_issues returns True when validators have strikes."""
        health = HealthStatus(
            strikes=StrikeSummary(total_validators_with_strikes=1, total_strikes=2)
        )
        assert health.has_issues is True


class TestAPYMetrics:
    """Tests for the APYMetrics model."""

    def test_apy_metrics_defaults(self):
        """Test that APYMetrics fields are optional with None defaults."""
        apy = APYMetrics()

        assert apy.current_distribution_eth is None
        assert apy.current_distribution_apy is None
        assert apy.lifetime_reward_apy is None
        assert apy.frames is None

    def test_apy_metrics_with_values(self, sample_apy_metrics):
        """Test APYMetrics with actual values."""
        assert sample_apy_metrics.current_distribution_apy == 2.77
        assert sample_apy_metrics.lifetime_net_apy == 5.40


class TestDistributionFrame:
    """Tests for the DistributionFrame model."""

    def test_distribution_frame_creation(self):
        """Test creating a DistributionFrame instance."""
        frame = DistributionFrame(
            frame_number=1,
            start_date="2025-03-14T00:00:00",
            end_date="2025-04-11T00:00:00",
            rewards_eth=1.2345,
            rewards_shares=1234500000000000000,
            duration_days=28.0,
            validator_count=500,
            apy=2.85,
        )

        assert frame.frame_number == 1
        assert frame.rewards_eth == 1.2345
        assert frame.validator_count == 500
        assert frame.apy == 2.85


class TestWithdrawalEvent:
    """Tests for the WithdrawalEvent model."""

    def test_withdrawal_event_creation(self, sample_withdrawal_event):
        """Test creating a WithdrawalEvent instance."""
        assert sample_withdrawal_event.block_number == 21278373
        assert sample_withdrawal_event.eth_value == 0.1261
        assert sample_withdrawal_event.tx_hash.startswith("0x")

    def test_withdrawal_event_required_fields(self):
        """Test that all fields are required for WithdrawalEvent."""
        with pytest.raises(ValidationError):
            WithdrawalEvent()  # Missing all required fields


class TestOperatorRewards:
    """Tests for the OperatorRewards model."""

    def test_operator_rewards_creation(self, sample_operator_rewards):
        """Test creating an OperatorRewards instance."""
        assert sample_operator_rewards.node_operator_id == 333
        assert sample_operator_rewards.operator_type == "Permissionless"
        assert sample_operator_rewards.curve_id == 2
        assert sample_operator_rewards.total_validators == 500

    def test_operator_rewards_decimal_precision(self, sample_operator_rewards):
        """Test that Decimal fields maintain full precision."""
        # Convert to string to verify full precision
        assert "269317414398397106" in str(sample_operator_rewards.current_bond_eth)
        assert str(sample_operator_rewards.unclaimed_eth) == "1.35"

    def test_operator_rewards_with_withdrawals(self, sample_operator_rewards, sample_withdrawal_event):
        """Test OperatorRewards with withdrawal history."""
        sample_operator_rewards.withdrawals = [sample_withdrawal_event]

        assert len(sample_operator_rewards.withdrawals) == 1
        assert sample_operator_rewards.withdrawals[0].eth_value == 0.1261

    def test_operator_rewards_health_status(self, sample_operator_rewards):
        """Test that health status is properly linked."""
        assert sample_operator_rewards.health is not None
        assert sample_operator_rewards.health.bond_healthy is True
        assert sample_operator_rewards.health.strikes.strike_threshold == 3
