"""
Unit tests for iron butterfly detection
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategy.iron_butterfly import (
    detect_iron_butterfly,
    validate_iron_butterfly_quantities
)


class TestIronButterflyDetection:
    """Test iron butterfly detection"""
    
    def test_perfect_iron_butterfly(self):
        """Test detection of perfect iron butterfly with symmetric wings"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 20.0,
                'expiration': '240115'
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0,
                'expiration': '240115'
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0,
                'expiration': '240115'
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 20.0,
                'expiration': '240115'
            }
        ]
        
        result = detect_iron_butterfly(legs)
        
        assert result is not None
        assert result.strategy_type == 'Iron Butterfly'
        assert result.confidence >= 0.95
        assert result.center_strike == 4500
        assert result.wing_width == 50
        assert result.lower_wing == 4450
        assert result.upper_wing == 4550
        assert result.net_credit == 60.0  # (50+50) - (20+20)
        assert result.max_profit == 60.0
        assert result.max_loss == -10.0  # 50 - 60
    
    def test_asymmetric_wings(self):
        """Test detection with slightly asymmetric wings"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4440,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'CALL',
                'strike': 4570,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115'
            }
        ]
        
        result = detect_iron_butterfly(legs)
        
        assert result is not None
        assert result.strategy_type == 'Iron Butterfly'
        # Lower confidence due to asymmetry: 60 vs 70 (16% difference)
        assert 0.80 <= result.confidence < 0.95
        assert result.center_strike == 4500
        assert result.lower_wing == 4440
        assert result.upper_wing == 4570
    
    def test_without_entry_prices(self):
        """Test detection without entry prices"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115'
            }
        ]
        
        result = detect_iron_butterfly(legs)
        
        assert result is not None
        assert result.strategy_type == 'Iron Butterfly'
        assert result.confidence >= 0.95
        assert result.net_credit is None
        assert result.max_profit is None
        assert result.max_loss is None
    
    def test_wrong_leg_count(self):
        """Test rejection with wrong number of legs"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
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
        
        result = detect_iron_butterfly(legs)
        assert result is None
    
    def test_wrong_option_type_distribution(self):
        """Test rejection when not 2 puts and 2 calls"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1
            }
        ]
        
        result = detect_iron_butterfly(legs)
        assert result is None
    
    def test_wrong_side_distribution(self):
        """Test rejection when sides don't match butterfly pattern"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1
            }
        ]
        
        result = detect_iron_butterfly(legs)
        assert result is None
    
    def test_center_strikes_dont_match(self):
        """Test rejection when center strikes differ"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4490,
                'side': 'SELL',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4510,
                'side': 'SELL',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1
            }
        ]
        
        result = detect_iron_butterfly(legs)
        assert result is None
    
    def test_invalid_structure(self):
        """Test rejection when structure is invalid (long put not below center)"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1
            },
            {
                'option_type': 'CALL',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1
            }
        ]
        
        result = detect_iron_butterfly(legs)
        assert result is None
    
    def test_different_expirations(self):
        """Test rejection when expirations differ"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240115'
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'expiration': '240122'
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1,
                'expiration': '240122'
            }
        ]
        
        result = detect_iron_butterfly(legs)
        assert result is None
    
    def test_breakeven_calculation(self):
        """Test breakeven point calculation"""
        legs = [
            {
                'option_type': 'PUT',
                'strike': 4450,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 20.0
            },
            {
                'option_type': 'PUT',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0
            },
            {
                'option_type': 'CALL',
                'strike': 4500,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 50.0
            },
            {
                'option_type': 'CALL',
                'strike': 4550,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 20.0
            }
        ]
        
        result = detect_iron_butterfly(legs)
        
        assert result is not None
        assert result.net_credit == 60.0
        assert result.breakeven_low == 4440.0  # 4500 - 60
        assert result.breakeven_high == 4560.0  # 4500 + 60


class TestQuantityValidation:
    """Test quantity validation for iron butterfly"""
    
    def test_matching_quantities(self):
        """Test validation passes with matching quantities"""
        legs = [
            {'quantity': 1},
            {'quantity': 1},
            {'quantity': 1},
            {'quantity': 1}
        ]
        
        assert validate_iron_butterfly_quantities(legs) is True
    
    def test_mismatched_quantities(self):
        """Test validation fails with mismatched quantities"""
        legs = [
            {'quantity': 1},
            {'quantity': 1},
            {'quantity': 2},
            {'quantity': 1}
        ]
        
        assert validate_iron_butterfly_quantities(legs) is False
    
    def test_wrong_leg_count(self):
        """Test validation fails with wrong leg count"""
        legs = [
            {'quantity': 1},
            {'quantity': 1}
        ]
        
        assert validate_iron_butterfly_quantities(legs) is False
