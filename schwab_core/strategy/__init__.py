"""
Strategy Detection Module for schwab-core

Detects and classifies multi-leg options strategies including:
- Vertical Spreads (Bull/Bear Put/Call Spreads)
- Iron Butterflies
- Custom strategies

Main entry point: detect_strategies()
"""
from .detector import detect_strategies, detect_strategy_from_legs
from .vertical_spread import detect_vertical_spread, calculate_vertical_spread_metrics
from .iron_butterfly import detect_iron_butterfly, validate_iron_butterfly_quantities
from .grouper import (
    group_by_time,
    group_by_expiration,
    group_by_underlying,
    group_by_expiration_and_underlying,
    group_by_order_id,
    extract_expiration_from_symbol,
    parse_entry_time,
)

__all__ = [
    # Main detection functions
    'detect_strategies',
    'detect_strategy_from_legs',
    
    # Strategy-specific detectors
    'detect_vertical_spread',
    'detect_iron_butterfly',
    
    # Metrics and validation
    'calculate_vertical_spread_metrics',
    'validate_iron_butterfly_quantities',
    
    # Grouping utilities
    'group_by_time',
    'group_by_expiration',
    'group_by_underlying',
    'group_by_expiration_and_underlying',
    'group_by_order_id',
    'extract_expiration_from_symbol',
    'parse_entry_time',
]
