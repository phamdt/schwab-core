"""
Unit tests for position transformers.
"""

import pytest
from schwab_core.transformers.positions import (
    normalize_quantity,
    extract_symbol,
    extract_entry_price,
    extract_current_price,
    calculate_profit,
    calculate_market_value,
    transform_position_to_trade,
)


class TestNormalizeQuantity:
    """Tests for normalize_quantity function."""
    
    def test_long_quantity(self):
        """Test extraction of long position quantity."""
        position = {'longQuantity': 100, 'shortQuantity': 0}
        assert normalize_quantity(position) == 100.0
    
    def test_short_quantity(self):
        """Test extraction of short position quantity (negative)."""
        position = {'longQuantity': 0, 'shortQuantity': 50}
        assert normalize_quantity(position) == -50.0
    
    def test_combined_quantity(self):
        """Test extraction of combined quantity field."""
        position = {'quantity': 75}
        assert normalize_quantity(position) == 75.0
    
    def test_nested_long_quantity(self):
        """Test extraction of nested long quantity in instrument."""
        position = {'instrument': {'longQuantity': 200, 'shortQuantity': 0}}
        assert normalize_quantity(position) == 200.0
    
    def test_nested_short_quantity(self):
        """Test extraction of nested short quantity in instrument."""
        position = {'instrument': {'longQuantity': 0, 'shortQuantity': 150}}
        assert normalize_quantity(position) == -150.0
    
    def test_nested_combined_quantity(self):
        """Test extraction of nested combined quantity."""
        position = {'instrument': {'quantity': 300}}
        assert normalize_quantity(position) == 300.0
    
    def test_missing_quantity(self):
        """Test handling of missing quantity."""
        position = {}
        assert normalize_quantity(position) == 0.0
    
    def test_priority_long_over_combined(self):
        """Test that longQuantity takes priority over quantity."""
        position = {'longQuantity': 100, 'quantity': 50}
        assert normalize_quantity(position) == 100.0


class TestExtractSymbol:
    """Tests for extract_symbol function."""
    
    def test_instrument_symbol(self):
        """Test extraction from instrument.symbol."""
        position = {'instrument': {'symbol': 'AAPL'}}
        assert extract_symbol(position) == 'AAPL'
    
    def test_position_symbol(self):
        """Test extraction from position.symbol."""
        position = {'symbol': 'MSFT'}
        assert extract_symbol(position) == 'MSFT'
    
    def test_priority_instrument_over_position(self):
        """Test that instrument.symbol takes priority."""
        position = {
            'instrument': {'symbol': 'AAPL'},
            'symbol': 'MSFT'
        }
        assert extract_symbol(position) == 'AAPL'
    
    def test_option_description_parsing(self):
        """Test parsing symbol from option description."""
        position = {
            'instrument': {
                'assetType': 'OPTION',
                'description': 'AAPL 01/17/25 $150 Call'
            }
        }
        assert extract_symbol(position) == 'AAPL'
    
    def test_missing_symbol(self):
        """Test handling of missing symbol."""
        position = {}
        assert extract_symbol(position) is None


class TestExtractEntryPrice:
    """Tests for extract_entry_price function."""
    
    def test_average_price(self):
        """Test extraction of averagePrice."""
        position = {'averagePrice': 150.50}
        assert extract_entry_price(position, 100) == 150.50
    
    def test_price_field(self):
        """Test extraction of price field."""
        position = {'price': 125.75}
        assert extract_entry_price(position, 100) == 125.75
    
    def test_cost_basis_calculation(self):
        """Test calculation from costBasis."""
        position = {'costBasis': 10000}
        assert extract_entry_price(position, 100) == 100.0
    
    def test_priority_average_over_price(self):
        """Test that averagePrice takes priority over price."""
        position = {'averagePrice': 150.0, 'price': 100.0}
        assert extract_entry_price(position, 100) == 150.0
    
    def test_missing_entry_price(self):
        """Test handling of missing entry price."""
        position = {}
        assert extract_entry_price(position, 100) == 0.0


class TestExtractCurrentPrice:
    """Tests for extract_current_price function."""
    
    def test_market_price(self):
        """Test extraction of marketPrice."""
        position = {'marketPrice': 155.25}
        assert extract_current_price(position, 100, 'EQUITY', 150.0) == 155.25
    
    def test_last_price(self):
        """Test extraction of lastPrice."""
        position = {'lastPrice': 160.00}
        assert extract_current_price(position, 100, 'EQUITY', 150.0) == 160.00
    
    def test_negative_price_absolute(self):
        """Test that negative prices are converted to absolute."""
        position = {'marketPrice': -155.25}
        assert extract_current_price(position, 100, 'EQUITY', 150.0) == 155.25
    
    def test_calculate_from_market_value_equity(self):
        """Test calculation from marketValue for equity."""
        position = {'marketValue': 15000}
        assert extract_current_price(position, 100, 'EQUITY', 150.0) == 150.0
    
    def test_calculate_from_market_value_option(self):
        """Test calculation from marketValue for option."""
        position = {'marketValue': 5000}
        # marketValue = 5000, quantity = 10 contracts
        # current_price = 5000 / (10 * 100) = 5.0
        assert extract_current_price(position, 10, 'OPTION', 3.0) == 5.0
    
    def test_fallback_to_entry_price(self):
        """Test fallback to entry price."""
        position = {}
        assert extract_current_price(position, 100, 'EQUITY', 150.0) == 150.0


class TestCalculateProfit:
    """Tests for calculate_profit function."""
    
    def test_positive_profit(self):
        """Test calculation of positive profit."""
        assert calculate_profit(155.0, 150.0, 100) == 500.0
    
    def test_negative_profit(self):
        """Test calculation of negative profit (loss)."""
        assert calculate_profit(145.0, 150.0, 100) == -500.0
    
    def test_zero_profit(self):
        """Test calculation with no profit."""
        assert calculate_profit(150.0, 150.0, 100) == 0.0
    
    def test_short_position_profit(self):
        """Test profit calculation for short position."""
        # Short 100 shares at $150, now at $145 = $500 profit
        assert calculate_profit(145.0, 150.0, -100) == 500.0


class TestCalculateMarketValue:
    """Tests for calculate_market_value function."""
    
    def test_equity_market_value(self):
        """Test market value calculation for equity."""
        assert calculate_market_value(150.0, 100, 'EQUITY') == 15000.0
    
    def test_option_market_value(self):
        """Test market value calculation for option."""
        # 10 contracts at $5.00 = $5000
        assert calculate_market_value(5.0, 10, 'OPTION') == 5000.0
    
    def test_negative_quantity_preserves_sign(self):
        """Test that negative quantity results in negative market value."""
        assert calculate_market_value(150.0, -100, 'EQUITY') == -15000.0


class TestTransformPositionToTrade:
    """Tests for transform_position_to_trade function."""
    
    def test_complete_equity_position(self):
        """Test transformation of complete equity position."""
        position = {
            'instrument': {
                'symbol': 'AAPL',
                'assetType': 'EQUITY',
                'description': 'Apple Inc.'
            },
            'longQuantity': 100,
            'shortQuantity': 0,
            'averagePrice': 150.0,
            'marketPrice': 155.0,
            'marketValue': 15500.0,
            'totalPnL': 500.0,
            'dayPnL': 100.0,
            'percentOfAccount': 25.5
        }
        
        trade = transform_position_to_trade(position)
        
        assert trade['symbol'] == 'AAPL'
        assert trade['quantity'] == 100.0
        assert trade['entry_price'] == 150.0
        assert trade['current_price'] == 155.0
        assert trade['profit'] == 500.0
        assert trade['market_value'] == 15500.0
        assert trade['asset_type'] == 'EQUITY'
        assert trade['description'] == 'Apple Inc.'
        assert trade['total_pnl'] == 500.0
        assert trade['day_pnl'] == 100.0
        assert trade['percent_of_account'] == 25.5
    
    def test_complete_option_position(self):
        """Test transformation of complete option position."""
        position = {
            'instrument': {
                'symbol': 'AAPL250117C00150000',
                'assetType': 'OPTION',
                'description': 'AAPL 01/17/25 $150 Call',
                'underlyingSymbol': 'AAPL'
            },
            'longQuantity': 10,
            'shortQuantity': 0,
            'averagePrice': 3.50,
            'marketPrice': 5.00,
            'marketValue': 5000.0
        }
        
        trade = transform_position_to_trade(position)
        
        assert trade['symbol'] == 'AAPL250117C00150000'
        assert trade['quantity'] == 10.0
        assert trade['entry_price'] == 3.50
        assert trade['current_price'] == 5.00
        assert trade['profit'] == 15.0  # (5.00 - 3.50) * 10
        assert trade['market_value'] == 5000.0
        assert trade['asset_type'] == 'OPTION'
        assert trade['underlying_symbol'] == 'AAPL'
    
    def test_short_position(self):
        """Test transformation of short position."""
        position = {
            'instrument': {
                'symbol': 'MSFT',
                'assetType': 'EQUITY'
            },
            'longQuantity': 0,
            'shortQuantity': 50,
            'averagePrice': 300.0,
            'marketPrice': 290.0,
            'marketValue': -14500.0
        }
        
        trade = transform_position_to_trade(position)
        
        assert trade['quantity'] == -50.0
        assert trade['profit'] == 500.0  # (290 - 300) * -50 = 500
    
    def test_minimal_position_data(self):
        """Test transformation with minimal data."""
        position = {
            'instrument': {'symbol': 'TSLA'},
            'quantity': 25
        }
        
        trade = transform_position_to_trade(position)
        
        assert trade['symbol'] == 'TSLA'
        assert trade['quantity'] == 25.0
        assert trade['entry_price'] == 0.0
        assert trade['current_price'] == 0.0
        assert trade['profit'] == 0.0
    
    def test_missing_symbol_raises_error(self):
        """Test that missing symbol raises ValueError."""
        position = {'quantity': 100}
        
        with pytest.raises(ValueError, match="Could not extract symbol"):
            transform_position_to_trade(position)
    
    def test_preserves_strategy_info(self):
        """Test that strategy info is preserved."""
        position = {
            'instrument': {'symbol': 'AAPL'},
            'quantity': 100,
            'strategy_group_id': 'STRAT-001',
            'strategy_type': 'IRON_CONDOR'
        }
        
        trade = transform_position_to_trade(position)
        
        assert trade['strategy_group_id'] == 'STRAT-001'
        assert trade['strategy_type'] == 'IRON_CONDOR'
    
    def test_market_value_calculation_when_missing(self):
        """Test that market value is calculated when not provided."""
        position = {
            'instrument': {'symbol': 'AAPL', 'assetType': 'EQUITY'},
            'quantity': 100,
            'marketPrice': 150.0
        }
        
        trade = transform_position_to_trade(position)
        
        # Should calculate: 150.0 * 100 = 15000.0
        assert trade['market_value'] == 15000.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
