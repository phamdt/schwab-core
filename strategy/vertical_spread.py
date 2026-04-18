"""
Vertical Spread Detection Module

Detects and classifies vertical spread strategies:
- Bear Put Spread (debit)
- Bull Put Spread (credit)
- Bull Call Spread (debit)
- Bear Call Spread (credit)
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VerticalSpreadResult:
    """Result from vertical spread detection"""
    strategy_type: str
    confidence: float
    strikes: tuple
    net_debit_credit: Optional[float]
    long_strike: float
    short_strike: float
    option_type: str
    notes: str


def detect_vertical_spread(legs: List[Dict]) -> Optional[VerticalSpreadResult]:
    """
    Detect vertical spread strategies from a list of option legs.
    
    Rules:
    - Must have exactly 2 legs
    - Both legs must be same option type (PUT or CALL)
    - Different strike prices
    - Matched quantities (absolute values)
    - One BUY leg and one SELL leg
    
    Args:
        legs: List of option legs with keys:
            - option_type: 'PUT' or 'CALL'
            - strike: Strike price
            - side: 'BUY' or 'SELL'
            - quantity: Number of contracts (can be negative)
            - entry_price: Optional premium paid/received
    
    Returns:
        VerticalSpreadResult with detected strategy or None if not a vertical spread
    """
    if len(legs) != 2:
        return None
    
    leg1, leg2 = legs[0], legs[1]
    
    # Validate required fields
    required_fields = ['option_type', 'strike', 'side', 'quantity']
    for leg in legs:
        if not all(field in leg for field in required_fields):
            logger.warning(f"Missing required fields in leg: {leg}")
            return None
    
    # Must be same option type
    if leg1['option_type'] != leg2['option_type']:
        return None
    
    option_type = leg1['option_type']
    
    # Check expiration if provided (different expirations should lower confidence)
    expiration_mismatch = False
    if 'expiration' in leg1 and 'expiration' in leg2:
        if leg1['expiration'] and leg2['expiration']:
            if leg1['expiration'] != leg2['expiration']:
                expiration_mismatch = True
                logger.debug(f"Expiration mismatch: {leg1['expiration']} vs {leg2['expiration']}")
    
    # Must have different strikes
    if abs(leg1['strike'] - leg2['strike']) < 0.01:
        return None
    
    # Must have matched quantities
    qty1 = abs(leg1['quantity'])
    qty2 = abs(leg2['quantity'])
    if abs(qty1 - qty2) > 0.01:
        logger.debug(f"Quantity mismatch: {qty1} vs {qty2}")
        return None
    
    # Must have one BUY and one SELL
    if leg1['side'] == leg2['side']:
        return None
    
    # Determine which leg is long (BUY) and which is short (SELL)
    long_leg = leg1 if leg1['side'] == 'BUY' else leg2
    short_leg = leg2 if leg1['side'] == 'BUY' else leg1
    
    # Calculate net debit/credit if entry prices available
    net_debit_credit = None
    if 'entry_price' in long_leg and 'entry_price' in short_leg:
        if long_leg['entry_price'] is not None and short_leg['entry_price'] is not None:
            # BUY leg: we pay the premium (positive cost)
            # SELL leg: we receive the premium (negative cost, i.e., credit)
            long_cost = long_leg['entry_price'] * abs(long_leg['quantity'])
            short_credit = short_leg['entry_price'] * abs(short_leg['quantity'])
            net_debit_credit = long_cost - short_credit
    
    is_debit = net_debit_credit is not None and net_debit_credit > 0
    is_credit = net_debit_credit is not None and net_debit_credit < 0
    
    # Classify based on option type and strike structure
    strategy_type = None
    
    if option_type == 'PUT':
        if long_leg['strike'] > short_leg['strike']:
            # Long higher strike put, short lower strike put = Bear Put Spread (debit)
            strategy_type = 'Bear Put Spread'
            if expiration_mismatch:
                confidence = 0.70
            elif net_debit_credit is None:
                confidence = 0.90
            elif is_debit:
                confidence = 0.95
            else:
                # Credit on a bear put spread structure is unusual
                confidence = 0.80
                logger.warning(
                    f"Bear Put Spread structure but premium shows credit ({net_debit_credit:.2f})"
                )
        else:
            # Long lower strike put, short higher strike put = Bull Put Spread (credit)
            strategy_type = 'Bull Put Spread'
            if expiration_mismatch:
                confidence = 0.70
            elif net_debit_credit is None:
                confidence = 0.90
            elif is_credit:
                confidence = 0.95
            else:
                # Debit on a bull put spread structure is unusual
                confidence = 0.80
                logger.warning(
                    f"Bull Put Spread structure but premium shows debit ({net_debit_credit:.2f})"
                )
    else:  # CALL
        if long_leg['strike'] < short_leg['strike']:
            # Long lower strike call, short higher strike call = Bull Call Spread (debit)
            strategy_type = 'Bull Call Spread'
            if expiration_mismatch:
                confidence = 0.70
            elif net_debit_credit is None:
                confidence = 0.90
            elif is_debit:
                confidence = 0.95
            else:
                # Credit on a bull call spread structure is unusual
                confidence = 0.80
                logger.warning(
                    f"Bull Call Spread structure but premium shows credit ({net_debit_credit:.2f})"
                )
        else:
            # Long higher strike call, short lower strike call = Bear Call Spread (credit)
            strategy_type = 'Bear Call Spread'
            if expiration_mismatch:
                confidence = 0.70
            elif net_debit_credit is None:
                confidence = 0.90
            elif is_credit:
                confidence = 0.95
            else:
                # Debit on a bear call spread structure is unusual
                confidence = 0.80
                logger.warning(
                    f"Bear Call Spread structure but premium shows debit ({net_debit_credit:.2f})"
                )
    
    strikes = tuple(sorted([leg1['strike'], leg2['strike']]))
    notes = f"{strategy_type}: Long {long_leg['strike']}{option_type[0].lower()} / Short {short_leg['strike']}{option_type[0].lower()}"
    if net_debit_credit is not None:
        notes += f" ({'debit' if is_debit else 'credit'})"
    
    return VerticalSpreadResult(
        strategy_type=strategy_type,
        confidence=confidence,
        strikes=strikes,
        net_debit_credit=net_debit_credit,
        long_strike=long_leg['strike'],
        short_strike=short_leg['strike'],
        option_type=option_type,
        notes=notes
    )


def calculate_vertical_spread_metrics(result: VerticalSpreadResult) -> Dict:
    """
    Calculate additional metrics for a vertical spread.
    
    Args:
        result: VerticalSpreadResult from detect_vertical_spread
    
    Returns:
        Dictionary with calculated metrics:
        - max_profit: Maximum profit potential
        - max_loss: Maximum loss potential
        - risk_reward_ratio: Risk/reward ratio
    """
    width = abs(result.long_strike - result.short_strike)
    
    metrics = {
        'width': width,
        'max_profit': None,
        'max_loss': None,
        'risk_reward_ratio': None
    }
    
    if result.net_debit_credit is not None:
        # Debit: bear put / bull call. Credit: bull put / bear call.
        debit_spreads = frozenset({'Bear Put Spread', 'Bull Call Spread'})
        if result.strategy_type in debit_spreads:
            metrics['max_loss'] = abs(result.net_debit_credit)
            metrics['max_profit'] = width - abs(result.net_debit_credit)
        else:
            metrics['max_profit'] = abs(result.net_debit_credit)
            metrics['max_loss'] = width - abs(result.net_debit_credit)
        
        if metrics['max_loss'] and metrics['max_loss'] > 0:
            metrics['risk_reward_ratio'] = metrics['max_profit'] / metrics['max_loss']
    
    return metrics
