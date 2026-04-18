"""
Schwab Core - Shared business logic for Schwab API integration.

This package consolidates duplicated Schwab-related logic across microservices:
- Position classification (long/short, credit/debit)
- Symbol processing (normalization, parsing)
- Strategy detection (vertical spreads, iron butterfly, etc.)
- P&L calculations and Greeks
- Data transformations
"""

__version__ = "1.0.0"

__all__ = [
    "broker",
    "transformers",
    "utils",
    "strategy",
    "calculations",
    "position",
    "symbol",
]
