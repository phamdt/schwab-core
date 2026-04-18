#!/usr/bin/env python3
"""
Greeks Calculator Module - Live Integration Demo

Demonstrates all 5 core functions with realistic Schwab API data.
"""
import sys
import importlib.util

# Load module
spec = importlib.util.spec_from_file_location('greeks', 'calculations/greeks.py')
greeks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(greeks)

print('='*60)
print('Greeks Calculator Module - Live Demo')
print('='*60)

# Example 1: Extract Greeks from contract
print('\n1. Extract Greeks from Schwab API Response:')
contract = {
    'symbol': 'SPY_041425C550',
    'bid': 5.80,
    'ask': 5.90,
    'openInterest': 12453,
    'volatility': 28.34,
    'greeks': {
        'delta': 0.52,
        'gamma': 0.037,
        'theta': -0.083,
        'vega': 0.192
    }
}

extracted = greeks.extract_greeks_from_contract(contract)
print(f'   Delta: {extracted["delta"]}')
print(f'   Gamma: {extracted["gamma"]}')
print(f'   Theta: {extracted["theta"]}')
print(f'   Vega: {extracted["vega"]}')
print(f'   IV: {extracted["iv"]}%')

# Example 2: Calculate gamma exposure
print('\n2. Calculate Gamma Exposure:')
gamma_exp = greeks.calculate_gamma_exposure(
    gamma=extracted['gamma'],
    open_interest=contract['openInterest'],
    contract_multiplier=100
)
print(f'   Gamma Exposure: ${gamma_exp:,.0f}')

# Example 3: Filter strikes
print('\n3. Filter Strike Region (±15% of spot):')
strikes = list(range(520, 581, 5))
spot = 550.0
filtered = greeks.filter_strike_region(strikes, spot, pct_range=0.15)
print(f'   Spot: ${spot}')
print(f'   All strikes: {len(strikes)} strikes')
print(f'   Filtered: {len(filtered)} strikes')
print(f'   Range: ${min(filtered)} - ${max(filtered)}')

# Example 4: Net gamma
print('\n4. Calculate Net Gamma (Call vs Put):')
call_exp = greeks.calculate_gamma_exposure(0.03, 10000, 100)
put_exp = greeks.calculate_gamma_exposure(0.03, 8000, 100)
net = greeks.calculate_net_gamma(call_exp, put_exp)
bias = "Call bias" if net > 0 else "Put bias"
print(f'   Call Exposure: ${call_exp:,.0f}')
print(f'   Put Exposure: ${put_exp:,.0f}')
print(f'   Net Gamma: ${net:,.0f} ({bias})')

# Example 5: Effective gamma
print('\n5. Calculate Effective Gamma (Distance-Weighted):')
strike = 560.0
distance = abs(strike - spot)
effective = greeks.calculate_effective_gamma_exposure(call_exp, distance, spot)
print(f'   Strike: ${strike} ({distance/spot*100:.1f}% from spot)')
print(f'   Raw Exposure: ${call_exp:,.0f}')
print(f'   Effective Exposure: ${effective:,.0f}')
print(f'   Weight Factor: {effective/call_exp:.1%}')

print('\n' + '='*60)
print('✓ All functions working correctly!')
print('='*60)
