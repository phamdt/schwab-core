"""
Constants used throughout schwab-core library.
"""

# Options contract multiplier (standard US options contracts)
CONTRACT_MULTIPLIER = 100

# Risk-free rate (default, can be overridden)
DEFAULT_RISK_FREE_RATE = 0.045  # 4.5%

# Volatility bounds
MIN_IMPLIED_VOLATILITY = 0.01  # 1%
MAX_IMPLIED_VOLATILITY = 3.0   # 300%
DEFAULT_IMPLIED_VOLATILITY = 0.20  # 20%

# Time to expiration bounds
MIN_TIME_TO_EXPIRATION = 0.0001  # ~8.6 seconds, for 0DTE options

# Precision for rounding
PRICE_PRECISION = 2  # 2 decimal places for prices
PNL_PRECISION = 2    # 2 decimal places for P&L
