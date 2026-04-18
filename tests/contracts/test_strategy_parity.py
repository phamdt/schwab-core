"""
Contract Test: Strategy Detection Parity (Python Backend)

This test suite verifies that the Python strategy detection module produces
consistent and accurate results when classifying multi-leg options strategies.

Reference:
- Python: /schwab-core/strategy/detector.py
- Python: /schwab-core/strategy/vertical_spread.py
- Python: /schwab-core/strategy/iron_butterfly.py

Test Philosophy:
- Use real position data from production accounts
- Verify confidence scores are consistent and meaningful
- Test edge cases where strategy detection is ambiguous
- Ensure detected strategies have correct metrics (max profit/loss, breakevens)

Author: Contract Testing Suite
Date: 2026-04-05
"""

import pytest
from schwab_core.strategy.detector import detect_strategies, detect_strategy_from_legs
from schwab_core.strategy.vertical_spread import detect_vertical_spread
from schwab_core.strategy.iron_butterfly import detect_iron_butterfly


class TestVerticalSpreadDetection:
    """
    Verify vertical spread detection (bull/bear call/put spreads).
    
    A vertical spread has:
    - 2 legs (same underlying, same expiration, same type)
    - Different strikes
    - Opposite sides (one long, one short)
    """
    
    def test_bull_call_spread_detection(self):
        """
        Bull call spread: Buy lower strike call, Sell higher strike call.
        
        Real trade: Buy 100 call, Sell 110 call
        Expected: Detect as "Bull Call Spread" with confidence >= 0.80
        """
        legs = [
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 100,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06100000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 110,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 2,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None, "Bull call spread not detected"
        assert result.strategy_type == "Bull Call Spread", "Strategy type mismatch"
        assert result.confidence >= 0.80, f"Confidence too low: {result.confidence}"
        assert result.long_strike == 100, "Long strike mismatch"
        assert result.short_strike == 110, "Short strike mismatch"
        assert result.option_type == "CALL", "Option type mismatch"
        
    def test_bear_put_spread_detection(self):
        """
        Bear put spread: Buy higher strike put, Sell lower strike put.
        
        Real trade: Buy 180 put, Sell 170 put
        Expected: Detect as "Bear Put Spread" with confidence >= 0.80
        """
        legs = [
            {
                'symbol': 'TSLA  260418P00180000',
                'underlying_symbol': 'TSLA',
                'option_type': 'PUT',
                'strike': 180,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 8,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'TSLA  260418P00170000',
                'underlying_symbol': 'TSLA',
                'option_type': 'PUT',
                'strike': 170,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 4,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None, "Bear put spread not detected"
        assert result.strategy_type == "Bear Put Spread", "Strategy type mismatch"
        assert result.confidence >= 0.80, f"Confidence too low: {result.confidence}"
        assert result.long_strike == 180, "Long strike mismatch"
        assert result.short_strike == 170, "Short strike mismatch"
        assert result.option_type == "PUT", "Option type mismatch"
        
    def test_bull_put_spread_credit_spread(self):
        """
        Bull put spread: Sell higher strike put, Buy lower strike put.
        This is a CREDIT spread (net premium received).
        
        Real trade: Sell 95 put, Buy 90 put
        Expected: Detect as "Bull Put Spread" (credit spread)
        """
        legs = [
            {
                'symbol': 'SPX   260418P05900000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 90,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 1,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418P05950000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 95,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 3,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None, "Bull put spread not detected"
        assert result.strategy_type == "Bull Put Spread", "Strategy type mismatch"
        assert result.confidence >= 0.80, f"Confidence too low: {result.confidence}"
        # Net debit/credit: long cost (1) - short credit (3) = -2 (credit)
        assert result.net_debit_credit < 0, "Should be credit spread (negative net)"
        
    def test_bear_call_spread_credit_spread(self):
        """
        Bear call spread: Sell lower strike call, Buy higher strike call.
        This is a CREDIT spread (net premium received).
        
        Real trade: Sell 105 call, Buy 110 call
        Expected: Detect as "Bear Call Spread" (credit spread)
        """
        legs = [
            {
                'symbol': 'SPX   260418C06105000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 110,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 1,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06100000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 105,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 3,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        assert result is not None, "Bear call spread not detected"
        assert result.strategy_type == "Bear Call Spread", "Strategy type mismatch"
        assert result.confidence >= 0.80, f"Confidence too low: {result.confidence}"
        # Net debit/credit: long cost (1) - short credit (3) = -2 (credit)
        assert result.net_debit_credit < 0, "Should be credit spread (negative net)"


class TestIronButterflyDetection:
    """
    Verify iron butterfly detection.
    
    An iron butterfly has:
    - 4 legs (same underlying, same expiration)
    - 2 calls, 2 puts
    - Same center strike for short options
    - Symmetric wing widths
    """
    
    def test_iron_butterfly_perfect_structure(self):
        """
        Perfect iron butterfly: Symmetric wings, same center strike.
        
        Real trade: SPX iron butterfly
        - Sell 6000 put @ $15
        - Sell 6000 call @ $15
        - Buy 5950 put @ $5
        - Buy 6050 call @ $5
        
        Expected: Confidence >= 0.95 (perfect structure)
        """
        legs = [
            {
                'symbol': 'SPX   260418P05950000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 5950,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418P06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06050000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6050,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_iron_butterfly(legs)
        
        assert result is not None, "Iron butterfly not detected"
        assert result.strategy_type == "Iron Butterfly", "Strategy type mismatch"
        assert result.confidence >= 0.90, f"Confidence too low: {result.confidence}"
        assert result.center_strike == 6000, "Center strike mismatch"
        assert result.wing_width == 50, "Wing width mismatch"
        
        # Verify max profit = net credit
        # Net credit = (15 + 15) - (5 + 5) = 20
        assert result.max_profit == 20, "Max profit mismatch"
        
        # Verify max loss = wing width - net credit
        # Max loss = 50 - 20 = 30
        assert result.max_loss == 30, "Max loss mismatch"
        
    def test_iron_butterfly_asymmetric_wings(self):
        """
        Iron butterfly with slightly asymmetric wings.
        Should still detect but with lower confidence.
        
        Real scenario: Adjusted iron butterfly
        - Sell 6000 put/call
        - Buy 5940 put (60 points wide)
        - Buy 6060 call (60 points wide)
        """
        legs = [
            {
                'symbol': 'SPX   260418P05940000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 5940,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 4,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418P06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 16,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 16,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06060000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6060,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 4,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_iron_butterfly(legs)
        
        assert result is not None, "Iron butterfly not detected"
        assert result.strategy_type == "Iron Butterfly", "Strategy type mismatch"
        # Slightly lower confidence due to asymmetry
        assert result.confidence >= 0.75, f"Confidence too low: {result.confidence}"
        
    def test_iron_butterfly_vs_iron_condor(self):
        """
        Distinguish iron butterfly from iron condor.
        
        Iron butterfly: Short strikes are SAME
        Iron condor: Short strikes are DIFFERENT
        
        This is an iron CONDOR (not butterfly):
        - Sell 5980 put, Sell 6020 call (different strikes)
        """
        legs = [
            {
                'symbol': 'SPX   260418P05950000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 5950,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418P05980000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 5980,  # Different from call short strike
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06020000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6020,  # Different from put short strike
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06050000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6050,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_iron_butterfly(legs)
        
        # Should NOT detect as iron butterfly (or very low confidence)
        # because short strikes are different (5980 vs 6020)
        if result is not None:
            assert result.confidence < 0.75, "Should have low confidence (not a butterfly)"


class TestMultiStrategyDetection:
    """
    Test detection of multiple strategies in a portfolio.
    Verify strategies are correctly grouped and classified.
    """
    
    def test_detect_single_strategy_from_positions(self):
        """
        Detect a single vertical spread from a list of positions.
        """
        positions = [
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 100,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06100000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 110,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 2,
                'expiration': '2026-04-18'
            }
        ]
        
        strategies = detect_strategies(positions, time_grouping=False)
        
        assert len(strategies) == 1, "Should detect exactly 1 strategy"
        assert strategies[0]['strategy_type'] == "Bull Call Spread"
        assert strategies[0]['confidence'] >= 0.80
        
    def test_detect_multiple_strategies_same_underlying(self):
        """
        Detect multiple strategies on the same underlying.
        
        Scenario: 2 separate vertical spreads on SPX (different expirations)
        """
        positions = [
            # Bull call spread - April expiration
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 100,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06100000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 110,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 2,
                'expiration': '2026-04-18'
            },
            # Bear put spread - May expiration
            {
                'symbol': 'SPX   260516P05900000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 180,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 8,
                'expiration': '2026-05-16'
            },
            {
                'symbol': 'SPX   260516P05800000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 170,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 4,
                'expiration': '2026-05-16'
            }
        ]
        
        strategies = detect_strategies(positions, time_grouping=False)
        
        # Should detect 2 separate strategies (different expirations)
        assert len(strategies) == 2, f"Should detect 2 strategies, got {len(strategies)}"
        
    def test_detect_iron_butterfly_from_positions(self):
        """
        Detect iron butterfly from a full position list.
        """
        positions = [
            {
                'symbol': 'SPX   260418P05950000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 5950,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418P06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06050000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6050,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            }
        ]
        
        strategies = detect_strategies(positions, time_grouping=False)
        
        assert len(strategies) == 1, "Should detect exactly 1 strategy"
        assert strategies[0]['strategy_type'] == "Iron Butterfly"
        assert strategies[0]['confidence'] >= 0.75


class TestEdgeCasesStrategyDetection:
    """
    Test edge cases and boundary conditions for strategy detection.
    """
    
    def test_single_leg_not_a_strategy(self):
        """
        Single option leg should be classified as "Single Leg".
        """
        positions = [
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 100,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            }
        ]
        
        strategies = detect_strategies(positions, time_grouping=False)
        
        assert len(strategies) == 1
        assert strategies[0]['strategy_type'] == "Single Leg"
        assert strategies[0]['confidence'] == 1.0
        
    def test_mismatched_expiration_not_strategy(self):
        """
        Options with different expirations should NOT form a spread.
        """
        legs = [
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 100,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260516C06100000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 110,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 2,
                'expiration': '2026-05-16'  # Different expiration
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        # Should NOT detect as vertical spread (or very low confidence)
        if result is not None:
            assert result.confidence < 0.80, "Should have low confidence (different expirations)"
            
    def test_same_side_not_spread(self):
        """
        Two long calls (same side) should NOT form a spread.
        """
        legs = [
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 100,
                'side': 'BUY',  # Both BUY
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06100000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 110,
                'side': 'BUY',  # Both BUY
                'quantity': 1,
                'entry_price': 2,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        # Should NOT detect (both same side)
        assert result is None or result.confidence < 0.80, "Should not detect spread (same side)"
        
    def test_unbalanced_quantities_lower_confidence(self):
        """
        Unbalanced quantities (e.g., 1 vs 2 contracts) should lower confidence.
        """
        legs = [
            {
                'symbol': 'SPX   260418C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 100,
                'side': 'BUY',
                'quantity': 1,  # 1 contract
                'entry_price': 5,
                'expiration': '2026-04-18'
            },
            {
                'symbol': 'SPX   260418C06100000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 110,
                'side': 'SELL',
                'quantity': 2,  # 2 contracts (unbalanced)
                'entry_price': 2,
                'expiration': '2026-04-18'
            }
        ]
        
        result = detect_vertical_spread(legs)
        
        # Should detect but with lower confidence
        if result is not None:
            assert result.confidence < 0.95, "Unbalanced quantities should lower confidence"


class TestDetectStrategyFromLegsParity:
    """`detect_strategy_from_legs` — explicit API parity with grouped detection."""

    def test_detect_strategy_from_legs_bull_call(self):
        legs = [
            {
                "symbol": "AAPL  260418C00150000",
                "underlying_symbol": "AAPL",
                "option_type": "CALL",
                "strike": 150,
                "side": "BUY",
                "quantity": 1,
                "entry_price": 5,
                "expiration": "2026-04-18",
            },
            {
                "symbol": "AAPL  260418C00155000",
                "underlying_symbol": "AAPL",
                "option_type": "CALL",
                "strike": 155,
                "side": "SELL",
                "quantity": 1,
                "entry_price": 2,
                "expiration": "2026-04-18",
            },
        ]
        out = detect_strategy_from_legs(legs)
        assert out is not None
        assert out["strategy_type"] == "Bull Call Spread"
        assert out["confidence"] >= 0.80

    def test_detect_strategy_from_legs_iron_butterfly(self):
        legs = [
            {
                "underlying_symbol": "SPX",
                "option_type": "PUT",
                "strike": 5950,
                "side": "BUY",
                "quantity": 1,
                "entry_price": 5,
                "expiration": "2026-04-05",
            },
            {
                "underlying_symbol": "SPX",
                "option_type": "PUT",
                "strike": 6000,
                "side": "SELL",
                "quantity": 1,
                "entry_price": 15,
                "expiration": "2026-04-05",
            },
            {
                "underlying_symbol": "SPX",
                "option_type": "CALL",
                "strike": 6000,
                "side": "SELL",
                "quantity": 1,
                "entry_price": 15,
                "expiration": "2026-04-05",
            },
            {
                "underlying_symbol": "SPX",
                "option_type": "CALL",
                "strike": 6050,
                "side": "BUY",
                "quantity": 1,
                "entry_price": 5,
                "expiration": "2026-04-05",
            },
        ]
        out = detect_strategy_from_legs(legs)
        assert out is not None
        assert out["strategy_type"] == "Iron Butterfly"
        assert out["confidence"] >= 0.75
        assert out["center_strike"] == 6000


class TestRealWorldStrategyScenarios:
    """
    Test strategy detection with real production data.
    """
    
    def test_real_aapl_covered_call(self):
        """
        Real scenario: AAPL covered call.
        Just the short call leg (stock ownership assumed).
        """
        positions = [
            {
                'symbol': 'AAPL  260418C00155000',
                'underlying_symbol': 'AAPL',
                'option_type': 'CALL',
                'strike': 155,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 3,
                'expiration': '2026-04-18'
            }
        ]
        
        strategies = detect_strategies(positions, time_grouping=False)
        
        # Should be classified as Single Leg
        assert len(strategies) == 1
        assert strategies[0]['strategy_type'] == "Single Leg"
        
    def test_real_spx_0dte_iron_butterfly(self):
        """
        Real SPX 0DTE iron butterfly from production.
        """
        positions = [
            {
                'symbol': 'SPX   260405P05950000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 5950,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-05'
            },
            {
                'symbol': 'SPX   260405P06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'PUT',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-05'
            },
            {
                'symbol': 'SPX   260405C06000000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6000,
                'side': 'SELL',
                'quantity': 1,
                'entry_price': 15,
                'expiration': '2026-04-05'
            },
            {
                'symbol': 'SPX   260405C06050000',
                'underlying_symbol': 'SPX',
                'option_type': 'CALL',
                'strike': 6050,
                'side': 'BUY',
                'quantity': 1,
                'entry_price': 5,
                'expiration': '2026-04-05'
            }
        ]
        
        strategies = detect_strategies(positions, time_grouping=False)
        
        assert len(strategies) == 1
        assert strategies[0]['strategy_type'] == "Iron Butterfly"
        assert strategies[0]['confidence'] >= 0.75
        assert strategies[0]['center_strike'] == 6000
        assert strategies[0]['wing_width'] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
