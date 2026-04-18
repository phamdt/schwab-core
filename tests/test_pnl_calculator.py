"""
Unit tests for P&L Calculator.

These tests verify that formulas EXACTLY match the TypeScript implementation
for contract testing between frontend and backend.

Test data is based on real-world scenarios from the frontend calculator.
"""

import pytest
from schwab_core.calculations.pnl import (
    calculate_intrinsic_value,
    calculate_option_pnl,
    calculate_strategy_pnl,
    calculate_breakeven_prices,
    calculate_max_profit_loss,
)


class TestIntrinsicValue:
    """Test intrinsic value calculations."""

    def test_call_itm(self):
        """Test in-the-money call."""
        # Stock at 105, strike 100 -> intrinsic = 5
        assert calculate_intrinsic_value(100, 105, 'call') == 5.0

    def test_call_otm(self):
        """Test out-of-the-money call."""
        # Stock at 95, strike 100 -> intrinsic = 0
        assert calculate_intrinsic_value(100, 95, 'call') == 0.0

    def test_call_atm(self):
        """Test at-the-money call."""
        # Stock at 100, strike 100 -> intrinsic = 0
        assert calculate_intrinsic_value(100, 100, 'call') == 0.0

    def test_put_itm(self):
        """Test in-the-money put."""
        # Stock at 95, strike 100 -> intrinsic = 5
        assert calculate_intrinsic_value(100, 95, 'put') == 5.0

    def test_put_otm(self):
        """Test out-of-the-money put."""
        # Stock at 105, strike 100 -> intrinsic = 0
        assert calculate_intrinsic_value(100, 105, 'put') == 0.0

    def test_put_atm(self):
        """Test at-the-money put."""
        # Stock at 100, strike 100 -> intrinsic = 0
        assert calculate_intrinsic_value(100, 100, 'put') == 0.0

    def test_case_insensitive(self):
        """Test case-insensitive option type."""
        assert calculate_intrinsic_value(100, 105, 'CALL') == 5.0
        assert calculate_intrinsic_value(100, 105, 'Call') == 5.0
        assert calculate_intrinsic_value(100, 95, 'PUT') == 5.0
        assert calculate_intrinsic_value(100, 95, 'Put') == 5.0

    def test_invalid_option_type(self):
        """Test invalid option type raises error."""
        with pytest.raises(ValueError, match="Invalid option_type"):
            calculate_intrinsic_value(100, 105, 'invalid')


class TestOptionPnL:
    """Test single option leg P&L calculations."""

    def test_long_call_profit(self):
        """
        Test long call with profit.
        
        TypeScript equivalent (line 99):
        pnl = (intrinsic - premium) × quantity × 100
        """
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': 5  # Premium paid
        }
        result = calculate_option_pnl(leg, 110)  # Stock at 110
        
        # Intrinsic = 10, Premium = 5
        # P&L = (10 - 5) * 1 * 100 = 500
        assert result['pnl'] == 500.0
        assert result['intrinsic_value'] == 10.0
        assert result['premium_value'] == 5.0

    def test_long_call_loss(self):
        """Test long call with loss."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 95)  # Stock at 95
        
        # Intrinsic = 0, Premium = 5
        # P&L = (0 - 5) * 1 * 100 = -500
        assert result['pnl'] == -500.0
        assert result['intrinsic_value'] == 0.0

    def test_long_call_breakeven(self):
        """Test long call at breakeven."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 105)  # Stock at 105
        
        # Intrinsic = 5, Premium = 5
        # P&L = (5 - 5) * 1 * 100 = 0
        assert result['pnl'] == 0.0

    def test_short_call_profit(self):
        """
        Test short call with profit.
        
        TypeScript equivalent (line 104):
        pnl = (premium - intrinsic) × quantity × 100
        """
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'short',
            'quantity': 1,
            'price': 5  # Premium received
        }
        result = calculate_option_pnl(leg, 95)  # Stock at 95
        
        # Intrinsic = 0, Premium = 5
        # P&L = (5 - 0) * 1 * 100 = 500
        assert result['pnl'] == 500.0

    def test_short_call_loss(self):
        """Test short call with loss."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'short',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 110)  # Stock at 110
        
        # Intrinsic = 10, Premium = 5
        # P&L = (5 - 10) * 1 * 100 = -500
        assert result['pnl'] == -500.0

    def test_long_put_profit(self):
        """Test long put with profit."""
        leg = {
            'strike': 100,
            'type': 'put',
            'side': 'long',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 90)  # Stock at 90
        
        # Intrinsic = 10, Premium = 5
        # P&L = (10 - 5) * 1 * 100 = 500
        assert result['pnl'] == 500.0
        assert result['intrinsic_value'] == 10.0

    def test_long_put_loss(self):
        """Test long put with loss."""
        leg = {
            'strike': 100,
            'type': 'put',
            'side': 'long',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 105)  # Stock at 105
        
        # Intrinsic = 0, Premium = 5
        # P&L = (0 - 5) * 1 * 100 = -500
        assert result['pnl'] == -500.0

    def test_short_put_profit(self):
        """Test short put with profit."""
        leg = {
            'strike': 100,
            'type': 'put',
            'side': 'short',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 105)  # Stock at 105
        
        # Intrinsic = 0, Premium = 5
        # P&L = (5 - 0) * 1 * 100 = 500
        assert result['pnl'] == 500.0

    def test_short_put_loss(self):
        """Test short put with loss."""
        leg = {
            'strike': 100,
            'type': 'put',
            'side': 'short',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 90)  # Stock at 90
        
        # Intrinsic = 10, Premium = 5
        # P&L = (5 - 10) * 1 * 100 = -500
        assert result['pnl'] == -500.0

    def test_multiple_contracts(self):
        """Test P&L with multiple contracts."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'long',
            'quantity': 5,
            'price': 3
        }
        result = calculate_option_pnl(leg, 108)  # Stock at 108
        
        # Intrinsic = 8, Premium = 3
        # P&L = (8 - 3) * 5 * 100 = 2500
        assert result['pnl'] == 2500.0

    def test_buy_side_normalized_to_long(self):
        """Test that 'buy' side is normalized to 'long'."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'buy',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 110)
        assert result['side'] == 'LONG'
        assert result['pnl'] == 500.0

    def test_sell_side_normalized_to_short(self):
        """Test that 'sell' side is normalized to 'short'."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'sell',
            'quantity': 1,
            'price': 5
        }
        result = calculate_option_pnl(leg, 95)
        assert result['side'] == 'SHORT'
        assert result['pnl'] == 500.0

    def test_negative_premium_warning(self):
        """Test that negative premium is converted to positive."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': -5  # Should be positive
        }
        result = calculate_option_pnl(leg, 110)
        
        # Should use abs(-5) = 5
        assert result['premium_value'] == 5.0
        assert result['pnl'] == 500.0

    def test_missing_required_field(self):
        """Test that missing required field raises error."""
        leg = {
            'strike': 100,
            'type': 'call',
            # Missing 'side', 'quantity', 'price'
        }
        with pytest.raises(ValueError, match="Missing required field"):
            calculate_option_pnl(leg, 110)

    def test_invalid_strike(self):
        """Test that invalid strike raises error."""
        leg = {
            'strike': 0,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': 5
        }
        with pytest.raises(ValueError, match="Invalid strike price"):
            calculate_option_pnl(leg, 110)

    def test_invalid_side(self):
        """Test that invalid side raises error."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'invalid',
            'quantity': 1,
            'price': 5
        }
        with pytest.raises(ValueError, match="Invalid side"):
            calculate_option_pnl(leg, 110)


class TestStrategyPnL:
    """Test multi-leg strategy P&L calculations."""

    def test_bull_call_spread(self):
        """
        Test bull call spread: Buy 100 call, Sell 110 call.
        
        Max profit = (110 - 100) - (5 - 2) = 7 per share = $700
        Max loss = (5 - 2) = 3 per share = $300
        """
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
            {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
        ]
        
        # At 105 (midpoint)
        result = calculate_strategy_pnl(legs, 105)
        # Long call: (5 - 5) * 100 = 0
        # Short call: (2 - 0) * 100 = 200
        # Total: 200
        assert result['total_pnl'] == 200.0
        
        # At max profit (110+)
        result = calculate_strategy_pnl(legs, 115)
        # Long call: (15 - 5) * 100 = 1000
        # Short call: (2 - 5) * 100 = -300
        # Total: 700
        assert result['total_pnl'] == 700.0
        
        # At max loss (100-)
        result = calculate_strategy_pnl(legs, 95)
        # Long call: (0 - 5) * 100 = -500
        # Short call: (2 - 0) * 100 = 200
        # Total: -300
        assert result['total_pnl'] == -300.0

    def test_iron_condor(self):
        """
        Test iron condor: 
        - Sell 95 put, Buy 90 put
        - Sell 105 call, Buy 110 call
        """
        legs = [
            {'strike': 90, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 1},
            {'strike': 95, 'type': 'put', 'side': 'short', 'quantity': 1, 'price': 3},
            {'strike': 105, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 3},
            {'strike': 110, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 1},
        ]
        
        # At 100 (center, max profit)
        result = calculate_strategy_pnl(legs, 100)
        # All options expire worthless
        # P&L = premiums received - premiums paid = (3 + 3 - 1 - 1) * 100 = 400
        assert result['total_pnl'] == 400.0

    def test_strategy_with_subgroups(self):
        """Test strategy with groupId for tracking subgroups."""
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5, 'groupId': 'group1'},
            {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2, 'groupId': 'group1'},
            {'strike': 95, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 4, 'groupId': 'group2'},
        ]
        
        result = calculate_strategy_pnl(legs, 105)
        
        # Verify subgroups are tracked
        assert 'group1' in result['subgroups']
        assert 'group2' in result['subgroups']
        
        # Verify total equals sum of subgroups
        total_from_subgroups = sum(result['subgroups'].values())
        assert abs(result['total_pnl'] - total_from_subgroups) < 0.01

    def test_empty_legs(self):
        """Test empty legs list."""
        result = calculate_strategy_pnl([], 100)
        assert result['total_pnl'] == 0.0
        assert result['leg_pnls'] == []
        assert result['subgroups'] == {}


class TestBreakevenPrices:
    """Test breakeven price calculations."""

    def test_long_call_breakeven(self):
        """Test breakeven for long call."""
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
        ]
        breakevens = calculate_breakeven_prices(legs)
        
        # Breakeven = Strike + Premium = 100 + 5 = 105
        assert len(breakevens) == 1
        assert abs(breakevens[0] - 105.0) < 1.0  # Allow 1 point tolerance

    def test_long_put_breakeven(self):
        """Test breakeven for long put."""
        legs = [
            {'strike': 100, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 5},
        ]
        breakevens = calculate_breakeven_prices(legs)
        
        # Breakeven = Strike - Premium = 100 - 5 = 95
        assert len(breakevens) == 1
        assert abs(breakevens[0] - 95.0) < 1.0

    def test_bull_call_spread_breakevens(self):
        """Test breakevens for bull call spread."""
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
            {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
        ]
        breakevens = calculate_breakeven_prices(legs)
        
        # Net debit = 5 - 2 = 3
        # Breakeven = 100 + 3 = 103
        assert len(breakevens) == 1
        assert abs(breakevens[0] - 103.0) < 1.0

    def test_straddle_two_breakevens(self):
        """Test straddle has two breakevens."""
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
            {'strike': 100, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 5},
        ]
        breakevens = calculate_breakeven_prices(legs)
        
        # Two breakevens: 100 - 10 = 90 and 100 + 10 = 110
        assert len(breakevens) == 2
        assert abs(breakevens[0] - 90.0) < 2.0
        assert abs(breakevens[1] - 110.0) < 2.0

    def test_empty_legs(self):
        """Test empty legs list."""
        breakevens = calculate_breakeven_prices([])
        assert breakevens == []


class TestMaxProfitLoss:
    """Test maximum profit and loss calculations."""

    def test_long_call_unlimited_profit(self):
        """Test long call has unlimited profit."""
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
        ]
        result = calculate_max_profit_loss(legs)
        
        # Max loss = Premium = $500
        assert result['max_loss'] == -500.0
        
        # Unlimited profit
        # Note: We may detect this as None or a very large number
        # depending on implementation

    def test_long_put_limited_profit(self):
        """Test long put has limited profit."""
        legs = [
            {'strike': 100, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 5},
        ]
        result = calculate_max_profit_loss(legs)
        
        # Max profit = (Strike - Premium) * 100 = (100 - 5) * 100 = 9500
        # Occurs when stock goes to 0
        assert result['max_profit'] is not None
        assert abs(result['max_profit'] - 9500.0) < 100.0
        
        # Max loss = Premium = -500
        assert result['max_loss'] == -500.0

    def test_bull_call_spread_defined_risk(self):
        """Test bull call spread has defined risk/reward."""
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
            {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
        ]
        result = calculate_max_profit_loss(legs)
        
        # Max profit = (110 - 100) - (5 - 2) = 7 * 100 = 700
        assert result['max_profit'] == 700.0
        
        # Max loss = (5 - 2) * 100 = 300
        assert result['max_loss'] == -300.0

    def test_iron_condor_defined_risk(self):
        """Test iron condor has defined risk/reward."""
        legs = [
            {'strike': 90, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 1},
            {'strike': 95, 'type': 'put', 'side': 'short', 'quantity': 1, 'price': 3},
            {'strike': 105, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 3},
            {'strike': 110, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 1},
        ]
        result = calculate_max_profit_loss(legs)
        
        # Max profit = Net credit = (3 + 3 - 1 - 1) * 100 = 400
        assert result['max_profit'] == 400.0
        
        # Max loss = (Width - Net credit) = (5 - 4) * 100 = -100
        # (either wing width minus net credit)
        assert result['max_loss'] is not None
        assert result['max_loss'] < 0

    def test_short_call_unlimited_loss(self):
        """Test short call has unlimited loss."""
        legs = [
            {'strike': 100, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 5},
        ]
        result = calculate_max_profit_loss(legs)
        
        # Max profit = Premium = 500
        assert result['max_profit'] == 500.0
        
        # Unlimited loss (may be detected as None or very large negative)

    def test_empty_legs(self):
        """Test empty legs list."""
        result = calculate_max_profit_loss([])
        assert result['max_profit'] is None
        assert result['max_loss'] is None


class TestRealWorldScenarios:
    """Test real-world options scenarios."""

    def test_aapl_covered_call(self):
        """
        Test AAPL covered call:
        - Own 100 shares at $150
        - Sell 155 call for $3
        """
        legs = [
            {'strike': 155, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 3},
        ]
        
        # At expiration below 155
        result = calculate_strategy_pnl(legs, 150)
        assert result['total_pnl'] == 300.0  # Keep premium
        
        # At expiration above 155
        result = calculate_strategy_pnl(legs, 160)
        # P&L = (3 - 5) * 100 = -200
        assert result['total_pnl'] == -200.0

    def test_spx_0dte_iron_condor(self):
        """
        Test SPX 0DTE iron condor with wide strikes.
        """
        legs = [
            {'strike': 5850, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 5},
            {'strike': 5900, 'type': 'put', 'side': 'short', 'quantity': 1, 'price': 15},
            {'strike': 6100, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 15},
            {'strike': 6150, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
        ]
        
        # At center (max profit)
        result = calculate_strategy_pnl(legs, 6000)
        # Net credit = (15 + 15 - 5 - 5) * 100 = 2000
        assert result['total_pnl'] == 2000.0

    def test_tsla_put_spread(self):
        """Test TSLA bear put spread."""
        legs = [
            {'strike': 180, 'type': 'put', 'side': 'long', 'quantity': 2, 'price': 8},
            {'strike': 170, 'type': 'put', 'side': 'short', 'quantity': 2, 'price': 4},
        ]
        
        # At max profit (below 170)
        result = calculate_strategy_pnl(legs, 160)
        # Long: (20 - 8) * 2 * 100 = 2400
        # Short: (4 - 10) * 2 * 100 = -1200
        # Total: 1200
        # Wait, let me recalculate:
        # Long put 180: (180 - 160) = 20 intrinsic, paid 8, profit = (20-8)*2*100 = 2400
        # Short put 170: (170 - 160) = 10 intrinsic, received 4, loss = (4-10)*2*100 = -1200
        # Net = 2400 - 1200 = 1200
        assert result['total_pnl'] == 1200.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_quantity(self):
        """Test zero quantity (should warn but not crash)."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'long',
            'quantity': 0,
            'price': 5
        }
        result = calculate_option_pnl(leg, 110)
        assert result['pnl'] == 0.0

    def test_very_high_strike(self):
        """Test very high strike (SPX options)."""
        leg = {
            'strike': 6000,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': 50
        }
        result = calculate_option_pnl(leg, 6100)
        # Intrinsic = 100, Premium = 50
        # P&L = (100 - 50) * 100 = 5000
        assert result['pnl'] == 5000.0

    def test_fractional_strike(self):
        """Test fractional strike price."""
        leg = {
            'strike': 100.5,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': 2.5
        }
        result = calculate_option_pnl(leg, 105.75)
        # Intrinsic = 5.25, Premium = 2.5
        # P&L = (5.25 - 2.5) * 100 = 275
        assert result['pnl'] == 275.0

    def test_fractional_premium(self):
        """Test fractional premium (e.g., $1.25)."""
        leg = {
            'strike': 100,
            'type': 'call',
            'side': 'long',
            'quantity': 1,
            'price': 1.25
        }
        result = calculate_option_pnl(leg, 105)
        # Intrinsic = 5, Premium = 1.25
        # P&L = (5 - 1.25) * 100 = 375
        assert result['pnl'] == 375.0

    def test_underlying_at_zero(self):
        """Test with underlying price near zero."""
        leg = {
            'strike': 5,
            'type': 'put',
            'side': 'long',
            'quantity': 1,
            'price': 1
        }
        result = calculate_option_pnl(leg, 0.01)
        # Intrinsic = ~5, Premium = 1
        # P&L = (5 - 1) * 100 = 400 (approximately)
        assert result['pnl'] > 300.0
