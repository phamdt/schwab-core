"""
Unit tests for Greeks calculator module.

Tests gamma exposure calculations, net gamma, strike filtering,
and Greeks extraction from Schwab API responses.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from schwab_core.calculations.greeks import (
    calculate_gamma_exposure,
    calculate_net_gamma,
    filter_strike_region,
    extract_greeks_from_contract,
    calculate_effective_gamma_exposure,
)


class TestCalculateGammaExposure:
    """Test gamma exposure calculation."""
    
    def test_basic_calculation(self):
        """Test basic gamma exposure calculation."""
        result = calculate_gamma_exposure(
            gamma=0.05,
            open_interest=1000,
            contract_multiplier=100
        )
        assert result == 5000.0
    
    def test_zero_gamma(self):
        """Test with zero gamma (expired options)."""
        result = calculate_gamma_exposure(
            gamma=0.0,
            open_interest=1000,
            contract_multiplier=100
        )
        assert result == 0.0
    
    def test_zero_open_interest(self):
        """Test with zero open interest."""
        result = calculate_gamma_exposure(
            gamma=0.05,
            open_interest=0,
            contract_multiplier=100
        )
        assert result == 0.0
    
    def test_custom_multiplier(self):
        """Test with custom contract multiplier."""
        result = calculate_gamma_exposure(
            gamma=0.05,
            open_interest=1000,
            contract_multiplier=10  # Mini options
        )
        assert result == 500.0
    
    def test_large_open_interest(self):
        """Test with large open interest (SPY scenario)."""
        result = calculate_gamma_exposure(
            gamma=0.03,
            open_interest=50000,
            contract_multiplier=100
        )
        assert result == 150000.0
    
    def test_negative_gamma(self):
        """Test with negative gamma (short positions)."""
        result = calculate_gamma_exposure(
            gamma=-0.05,
            open_interest=1000,
            contract_multiplier=100
        )
        assert result == -5000.0


class TestCalculateNetGamma:
    """Test net gamma calculation."""
    
    def test_positive_net_gamma(self):
        """Test when calls dominate (positive net gamma)."""
        result = calculate_net_gamma(
            call_gamma_exposure=10000.0,
            put_gamma_exposure=7000.0
        )
        assert result == 3000.0
    
    def test_negative_net_gamma(self):
        """Test when puts dominate (negative net gamma)."""
        result = calculate_net_gamma(
            call_gamma_exposure=5000.0,
            put_gamma_exposure=12000.0
        )
        assert result == -7000.0
    
    def test_zero_net_gamma(self):
        """Test balanced gamma (zero net)."""
        result = calculate_net_gamma(
            call_gamma_exposure=8000.0,
            put_gamma_exposure=8000.0
        )
        assert result == 0.0
    
    def test_zero_call_gamma(self):
        """Test with zero call gamma."""
        result = calculate_net_gamma(
            call_gamma_exposure=0.0,
            put_gamma_exposure=5000.0
        )
        assert result == -5000.0
    
    def test_zero_put_gamma(self):
        """Test with zero put gamma."""
        result = calculate_net_gamma(
            call_gamma_exposure=5000.0,
            put_gamma_exposure=0.0
        )
        assert result == 5000.0


class TestFilterStrikeRegion:
    """Test strike region filtering."""
    
    def test_default_15_percent_range(self):
        """Test default ±15% filtering."""
        strikes = [90, 95, 100, 105, 110, 115, 120]
        result = filter_strike_region(strikes, spot_price=100.0)
        assert result == [90, 95, 100, 105, 110, 115]
    
    def test_custom_10_percent_range(self):
        """Test custom ±10% filtering."""
        strikes = [90, 95, 100, 105, 110, 115, 120]
        result = filter_strike_region(strikes, spot_price=100.0, pct_range=0.10)
        assert result == [90, 95, 100, 105, 110]
    
    def test_custom_5_percent_range(self):
        """Test tight ±5% filtering."""
        strikes = [90, 95, 100, 105, 110, 115, 120]
        result = filter_strike_region(strikes, spot_price=100.0, pct_range=0.05)
        assert result == [95, 100, 105]
    
    def test_empty_strikes_list(self):
        """Test with empty strikes list."""
        result = filter_strike_region([], spot_price=100.0)
        assert result == []
    
    def test_no_strikes_in_range(self):
        """Test when no strikes fall in range."""
        strikes = [50, 60, 70, 150, 160, 170]
        result = filter_strike_region(strikes, spot_price=100.0, pct_range=0.15)
        assert result == []
    
    def test_all_strikes_in_range(self):
        """Test when all strikes fall in range."""
        strikes = [95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105]
        result = filter_strike_region(strikes, spot_price=100.0, pct_range=0.15)
        assert len(result) == 11
    
    def test_spy_realistic_scenario(self):
        """Test realistic SPY strikes scenario."""
        strikes = list(range(520, 581, 5))  # SPY strikes $520-$580
        result = filter_strike_region(strikes, spot_price=550.0, pct_range=0.15)
        # Should include strikes from 467.5 to 632.5
        assert 520 in result
        assert 525 in result
        assert 550 in result
        assert 575 in result
        assert 580 in result


class TestExtractGreeksFromContract:
    """Test Greeks extraction from Schwab API responses."""
    
    def test_complete_greeks_data(self):
        """Test extraction with complete Greeks data."""
        contract_data = {
            "symbol": "SPY_041425C550",
            "bid": 1.25,
            "ask": 1.30,
            "last": 1.27,
            "volatility": 18.5,
            "greeks": {
                "delta": 0.45,
                "gamma": 0.05,
                "theta": -0.02,
                "vega": 0.15
            }
        }
        
        result = extract_greeks_from_contract(contract_data)
        
        assert result['delta'] == 0.45
        assert result['gamma'] == 0.05
        assert result['theta'] == -0.02
        assert result['vega'] == 0.15
        assert result['iv'] == 18.5
    
    def test_missing_greeks_object(self):
        """Test when greeks object is missing."""
        contract_data = {
            "symbol": "SPY_041425C550",
            "volatility": 18.5
        }
        
        result = extract_greeks_from_contract(contract_data)
        
        assert result['delta'] is None
        assert result['gamma'] is None
        assert result['theta'] is None
        assert result['vega'] is None
        assert result['iv'] == 18.5
    
    def test_partial_greeks_data(self):
        """Test with partial Greeks data (some missing)."""
        contract_data = {
            "symbol": "SPY_041425C550",
            "volatility": 18.5,
            "greeks": {
                "delta": 0.45,
                "gamma": 0.05
                # theta and vega missing
            }
        }
        
        result = extract_greeks_from_contract(contract_data)
        
        assert result['delta'] == 0.45
        assert result['gamma'] == 0.05
        assert result['theta'] is None
        assert result['vega'] is None
        assert result['iv'] == 18.5
    
    def test_missing_volatility(self):
        """Test when IV/volatility is missing."""
        contract_data = {
            "symbol": "SPY_041425C550",
            "greeks": {
                "delta": 0.45,
                "gamma": 0.05,
                "theta": -0.02,
                "vega": 0.15
            }
        }
        
        result = extract_greeks_from_contract(contract_data)
        
        assert result['delta'] == 0.45
        assert result['gamma'] == 0.05
        assert result['theta'] == -0.02
        assert result['vega'] == 0.15
        assert result['iv'] is None
    
    def test_zero_values(self):
        """Test with zero Greeks values (valid for expired options)."""
        contract_data = {
            "symbol": "SPY_041425C550",
            "volatility": 0.0,
            "greeks": {
                "delta": 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0
            }
        }
        
        result = extract_greeks_from_contract(contract_data)
        
        assert result['delta'] == 0.0
        assert result['gamma'] == 0.0
        assert result['theta'] == 0.0
        assert result['vega'] == 0.0
        assert result['iv'] == 0.0
    
    def test_none_contract_data(self):
        """Test with None contract data."""
        with pytest.raises(ValueError, match="contract_data cannot be None or empty"):
            extract_greeks_from_contract(None)
    
    def test_empty_contract_data(self):
        """Test with empty contract data."""
        with pytest.raises(ValueError, match="contract_data cannot be None or empty"):
            extract_greeks_from_contract({})
    
    def test_realistic_atm_call(self):
        """Test with realistic ATM call option data."""
        contract_data = {
            "symbol": "AAPL_041125C170",
            "description": "AAPL Apr 11 2025 170 Call",
            "bid": 5.80,
            "ask": 5.90,
            "last": 5.85,
            "mark": 5.85,
            "openInterest": 12453,
            "volatility": 28.34,
            "delta": 0.52,
            "greeks": {
                "delta": 0.52,
                "gamma": 0.037,
                "theta": -0.083,
                "vega": 0.192,
                "rho": 0.045
            }
        }
        
        result = extract_greeks_from_contract(contract_data)
        
        assert result['delta'] == 0.52
        assert result['gamma'] == 0.037
        assert result['theta'] == -0.083
        assert result['vega'] == 0.192
        assert result['iv'] == 28.34
    
    def test_realistic_otm_put(self):
        """Test with realistic OTM put option data."""
        contract_data = {
            "symbol": "SPY_041425P540",
            "description": "SPY Apr 14 2025 540 Put",
            "bid": 2.10,
            "ask": 2.15,
            "last": 2.12,
            "mark": 2.125,
            "openInterest": 8932,
            "volatility": 21.56,
            "delta": -0.28,
            "greeks": {
                "delta": -0.28,
                "gamma": 0.021,
                "theta": -0.045,
                "vega": 0.134,
                "rho": -0.032
            }
        }
        
        result = extract_greeks_from_contract(contract_data)
        
        assert result['delta'] == -0.28
        assert result['gamma'] == 0.021
        assert result['theta'] == -0.045
        assert result['vega'] == 0.134
        assert result['iv'] == 21.56


class TestCalculateEffectiveGammaExposure:
    """Test effective gamma exposure calculation."""
    
    def test_at_the_money(self):
        """Test effective gamma at the money (distance = 0)."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=10000.0,
            distance_from_spot=0.0,
            spot_price=100.0
        )
        assert result == 10000.0
    
    def test_5_percent_away(self):
        """Test effective gamma 5% away from spot."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=10000.0,
            distance_from_spot=5.0,
            spot_price=100.0
        )
        assert result == pytest.approx(9500.0)
    
    def test_10_percent_away(self):
        """Test effective gamma 10% away from spot."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=10000.0,
            distance_from_spot=10.0,
            spot_price=100.0
        )
        assert result == pytest.approx(9000.0)
    
    def test_negative_distance(self):
        """Test with negative distance (below spot)."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=10000.0,
            distance_from_spot=-5.0,
            spot_price=100.0
        )
        assert result == pytest.approx(9500.0)
    
    def test_far_from_spot(self):
        """Test far from spot (100% away, weight = 0)."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=10000.0,
            distance_from_spot=100.0,
            spot_price=100.0
        )
        assert result == 0.0
    
    def test_beyond_100_percent(self):
        """Test beyond 100% away (weight clamped to 0)."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=10000.0,
            distance_from_spot=150.0,
            spot_price=100.0
        )
        assert result == 0.0
    
    def test_zero_spot_price(self):
        """Test with zero spot price (edge case)."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=10000.0,
            distance_from_spot=5.0,
            spot_price=0.0
        )
        assert result == 0.0
    
    def test_zero_gamma_exposure(self):
        """Test with zero gamma exposure."""
        result = calculate_effective_gamma_exposure(
            gamma_exposure=0.0,
            distance_from_spot=5.0,
            spot_price=100.0
        )
        assert result == 0.0
    
    def test_realistic_spy_scenario(self):
        """Test realistic SPY scenario."""
        # SPY at $550, strike at $560 (10 points away)
        result = calculate_effective_gamma_exposure(
            gamma_exposure=150000.0,
            distance_from_spot=10.0,
            spot_price=550.0
        )
        # ~1.8% away, weight = 0.9818
        assert result == pytest.approx(147272.72, rel=1e-2)


class TestIntegrationScenarios:
    """Integration tests with realistic scenarios."""
    
    def test_complete_gamma_calculation_flow(self):
        """Test complete flow: extract Greeks -> calculate exposure -> net gamma."""
        # Simulate SPY call and put at same strike
        call_contract = {
            "symbol": "SPY_041425C550",
            "openInterest": 10000,
            "greeks": {"gamma": 0.03},
            "volatility": 18.5
        }
        
        put_contract = {
            "symbol": "SPY_041425P550",
            "openInterest": 8000,
            "greeks": {"gamma": 0.03},
            "volatility": 19.2
        }
        
        # Extract Greeks
        call_greeks = extract_greeks_from_contract(call_contract)
        put_greeks = extract_greeks_from_contract(put_contract)
        
        # Calculate exposures
        call_exposure = calculate_gamma_exposure(
            gamma=call_greeks['gamma'],
            open_interest=call_contract['openInterest']
        )
        
        put_exposure = calculate_gamma_exposure(
            gamma=put_greeks['gamma'],
            open_interest=put_contract['openInterest']
        )
        
        # Calculate net gamma
        net = calculate_net_gamma(call_exposure, put_exposure)
        
        assert call_exposure == 30000.0
        assert put_exposure == 24000.0
        assert net == 6000.0
    
    def test_strike_filtering_and_exposure_calculation(self):
        """Test filtering strikes then calculating total exposure."""
        strikes = [520, 525, 530, 535, 540, 545, 550, 555, 560, 565, 570]
        spot_price = 550.0
        
        # Filter to ±10% range
        filtered_strikes = filter_strike_region(
            strikes, spot_price, pct_range=0.10
        )
        
        # Should be 530-570
        assert min(filtered_strikes) >= 495  # 550 * 0.9
        assert max(filtered_strikes) <= 605  # 550 * 1.1
        
        # Calculate total exposure for filtered strikes
        total_exposure = 0
        for strike in filtered_strikes:
            exposure = calculate_gamma_exposure(
                gamma=0.03,
                open_interest=5000
            )
            total_exposure += exposure
        
        assert total_exposure == 15000.0 * len(filtered_strikes)
