"""
Contract Test: Position Classification Parity (Python vs TypeScript)

This test suite verifies that the Python position classifier produces IDENTICAL
results to the TypeScript frontend logic for position classification.

Reference:
- TypeScript: /finimal/frontend/src/utils/creditPositionAnalysis.ts
- Python: /schwab-core/position/classifier.py

Test Philosophy:
- Verify long vs short detection matches frontend logic
- Verify credit vs debit classification matches frontend
- Test quantity normalization edge cases
- Tests MUST fail if classification diverges between implementations

Author: Contract Testing Suite
Date: 2026-04-05
"""

import pytest
from schwab_core.position import (
    classify_position_direction,
    classify_credit_debit,
    normalize_quantity,
    is_credit_strategy,
    extract_position_effect,
)


class TestPositionDirectionParity:
    """
    Verify position direction classification (LONG vs SHORT) matches TypeScript.
    
    TypeScript reference: creditPositionAnalysis.ts line 34
    Python reference: classifier.py line 16
    """
    
    def test_long_position_positive_quantity(self):
        """
        Long position: longQuantity > 0
        TypeScript: isShort = trade.quantity < 0 (line 34)
        """
        position = {'longQuantity': 10}
        result = classify_position_direction(position)
        assert result == "LONG", "Long position detection failed"
        
    def test_short_position_negative_quantity(self):
        """
        Short position: shortQuantity < 0
        TypeScript: isShort = trade.quantity < 0 (line 34)
        """
        position = {'shortQuantity': -5}
        result = classify_position_direction(position)
        assert result == "SHORT", "Short position detection failed"
        
    def test_fallback_to_quantity_field(self):
        """
        Fallback to quantity field when longQuantity/shortQuantity missing.
        """
        position = {'quantity': 10}
        result = classify_position_direction(position)
        assert result == "LONG", "Fallback to quantity field failed"
        
        position = {'quantity': -5}
        result = classify_position_direction(position)
        assert result == "SHORT", "Negative quantity should be SHORT"
        
    def test_zero_quantity_defaults_long(self):
        """
        Edge case: Zero quantity defaults to LONG.
        """
        position = {'quantity': 0}
        result = classify_position_direction(position)
        assert result == "LONG", "Zero quantity should default to LONG"


class TestQuantityNormalizationParity:
    """
    Verify quantity normalization matches TypeScript expectations.
    
    TypeScript expects signed quantities: positive=long, negative=short
    Python reference: classifier.py line 51
    """
    
    def test_normalize_long_quantity(self):
        """
        Long position: return positive quantity.
        """
        position = {'longQuantity': 10}
        result = normalize_quantity(position)
        assert result == 10.0, "Long quantity normalization failed"
        
    def test_normalize_short_quantity(self):
        """
        Short position: return negative quantity.
        """
        position = {'shortQuantity': 5}
        result = normalize_quantity(position)
        assert result == -5.0, "Short quantity should be negative"
        
    def test_normalize_quantity_field(self):
        """
        Fallback to quantity field.
        """
        position = {'quantity': 3}
        result = normalize_quantity(position)
        assert result == 3.0, "Quantity field normalization failed"
        
    def test_nested_instrument_quantity(self):
        """
        Handle nested instrument object with quantity.
        Real Schwab API format.
        """
        position = {
            'instrument': {
                'longQuantity': 5
            }
        }
        result = normalize_quantity(position)
        assert result == 5.0, "Nested instrument quantity failed"
        
    def test_missing_quantity_defaults_zero(self):
        """
        Edge case: Missing quantity defaults to 0.
        """
        position = {}
        result = normalize_quantity(position)
        assert result == 0.0, "Missing quantity should default to 0"
        
    def test_null_quantity_handled(self):
        """
        Edge case: Null quantity values handled gracefully.
        """
        position = {'longQuantity': None}
        result = normalize_quantity(position)
        assert result == 0.0, "Null quantity should default to 0"


class TestCreditDebitClassificationParity:
    """
    Verify credit/debit classification matches TypeScript logic.
    
    TypeScript reference: creditPositionAnalysis.ts lines 53-62
    Python reference: classifier.py line 114
    
    Key formula: net = long_cost - short_credit
    - Positive net = DEBIT (paid more than received)
    - Negative net = CREDIT (received more than paid)
    """
    
    def test_debit_spread_classification(self):
        """
        Debit spread: Paid more than received.
        
        Example: Bull call spread - buy 100 call @ $5, sell 110 call @ $2
        Net: 5 - 2 = 3 debit
        """
        legs = [
            {'entry_price': 5.0, 'quantity': 1},   # Long leg (cost)
            {'entry_price': 2.0, 'quantity': -1},  # Short leg (credit)
        ]
        classification, amount = classify_credit_debit(legs)
        
        # Expected: DEBIT, $3
        assert classification == "DEBIT", "Debit spread classification failed"
        assert amount == 3.0, "Debit amount calculation mismatch"
        
    def test_credit_spread_classification(self):
        """
        Credit spread: Received more than paid.
        
        Example: Bull put spread - sell 95 put @ $3, buy 90 put @ $1
        Net: 1 - 3 = -2 credit
        """
        legs = [
            {'entry_price': 1.0, 'quantity': 1},   # Long leg (cost)
            {'entry_price': 3.0, 'quantity': -1},  # Short leg (credit)
        ]
        classification, amount = classify_credit_debit(legs)
        
        # Expected: CREDIT, $2
        assert classification == "CREDIT", "Credit spread classification failed"
        assert amount == 2.0, "Credit amount calculation mismatch"
        
    def test_iron_butterfly_credit(self):
        """
        Iron butterfly: Net credit strategy.
        
        Sell 6000P/6000C @ $15 each, Buy 5950P/6050C @ $5 each
        Net: (5 + 5) - (15 + 15) = -20 credit
        """
        legs = [
            {'entry_price': 5.0, 'quantity': 1},   # Long put (cost)
            {'entry_price': 15.0, 'quantity': -1}, # Short put (credit)
            {'entry_price': 15.0, 'quantity': -1}, # Short call (credit)
            {'entry_price': 5.0, 'quantity': 1},   # Long call (cost)
        ]
        classification, amount = classify_credit_debit(legs)
        
        # Expected: CREDIT, $20
        assert classification == "CREDIT", "Iron butterfly classification failed"
        assert amount == 20.0, "Iron butterfly credit amount mismatch"
        
    def test_multiple_contracts_scaling(self):
        """
        Verify quantity scaling works correctly.
        
        Example: 5 contracts of bull call spread
        """
        legs = [
            {'entry_price': 5.0, 'quantity': 5},   # 5x long calls
            {'entry_price': 2.0, 'quantity': -5},  # 5x short calls
        ]
        classification, amount = classify_credit_debit(legs)
        
        # Expected: DEBIT, $15 (net $3 × 5 contracts)
        assert classification == "DEBIT", "Multiple contracts classification failed"
        assert amount == 15.0, "Multiple contracts amount scaling mismatch"
        
    def test_zero_net_neutral(self):
        """
        Edge case: Exactly zero net = NEUTRAL.
        """
        legs = [
            {'entry_price': 5.0, 'quantity': 1},
            {'entry_price': 5.0, 'quantity': -1},
        ]
        classification, amount = classify_credit_debit(legs)
        
        # Expected: NEUTRAL, $0
        assert classification == "NEUTRAL", "Zero net should be NEUTRAL"
        assert amount == 0.0, "Zero net amount should be 0"
        
    def test_missing_premium_data(self):
        """
        Edge case: No premium data available.
        Should return UNKNOWN.
        """
        legs = [
            {'quantity': 1},  # No entry_price
            {'quantity': -1},
        ]
        classification, amount = classify_credit_debit(legs)
        
        # Expected: UNKNOWN, $0
        assert classification == "UNKNOWN", "Missing premium should return UNKNOWN"
        assert amount == 0.0, "Missing premium amount should be 0"


class TestCreditStrategyDetectionParity:
    """
    Verify credit strategy detection matches TypeScript logic.
    
    TypeScript reference: creditPositionAnalysis.ts lines 36-45
    Python reference: classifier.py line 221
    """
    
    def test_iron_butterfly_is_credit(self):
        """
        Iron butterfly is a credit strategy.
        TypeScript line 36-38: includes 'iron-butterfly'
        """
        result = is_credit_strategy("iron-butterfly", -1, "OPTION")
        assert result is True, "Iron butterfly should be credit strategy"
        
    def test_iron_condor_is_credit(self):
        """
        Iron condor is a credit strategy.
        TypeScript line 39: includes 'iron-condor'
        """
        result = is_credit_strategy("iron-condor", -1, "OPTION")
        assert result is True, "Iron condor should be credit strategy"
        
    def test_credit_spread_is_credit(self):
        """
        Explicit credit spread naming.
        TypeScript line 41: includes 'credit'
        """
        result = is_credit_strategy("credit spread", -1, "OPTION")
        assert result is True, "Credit spread should be credit strategy"
        
    def test_short_call_spread_is_credit(self):
        """
        Short call spread is a credit strategy.
        TypeScript line 42: includes 'short call spread'
        """
        result = is_credit_strategy("short call spread", -1, "OPTION")
        assert result is True, "Short call spread should be credit strategy"
        
    def test_short_put_spread_is_credit(self):
        """
        Short put spread is a credit strategy.
        TypeScript line 43: includes 'short put spread'
        """
        result = is_credit_strategy("short put spread", -1, "OPTION")
        assert result is True, "Short put spread should be credit strategy"
        
    def test_short_option_is_credit(self):
        """
        Short option positions are credit strategies.
        TypeScript line 34-45: isShort && assetType === 'OPTION'
        """
        result = is_credit_strategy("single leg", -1, "OPTION")
        assert result is True, "Short option should be credit strategy"
        
    def test_long_call_spread_not_credit(self):
        """
        Long call spread is NOT a credit strategy (debit).
        """
        result = is_credit_strategy("long call spread", 1, "OPTION")
        assert result is False, "Long call spread should NOT be credit strategy"
        
    def test_long_option_not_credit(self):
        """
        Long option positions are NOT credit strategies.
        """
        result = is_credit_strategy("single leg", 1, "OPTION")
        assert result is False, "Long option should NOT be credit strategy"
        
    def test_vertical_spread_ambiguous(self):
        """
        'Vertical spread' keyword matches credit (could be bull/bear).
        TypeScript line 44: includes 'vertical spread'
        """
        result = is_credit_strategy("vertical spread", -1, "OPTION")
        assert result is True, "Vertical spread should match credit keyword"


class TestRealWorldPositionClassification:
    """
    Test position classification with real production data structures.
    """
    
    def test_schwab_api_long_position(self):
        """
        Real Schwab API format: Long stock position.
        """
        position = {
            'longQuantity': 100,
            'shortQuantity': 0,
            'instrument': {
                'symbol': 'AAPL',
                'assetType': 'EQUITY'
            }
        }
        
        direction = classify_position_direction(position)
        quantity = normalize_quantity(position)
        
        assert direction == "LONG"
        assert quantity == 100.0
        
    def test_schwab_api_short_option(self):
        """
        Real Schwab API format: Short option position.
        """
        position = {
            'longQuantity': 0,
            'shortQuantity': 5,
            'instrument': {
                'symbol': 'SPX   260418C06000000',
                'assetType': 'OPTION'
            }
        }
        
        direction = classify_position_direction(position)
        quantity = normalize_quantity(position)
        
        assert direction == "SHORT"
        assert quantity == -5.0
        
    def test_iron_butterfly_legs_classification(self):
        """
        Real iron butterfly: Classify all 4 legs correctly.
        """
        legs = [
            {'entry_price': 5.0, 'quantity': 1, 'side': 'BUY'},   # Long put
            {'entry_price': 15.0, 'quantity': -1, 'side': 'SELL'}, # Short put
            {'entry_price': 15.0, 'quantity': -1, 'side': 'SELL'}, # Short call
            {'entry_price': 5.0, 'quantity': 1, 'side': 'BUY'},   # Long call
        ]
        
        classification, amount = classify_credit_debit(legs)
        
        # Should be CREDIT with $20 net
        assert classification == "CREDIT"
        assert amount == 20.0
        
    def test_covered_call_single_leg(self):
        """
        Real covered call: Just the short call leg.
        """
        position = {
            'quantity': -1,
            'instrument': {
                'assetType': 'OPTION',
                'optionType': 'CALL'
            }
        }
        
        direction = classify_position_direction(position)
        result = is_credit_strategy("covered call", -1, "OPTION")
        
        assert direction == "SHORT"
        assert result is True  # Short option is credit strategy


class TestPositionEffectParity:
    """Opening/closing effect from transferItems (Schwab API); backend parity helper."""

    def test_opening_from_transfer_items(self):
        tx = {"transferItems": [{"positionEffect": "OPENING"}]}
        assert extract_position_effect(tx) == "OPENING"

    def test_closing_from_transfer_items(self):
        tx = {"transferItems": [{"positionEffect": "CLOSING"}]}
        assert extract_position_effect(tx) == "CLOSING"

    def test_unknown_without_transfer_items(self):
        assert extract_position_effect({}) == "UNKNOWN"


class TestEdgeCasesPositionClassification:
    """
    Edge cases and boundary conditions for position classification.
    """
    
    def test_fractional_quantities(self):
        """
        Edge case: Fractional quantities (partial fills).
        """
        position = {'longQuantity': 2.5}
        result = normalize_quantity(position)
        assert result == 2.5, "Fractional quantity not preserved"
        
    def test_very_large_quantities(self):
        """
        Edge case: Very large institutional positions.
        """
        position = {'longQuantity': 10000}
        result = normalize_quantity(position)
        assert result == 10000.0, "Large quantity not preserved"
        
    def test_mixed_long_short_warning(self):
        """
        Edge case: Both longQuantity and shortQuantity present (should prefer long).
        """
        position = {
            'longQuantity': 5,
            'shortQuantity': 3,  # Should be ignored if longQuantity != 0
        }
        result = normalize_quantity(position)
        assert result == 5.0, "Should prioritize longQuantity over shortQuantity"
        
    def test_empty_legs_array(self):
        """
        Edge case: Empty legs array.
        """
        classification, amount = classify_credit_debit([])
        
        # Should return UNKNOWN with 0 amount
        assert classification == "UNKNOWN"
        assert amount == 0.0
        
    def test_case_insensitive_strategy_names(self):
        """
        Edge case: Strategy names with mixed case.
        """
        result1 = is_credit_strategy("IRON-BUTTERFLY", -1, "OPTION")
        result2 = is_credit_strategy("Iron-Butterfly", -1, "OPTION")
        result3 = is_credit_strategy("iron-butterfly", -1, "OPTION")
        
        # All should return True (case-insensitive)
        assert result1 is True
        assert result2 is True
        assert result3 is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
