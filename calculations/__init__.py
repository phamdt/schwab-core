"""
Options calculations module.

Provides P&L calculation functionality for options strategies
and Greeks-based gamma exposure analysis.
"""

from .pnl import (
    calculate_intrinsic_value,
    calculate_option_pnl,
    calculate_strategy_pnl,
    calculate_breakeven_prices,
    calculate_max_profit_loss,
)

from .greeks import (
    calculate_gamma_exposure,
    calculate_net_gamma,
    filter_strike_region,
    extract_greeks_from_contract,
    calculate_effective_gamma_exposure,
)

__all__ = [
    # P&L calculations
    'calculate_intrinsic_value',
    'calculate_option_pnl',
    'calculate_strategy_pnl',
    'calculate_breakeven_prices',
    'calculate_max_profit_loss',
    
    # Greeks calculations
    'calculate_gamma_exposure',
    'calculate_net_gamma',
    'filter_strike_region',
    'extract_greeks_from_contract',
    'calculate_effective_gamma_exposure',
]
