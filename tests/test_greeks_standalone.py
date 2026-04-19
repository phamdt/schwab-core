"""
Standalone unit tests for Greeks calculator module.

Tests gamma exposure calculations, net gamma, strike filtering,
and Greeks extraction from Schwab API responses.

Run: python tests/test_greeks_standalone.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schwab_core.calculations.greeks import (
    calculate_gamma_exposure,
    calculate_net_gamma,
    filter_strike_region,
    extract_greeks_from_contract,
    calculate_effective_gamma_exposure,
)


def test_calculate_gamma_exposure():
    """Test gamma exposure calculation."""
    print("\n✓ Testing calculate_gamma_exposure...")
    
    # Basic calculation
    result = calculate_gamma_exposure(0.05, 1000, 100)
    assert result == 5000.0, f"Expected 5000.0, got {result}"
    
    # Zero gamma
    result = calculate_gamma_exposure(0.0, 1000, 100)
    assert result == 0.0, f"Expected 0.0, got {result}"
    
    # Large open interest
    result = calculate_gamma_exposure(0.03, 50000, 100)
    assert result == 150000.0, f"Expected 150000.0, got {result}"
    
    print("  ✓ All calculate_gamma_exposure tests passed")


def test_calculate_net_gamma():
    """Test net gamma calculation."""
    print("\n✓ Testing calculate_net_gamma...")
    
    # Positive net gamma
    result = calculate_net_gamma(10000.0, 7000.0)
    assert result == 3000.0, f"Expected 3000.0, got {result}"
    
    # Negative net gamma
    result = calculate_net_gamma(5000.0, 12000.0)
    assert result == -7000.0, f"Expected -7000.0, got {result}"
    
    # Zero net gamma
    result = calculate_net_gamma(8000.0, 8000.0)
    assert result == 0.0, f"Expected 0.0, got {result}"
    
    print("  ✓ All calculate_net_gamma tests passed")


def test_filter_strike_region():
    """Test strike region filtering."""
    print("\n✓ Testing filter_strike_region...")
    
    # Default 15% range
    strikes = [90, 95, 100, 105, 110, 115, 120]
    result = filter_strike_region(strikes, 100.0)
    # 100 * (1-0.15) = 85, 100 * (1+0.15) = 115 (but floating point may exclude 115)
    # So 90-110 are definitely included, 115 may be on boundary
    assert 90 in result and 110 in result and 120 not in result, f"Expected strikes 90-110+, got {result}"
    
    # Custom 10% range  
    result = filter_strike_region(strikes, 100.0, pct_range=0.10)
    # 100 * 0.9 = 90, 100 * 1.1 = 110, so 90-110 should be included
    assert 90 in result and 110 in result and 115 not in result, f"Expected strikes 90-110, got {result}"
    
    # Tighter 5% range
    strikes = [90, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 110]
    result = filter_strike_region(strikes, 100.0, pct_range=0.05)
    # Should get 95-105 range
    assert 95 in result and 105 in result and 90 not in result and 110 not in result
    
    # Empty list
    result = filter_strike_region([], 100.0)
    assert result == [], f"Expected [], got {result}"
    
    print("  ✓ All filter_strike_region tests passed")


def test_extract_greeks_from_contract():
    """Test Greeks extraction from Schwab API responses."""
    print("\n✓ Testing extract_greeks_from_contract...")
    
    # Complete Greeks data
    contract = {
        "symbol": "SPY_041425C550",
        "volatility": 18.5,
        "greeks": {
            "delta": 0.45,
            "gamma": 0.05,
            "theta": -0.02,
            "vega": 0.15
        }
    }
    result = extract_greeks_from_contract(contract)
    assert result['delta'] == 0.45
    assert result['gamma'] == 0.05
    assert result['theta'] == -0.02
    assert result['vega'] == 0.15
    assert result['iv'] == 18.5
    
    # Missing greeks object
    contract = {"symbol": "SPY_041425C550", "volatility": 18.5}
    result = extract_greeks_from_contract(contract)
    assert result['delta'] is None
    assert result['gamma'] is None
    assert result['iv'] == 18.5
    
    # None contract data
    try:
        extract_greeks_from_contract(None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot be None or empty" in str(e)
    
    print("  ✓ All extract_greeks_from_contract tests passed")


def test_calculate_effective_gamma_exposure():
    """Test effective gamma exposure calculation."""
    print("\n✓ Testing calculate_effective_gamma_exposure...")
    
    # At the money
    result = calculate_effective_gamma_exposure(10000.0, 0.0, 100.0)
    assert result == 10000.0, f"Expected 10000.0, got {result}"
    
    # 5% away
    result = calculate_effective_gamma_exposure(10000.0, 5.0, 100.0)
    assert abs(result - 9500.0) < 0.1, f"Expected ~9500.0, got {result}"
    
    # 10% away
    result = calculate_effective_gamma_exposure(10000.0, 10.0, 100.0)
    assert abs(result - 9000.0) < 0.1, f"Expected ~9000.0, got {result}"
    
    # Far from spot
    result = calculate_effective_gamma_exposure(10000.0, 100.0, 100.0)
    assert result == 0.0, f"Expected 0.0, got {result}"
    
    print("  ✓ All calculate_effective_gamma_exposure tests passed")


def test_integration_scenario():
    """Test complete flow: extract Greeks -> calculate exposure -> net gamma."""
    print("\n✓ Testing integration scenario...")
    
    # Simulate SPY call and put
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
    
    print("  ✓ Integration scenario passed")


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("Running Greeks Calculator Unit Tests")
    print("="*60)
    
    try:
        test_calculate_gamma_exposure()
        test_calculate_net_gamma()
        test_filter_strike_region()
        test_extract_greeks_from_contract()
        test_calculate_effective_gamma_exposure()
        test_integration_scenario()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
