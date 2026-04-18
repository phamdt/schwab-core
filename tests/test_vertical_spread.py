"""
Unit tests for vertical spread detection
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategy.vertical_spread import (
    detect_vertical_spread,
    calculate_vertical_spread_metrics
)


class TestVerticalSpreadDetection:
    """Test vertical spread detection"""
    
    def test_long_put_spread(self):
        """Test detection of long put spread"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 50.0
            },
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 30.0
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None
        assert result.strategy_type == 'Bear Put Spread'
        assert result.confidence >= 0.90
        assert result.long_strike == 4500
        assert result.short_strike == 4450
        assert result.net_debit_credit == 20.0  # Paid 50, received 30
        assert result.option_type == 'PUT'
    
    def test_short_put_spread(self):
        """Test detection of short put spread"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 30.0
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None
        assert result.strategy_type == 'Bull Put Spread'
        assert result.confidence >= 0.90
        assert result.long_strike == 4450
        assert result.short_strike == 4500
        assert result.net_debit_credit == -20.0  # Received 50, paid 30
        assert result.option_type == 'PUT'
    
    def test_long_call_spread(self):
        """Test detection of long call spread"""
        legs = [
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 60.0
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 40.0
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None
        assert result.strategy_type == 'Bull Call Spread'
        assert result.confidence >= 0.90
        assert result.long_strike == 4500
        assert result.short_strike == 4550
        assert result.net_debit_credit == 20.0  # Paid 60, received 40
        assert result.option_type == 'CALL'
    
    def test_short_call_spread(self):
        """Test detection of short call spread"""
        legs = [
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 40.0
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 60.0
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None
        assert result.strategy_type == 'Bear Call Spread'
        assert result.confidence >= 0.90
        assert result.long_strike == 4550
        assert result.short_strike == 4500
        assert result.net_debit_credit == -20.0  # Received 60, paid 40
        assert result.option_type == 'CALL'
    
    def test_without_entry_prices(self):
        """Test detection without entry prices"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'SELL',
                'quantity': 1
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None
        assert result.strategy_type == 'Bear Put Spread'
        assert result.confidence == 0.90
        assert result.net_debit_credit is None
    
    def test_mismatched_quantities(self):
        """Test rejection when quantities don't match"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'SELL',
                'quantity': 2
            }
        ]
        
        result = detect_vertical_spread(legs)
        assert result is None
    
    def test_same_side(self):
        """Test rejection when both legs are same side"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1
            }
        ]
        
        result = detect_vertical_spread(legs)
        assert result is None
    
    def test_different_option_types(self):
        """Test rejection when option types differ"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4450,
                'side': 'SELL',
                'quantity': 1
            }
        ]
        
        result = detect_vertical_spread(legs)
        assert result is None
    
    def test_same_strikes(self):
        """Test rejection when strikes are the same"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1
            }
        ]
        
        result = detect_vertical_spread(legs)
        assert result is None
    
    def test_wrong_leg_count(self):
        """Test rejection with wrong number of legs"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1
            }
        ]
        
        result = detect_vertical_spread(legs)
        assert result is None


class TestVerticalSpreadMetrics:
    """Test vertical spread metrics calculation"""
    
    def test_long_spread_metrics(self):
        """Test metrics for long spread (debit)"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 50.0
            },
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 30.0
            }
        ]
        
        result = detect_vertical_spread(legs)
        metrics = calculate_vertical_spread_metrics(result)
        
        assert metrics['width'] == 50
        assert metrics['max_loss'] == 20.0  # Debit paid
        assert metrics['max_profit'] == 30.0  # Width - debit
        assert metrics['risk_reward_ratio'] == 1.5  # 30/20
    
    def test_short_spread_metrics(self):
        """Test metrics for short spread (credit)"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 30.0
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0
            }
        ]
        
        result = detect_vertical_spread(legs)
        metrics = calculate_vertical_spread_metrics(result)
        
        assert metrics['width'] == 50
        assert metrics['max_profit'] == 20.0  # Credit received
        assert metrics['max_loss'] == 30.0  # Width - credit
        assert metrics['risk_reward_ratio'] == pytest.approx(0.667, 0.01)  # 20/30
