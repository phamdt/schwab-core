"""
Schwab Core - Shared business logic for broker API integration.

Subpackages:
- broker: Broker abstraction layer (Schwab, Tradier, extensible)
- calculations: Greeks, P&L
- position: Classification (long/short, credit/debit)
- strategy: Detection (vertical spreads, iron butterfly, etc.)
- symbol: Normalization, parsing
- transformers: Data transformations (accounts, positions, option chains)
- utils: Shared constants
"""

__version__ = "0.2.0"

__all__ = [
    "broker",
    "calculations",
    "position",
    "strategy",
    "symbol",
    "transformers",
    "utils",
]
