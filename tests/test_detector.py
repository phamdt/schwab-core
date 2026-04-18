"""
Unit tests for main strategy detector
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategy.detector import (
    detect_strategies,
    detect_strategy_from_legs
)


class TestStrategyDetection:
    """Test main strategy detection"""
    
    def test_detect_vertical_spread(self):
        """Test detection of vertical spread"""
        positions = [
            {
                'symbol': 'SPY_240115P450',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_price': 50.0,
                'entry_time': datetime(2024, 1, 15, 10, 0, 0)
            },
            {
                'symbol': 'SPY_240115P445',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 445,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_price': 30.0,
                'entry_time': datetime(2024, 1, 15, 10, 0, 0)
            }
        ]
        
        strategies = detect_strategies(positions)
        
        assert len(strategies) == 1
        assert strategies[0]['strategy_type'] == 'Bear Put Spread'
        assert strategies[0]['confidence'] >= 0.90
        assert strategies[0]['underlying'] == 'SPY'
        assert strategies[0]['expiration'] == '240115'
        assert len(strategies[0]['legs']) == 2
    
    def test_detect_iron_butterfly(self):
        """Test detection of iron butterfly"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        positions = [
            {
                'symbol': 'SPY_240115P450',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_price': 20.0,
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240115P500',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_price': 50.0,
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240115C500',
                'underlying_symbol': 'SPY',
                'option_type': 'CALL',
                'strike': 500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_price': 50.0,
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240115C550',
                'underlying_symbol': 'SPY',
                'option_type': 'CALL',
                'strike': 550,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_price': 20.0,
                'entry_time': base_time
            }
        ]
        
        strategies = detect_strategies(positions)
        
        assert len(strategies) == 1
        assert strategies[0]['strategy_type'] == 'Iron Butterfly'
        assert strategies[0]['confidence'] >= 0.75
        assert strategies[0]['center_strike'] == 500
        assert strategies[0]['wing_width'] == 50
        assert len(strategies[0]['legs']) == 4
    
    def test_detect_multiple_strategies(self):
        """Test detection of multiple strategies on same underlying"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        positions = [
            # First vertical spread
            {
                'symbol': 'SPY_240115P450',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240115P445',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 445,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            # Second vertical spread (different time)
            {
                'symbol': 'SPY_240115C460',
                'underlying_symbol': 'SPY',
                'option_type': 'CALL',
                'strike': 460,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time + timedelta(hours=2)
            },
            {
                'symbol': 'SPY_240115C465',
                'underlying_symbol': 'SPY',
                'option_type': 'CALL',
                'strike': 465,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time + timedelta(hours=2)
            }
        ]
        
        strategies = detect_strategies(positions, time_grouping=True)
        
        assert len(strategies) == 2
        assert all(s['strategy_type'] in ['Bear Put Spread', 'Bull Call Spread']
                  for s in strategies)
    
    def test_detect_single_legs(self):
        """Test single legs are identified"""
        positions = [
            {
                'symbol': 'SPY_240115C450',
                'underlying_symbol': 'SPY',
                'option_type': 'CALL',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': datetime(2024, 1, 15, 10, 0, 0)
            }
        ]
        
        strategies = detect_strategies(positions)
        
        assert len(strategies) == 1
        assert strategies[0]['strategy_type'] == 'Single Leg'
        assert strategies[0]['confidence'] == 1.0
    
    def test_different_underlyings(self):
        """Test positions on different underlyings are separate"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        positions = [
            {
                'symbol': 'SPY_240115P450',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240115P445',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 445,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            {
                'symbol': 'AAPL_240115C180',
                'underlying_symbol': 'AAPL',
                'option_type': 'CALL',
                'strike': 180,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            {
                'symbol': 'AAPL_240115C185',
                'underlying_symbol': 'AAPL',
                'option_type': 'CALL',
                'strike': 185,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            }
        ]
        
        strategies = detect_strategies(positions)
        
        assert len(strategies) == 2
        underlyings = {s['underlying'] for s in strategies}
        assert underlyings == {'SPY', 'AAPL'}
    
    def test_different_expirations(self):
        """Test positions with different expirations are separate"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        positions = [
            {
                'symbol': 'SPY_240115P450',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240115P445',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 445,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240122C450',
                'underlying_symbol': 'SPY',
                'option_type': 'CALL',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240122',
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240122C455',
                'underlying_symbol': 'SPY',
                'option_type': 'CALL',
                'strike': 455,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240122',
                'entry_time': base_time
            }
        ]
        
        strategies = detect_strategies(positions)
        
        assert len(strategies) == 2
        expirations = {s['expiration'] for s in strategies}
        assert expirations == {'240115', '240122'}
    
    def test_without_time_grouping(self):
        """Test detection without time grouping"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        positions = [
            {
                'symbol': 'SPY_240115P450',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time
            },
            {
                'symbol': 'SPY_240115P445',
                'underlying_symbol': 'SPY',
                'option_type': 'PUT',
                'strike': 445,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115',
                'entry_time': base_time + timedelta(hours=5)
            }
        ]
        
        # With time grouping, might be separate
        strategies_with = detect_strategies(positions, time_grouping=True, time_window_seconds=60)
        
        # Without time grouping, should be detected as one strategy
        strategies_without = detect_strategies(positions, time_grouping=False)
        
        assert len(strategies_without) == 1
        assert strategies_without[0]['strategy_type'] == 'Bear Put Spread'


class TestDetectFromLegs:
    """Test direct strategy detection from specific legs"""
    
    def test_detect_vertical_from_legs(self):
        """Test detecting vertical spread from specific legs"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 50.0
            },
            {
                'option_type': 'PUT',
                'strike': 445,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 30.0
            }
        ]
        
        strategy = detect_strategy_from_legs(legs)
        
        assert strategy is not None
        assert strategy['strategy_type'] == 'Bear Put Spread'
        assert strategy['confidence'] >= 0.90
    
    def test_detect_iron_butterfly_from_legs(self):
        """Test detecting iron butterfly from specific legs"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 20.0
            },
            {
                'option_type': 'PUT',
                'strike': 500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0
            },
            {
                'option_type': 'CALL',
                'strike': 500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0
            },
            {
                'option_type': 'CALL',
                'strike': 550,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 20.0
            }
        ]
        
        strategy = detect_strategy_from_legs(legs)
        
        assert strategy is not None
        assert strategy['strategy_type'] == 'Iron Butterfly'
        assert strategy['confidence'] >= 0.75
    
    def test_invalid_legs(self):
        """Test invalid legs return None"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 450,
                'side': 'BUY',
                'quantity': 1
            }
        ]
        
        strategy = detect_strategy_from_legs(legs)
        assert strategy is None
