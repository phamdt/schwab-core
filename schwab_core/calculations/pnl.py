"""
Options P&L Calculator - Python Edition

Fast calculation of options P&L at expiration using intrinsic value.
Formulas MUST match frontend TypeScript implementation exactly for contract testing.

This module extracts P&L calculation logic from:
- Frontend: /finimal/frontend/src/utils/optionsPnLCalculator.ts (lines 76-141)
- Backend: /finimal/app/services/options_analysis_service.py (lines 702-739)
"""

from typing import Dict, List, Optional, Tuple, Any
import logging

from schwab_core.utils.constants import CONTRACT_MULTIPLIER, PRICE_PRECISION, PNL_PRECISION

logger = logging.getLogger(__name__)


def calculate_intrinsic_value(strike: float, underlying_price: float, option_type: str) -> float:
    """
    Calculate intrinsic value of an option at expiration.

    Intrinsic value is the value an option would have if it were exercised immediately.
    - Call: max(0, underlying_price - strike)
    - Put: max(0, strike - underlying_price)

    Args:
        strike: Strike price of the option
        underlying_price: Current price of underlying asset
        option_type: 'call' or 'put' (case-insensitive)

    Returns:
        Intrinsic value (always >= 0)

    Example:
        >>> calculate_intrinsic_value(100, 105, 'call')
        5.0
        >>> calculate_intrinsic_value(100, 95, 'call')
        0.0
        >>> calculate_intrinsic_value(100, 95, 'put')
        5.0
    """
    option_type = option_type.lower()

    if option_type == 'call':
        # Call: max(0, underlying - strike)
        intrinsic = max(0, underlying_price - strike)
    elif option_type == 'put':
        # Put: max(0, strike - underlying)
        intrinsic = max(0, strike - underlying_price)
    else:
        raise ValueError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'.")

    return round(intrinsic, PRICE_PRECISION)


def calculate_option_pnl(
    leg: Dict[str, Any],
    underlying_price: float,
    calculation_type: str = "expiration"
) -> Dict[str, float]:
    """
    Calculate P&L for a single option leg.

    CRITICAL: Formulas MUST match TypeScript implementation (lines 96-106):
    - Long: (intrinsic - premium) × quantity × 100
    - Short: (premium - intrinsic) × quantity × 100

    Premium convention:
    - ALWAYS entered as POSITIVE number
    - Long positions: premium = what you PAID (debit)
    - Short positions: premium = what you RECEIVED (credit)

    Args:
        leg: Dictionary containing:
            - strike (float): Strike price
            - type (str): 'call' or 'put'
            - side (str): 'long' or 'short' (or 'buy'/'sell')
            - quantity (int): Number of contracts
            - price (float): Premium paid/received (ALWAYS positive)
            - groupId (str, optional): Group identifier
        underlying_price: Current price of underlying asset
        calculation_type: 'expiration' (intrinsic value only, default) or 'current' (requires greeks)

    Returns:
        Dictionary containing:
            - pnl: Profit/loss in dollars
            - intrinsic_value: Intrinsic value per share
            - premium_value: Premium paid/received per share
            - strike: Strike price (passthrough)
            - type: Option type (passthrough)
            - side: Position side (passthrough)
            - quantity: Number of contracts (passthrough)

    Raises:
        ValueError: If required fields are missing or invalid

    Example:
        >>> leg = {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5}
        >>> result = calculate_option_pnl(leg, 110)
        >>> result['pnl']
        500.0  # (10 - 5) * 1 * 100
    """
    # Validate inputs
    required_fields = ['strike', 'type', 'side', 'quantity', 'price']
    for field in required_fields:
        if field not in leg:
            raise ValueError(f"Missing required field: {field}")

    strike = float(leg['strike'])
    option_type = str(leg['type']).lower()
    side = str(leg['side']).lower()
    quantity = int(leg['quantity'])
    premium = float(leg['price'])

    # Validate inputs
    if premium < 0:
        logger.warning(
            f"Negative premium detected ({premium}). "
            f"Premiums should always be positive. Using absolute value."
        )
        premium = abs(premium)

    if strike <= 0:
        raise ValueError(f"Invalid strike price ({strike}). Strike must be > 0.")

    if quantity <= 0:
        logger.warning(f"Invalid quantity ({quantity}). Quantity should be > 0.")

    # Normalize side: 'buy' -> 'long', 'sell' -> 'short'
    if side == 'buy':
        side = 'long'
    elif side == 'sell':
        side = 'short'

    if side not in ['long', 'short']:
        raise ValueError(f"Invalid side: {side}. Must be 'long', 'short', 'buy', or 'sell'.")

    # Calculate intrinsic value at expiration
    intrinsic_value = calculate_intrinsic_value(strike, underlying_price, option_type)

    # Calculate P&L (MUST MATCH TypeScript lines 96-106)
    if side == 'long':
        # Long: (intrinsic - premium) × quantity × 100
        # You paid the premium, so it's subtracted from intrinsic value
        pnl = (intrinsic_value - premium) * quantity * CONTRACT_MULTIPLIER
    else:  # short
        # Short: (premium - intrinsic) × quantity × 100
        # You received the premium, so it's your starting credit
        pnl = (premium - intrinsic_value) * quantity * CONTRACT_MULTIPLIER

    return {
        'pnl': round(pnl, PNL_PRECISION),
        'intrinsic_value': round(intrinsic_value, PRICE_PRECISION),
        'premium_value': round(premium, PRICE_PRECISION),
        'strike': strike,
        'type': option_type.upper(),
        'side': side.upper(),
        'quantity': quantity,
    }


def calculate_strategy_pnl(
    legs: List[Dict[str, Any]],
    underlying_price: float,
    calculation_type: str = "expiration"
) -> Dict[str, Any]:
    """
    Calculate P&L for an entire options strategy (multiple legs).

    Args:
        legs: List of option legs (see calculate_option_pnl for leg format)
        underlying_price: Current price of underlying asset
        calculation_type: 'expiration' (default) or 'current'

    Returns:
        Dictionary containing:
            - total_pnl: Sum of all leg P&Ls
            - leg_pnls: List of individual leg P&L results
            - subgroups: Dictionary mapping groupId to group P&L
            - underlying_price: Price at which P&L was calculated

    Example:
        >>> legs = [
        ...     {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
        ...     {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
        ... ]
        >>> result = calculate_strategy_pnl(legs, 105)
        >>> result['total_pnl']
        0.0  # Bull call spread at midpoint
    """
    total_pnl = 0.0
    leg_pnls = []
    subgroups: Dict[str, float] = {}

    for leg in legs:
        leg_result = calculate_option_pnl(leg, underlying_price, calculation_type)
        total_pnl += leg_result['pnl']
        leg_pnls.append(leg_result)

        # Track subgroup P&L
        group_id = leg.get('groupId')
        if group_id:
            subgroups[group_id] = subgroups.get(group_id, 0.0) + leg_result['pnl']

    # Round subgroup P&Ls
    subgroups = {k: round(v, PNL_PRECISION) for k, v in subgroups.items()}

    return {
        'total_pnl': round(total_pnl, PNL_PRECISION),
        'leg_pnls': leg_pnls,
        'subgroups': subgroups,
        'underlying_price': round(underlying_price, PRICE_PRECISION),
    }


def calculate_breakeven_prices(legs: List[Dict[str, Any]]) -> List[float]:
    """
    Calculate breakeven points for an options strategy.

    Breakeven points are prices where the total P&L equals zero.
    Uses linear interpolation between price points to find approximate crossings.

    Args:
        legs: List of option legs (see calculate_option_pnl for leg format)

    Returns:
        List of breakeven prices (sorted, may be empty)

    Example:
        >>> legs = [
        ...     {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
        ... ]
        >>> breakevens = calculate_breakeven_prices(legs)
        >>> breakevens[0]
        105.0  # Strike + premium
    """
    if not legs:
        return []

    # Determine price range from strikes
    strikes = [float(leg['strike']) for leg in legs]
    min_strike = min(strikes)
    max_strike = max(strikes)

    # Expand range by 30%
    expansion = (max_strike - min_strike) * 0.3 if max_strike != min_strike else min_strike * 0.3
    min_price = min_strike - expansion
    max_price = max_strike + expansion

    # Ensure min_price is positive
    min_price = max(0.01, min_price)

    # Generate price points (step = 1.0 for most stocks)
    step = 1.0
    if max_price < 20:
        step = 0.5  # Finer granularity for low-priced stocks

    prices = []
    price = min_price
    while price <= max_price:
        prices.append(round(price, PRICE_PRECISION))
        price += step

    # Calculate P&L at each price point
    pnl_points = []
    for price in prices:
        result = calculate_strategy_pnl(legs, price)
        pnl_points.append((price, result['total_pnl']))

    # Find zero crossings
    breakevens = []
    for i in range(1, len(pnl_points)):
        prev_price, prev_pnl = pnl_points[i - 1]
        curr_price, curr_pnl = pnl_points[i]

        # Check if P&L crosses zero between these two points
        if (prev_pnl <= 0 and curr_pnl > 0) or (prev_pnl > 0 and curr_pnl <= 0):
            # Linear interpolation to find approximate breakeven
            if abs(prev_pnl) + abs(curr_pnl) > 0:
                ratio = abs(prev_pnl) / (abs(prev_pnl) + abs(curr_pnl))
                breakeven = prev_price + (curr_price - prev_price) * ratio
                breakevens.append(round(breakeven, PRICE_PRECISION))

    return sorted(breakevens)


def calculate_max_profit_loss(legs: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    """
    Calculate maximum profit and maximum loss for an options strategy.

    Note: Some strategies have unlimited profit (e.g., long call) or unlimited loss
    (e.g., short call). These are returned as None.

    Args:
        legs: List of option legs (see calculate_option_pnl for leg format)

    Returns:
        Dictionary containing:
            - max_profit: Maximum possible profit (None if unlimited)
            - max_profit_price: Price at which max profit occurs (None if unlimited)
            - max_loss: Maximum possible loss (None if unlimited)
            - max_loss_price: Price at which max loss occurs (None if unlimited)

    Example:
        >>> legs = [
        ...     {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
        ...     {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
        ... ]
        >>> result = calculate_max_profit_loss(legs)
        >>> result['max_profit']
        700.0  # Max profit = (110 - 100 - (5 - 2)) * 100
        >>> result['max_loss']
        -300.0  # Max loss = -(5 - 2) * 100
    """
    if not legs:
        return {
            'max_profit': None,
            'max_profit_price': None,
            'max_loss': None,
            'max_loss_price': None,
        }

    # Determine price range from strikes
    strikes = [float(leg['strike']) for leg in legs]
    min_strike = min(strikes)
    max_strike = max(strikes)

    # Expand range significantly to capture asymptotic behavior
    expansion = (max_strike - min_strike) * 0.5 if max_strike != min_strike else min_strike * 0.5
    min_price = max(0.01, min_strike - expansion)
    max_price = max_strike + expansion

    # Generate price points
    step = 1.0
    if max_price < 20:
        step = 0.5

    prices = []
    price = min_price
    while price <= max_price:
        prices.append(round(price, PRICE_PRECISION))
        price += step

    # Also check extreme prices to detect unlimited profit/loss
    prices.extend([0.01, max_price * 2, max_price * 3])

    # Calculate P&L at each price point
    max_profit = float('-inf')
    max_profit_price = None
    max_loss = float('inf')
    max_loss_price = None

    pnl_values = []
    for price in sorted(set(prices)):
        result = calculate_strategy_pnl(legs, price)
        pnl = result['total_pnl']
        pnl_values.append(pnl)

        if pnl > max_profit:
            max_profit = pnl
            max_profit_price = price

        if pnl < max_loss:
            max_loss = pnl
            max_loss_price = price

    # Check for unlimited profit (monotonically increasing at extremes)
    if len(pnl_values) >= 3:
        # Check last 3 points for increasing trend
        if pnl_values[-1] > pnl_values[-2] > pnl_values[-3]:
            last_diff = pnl_values[-1] - pnl_values[-2]
            prev_diff = pnl_values[-2] - pnl_values[-3]
            # If difference is increasing or staying constant, likely unlimited
            if last_diff >= prev_diff * 0.9:
                max_profit = None
                max_profit_price = None

        # Check first 3 points for decreasing trend (as price goes to 0)
        if pnl_values[0] < pnl_values[1] < pnl_values[2]:
            first_diff = pnl_values[1] - pnl_values[0]
            next_diff = pnl_values[2] - pnl_values[1]
            # If difference is decreasing, max loss might be at price=0
            if first_diff > next_diff * 0.9:
                # Calculate P&L at price = 0 to check if it's the max loss
                result_at_zero = calculate_strategy_pnl(legs, 0.01)
                if result_at_zero['total_pnl'] < max_loss:
                    max_loss = result_at_zero['total_pnl']
                    max_loss_price = 0.0

    return {
        'max_profit': round(max_profit, PNL_PRECISION) if max_profit is not None and max_profit != float('-inf') else None,
        'max_profit_price': round(max_profit_price, PRICE_PRECISION) if max_profit_price is not None else None,
        'max_loss': round(max_loss, PNL_PRECISION) if max_loss is not None and max_loss != float('inf') else None,
        'max_loss_price': round(max_loss_price, PRICE_PRECISION) if max_loss_price is not None else None,
    }
