"""
Iron Butterfly Detection Module

Detects iron butterfly options strategies.

An iron butterfly consists of:
- 4 legs with same expiration
- 2 short options at center strike (1 put, 1 call)
- 1 long put at lower wing strike
- 1 long call at higher wing strike
- Symmetric wings (equidistant from center)
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class IronButterflyResult:
    """Result from iron butterfly detection"""
    strategy_type: str = "Iron Butterfly"
    confidence: float = 0.0
    center_strike: float = 0.0
    wing_width: float = 0.0
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    net_credit: Optional[float] = None
    lower_wing: Optional[float] = None
    upper_wing: Optional[float] = None
    breakeven_low: Optional[float] = None
    breakeven_high: Optional[float] = None
    notes: str = ""


def detect_iron_butterfly(legs: List[Dict]) -> Optional[IronButterflyResult]:
    """
    Detect iron butterfly strategy from option legs.
    
    Rules:
    - Must have exactly 4 legs
    - Same expiration date (if provided)
    - 2 PUT legs (1 long lower, 1 short center)
    - 2 CALL legs (1 short center, 1 long higher)
    - Center strikes should match (shorts at same strike)
    - Wings should be symmetric (equidistant from center)
    
    Args:
        legs: List of option legs with keys:
            - option_type: 'PUT' or 'CALL'
            - strike: Strike price
            - side: 'BUY' or 'SELL'
            - quantity: Number of contracts
            - expiration: Optional expiration date
            - entry_price: Optional premium
    
    Returns:
        IronButterflyResult if detected, None otherwise
    """
    if len(legs) != 4:
        return None
    
    # Validate required fields
    required_fields = ['option_type', 'strike', 'side', 'quantity']
    for leg in legs:
        if not all(field in leg for field in required_fields):
            logger.warning(f"Missing required fields in leg: {leg}")
            return None
    
    # Check same expiration if provided
    expirations = [leg.get('expiration') for leg in legs if leg.get('expiration')]
    if expirations and len(set(expirations)) > 1:
        logger.debug(f"Different expirations: {set(expirations)}")
        return None
    
    # Separate by type
    puts = [l for l in legs if l['option_type'] == 'PUT']
    calls = [l for l in legs if l['option_type'] == 'CALL']
    
    # Must have 2 of each
    if len(puts) != 2 or len(calls) != 2:
        return None
    
    # Separate by side
    long_puts = [p for p in puts if p['side'] == 'BUY']
    short_puts = [p for p in puts if p['side'] == 'SELL']
    long_calls = [c for c in calls if c['side'] == 'BUY']
    short_calls = [c for c in calls if c['side'] == 'SELL']
    
    # Must have 1 of each
    if len(long_puts) != 1 or len(short_puts) != 1 or len(long_calls) != 1 or len(short_calls) != 1:
        return None
    
    long_put = long_puts[0]
    short_put = short_puts[0]
    long_call = long_calls[0]
    short_call = short_calls[0]
    
    # Check center strikes match (shorts should be at same strike)
    center_strike_tolerance = 0.01
    if abs(short_put['strike'] - short_call['strike']) > center_strike_tolerance:
        logger.debug(
            f"Center strikes don't match: {short_put['strike']} vs {short_call['strike']}"
        )
        return None
    
    center_strike = (short_put['strike'] + short_call['strike']) / 2
    
    # Check structure: long put < center < long call
    if not (long_put['strike'] < center_strike < long_call['strike']):
        logger.debug(
            f"Invalid structure: {long_put['strike']} (long put) < "
            f"{center_strike} (center) < {long_call['strike']} (long call)"
        )
        return None
    
    # Calculate wing widths
    lower_wing = center_strike - long_put['strike']
    upper_wing = long_call['strike'] - center_strike
    
    # Check symmetry (within 10% tolerance)
    symmetry_tolerance = 0.10
    wing_diff = abs(lower_wing - upper_wing)
    avg_wing = (lower_wing + upper_wing) / 2
    
    if avg_wing > 0 and wing_diff / avg_wing > symmetry_tolerance:
        logger.debug(
            f"Wings not symmetric: lower={lower_wing}, upper={upper_wing}, "
            f"diff={wing_diff}, avg={avg_wing}, ratio={wing_diff/avg_wing:.2%}"
        )
        # Not perfectly symmetric, but could still be an iron butterfly
        confidence = 0.80
    else:
        confidence = 0.95
    
    # Use average wing width
    wing_width = avg_wing
    
    # Calculate net credit if entry prices available
    net_credit = None
    if all('entry_price' in leg and leg['entry_price'] is not None for leg in legs):
        # Credits from short positions (positive)
        short_credits = (
            short_put['entry_price'] * abs(short_put['quantity']) +
            short_call['entry_price'] * abs(short_call['quantity'])
        )
        # Debits from long positions (positive cost)
        long_debits = (
            long_put['entry_price'] * abs(long_put['quantity']) +
            long_call['entry_price'] * abs(long_call['quantity'])
        )
        # Net credit = received - paid
        net_credit = short_credits - long_debits
        
        if net_credit < 0:
            logger.warning(f"Iron butterfly shows net debit ({net_credit:.2f}) - unusual")
            confidence = min(confidence, 0.75)
    
    # Calculate P&L metrics
    max_profit = net_credit if net_credit is not None else None
    max_loss = None
    breakeven_low = None
    breakeven_high = None
    
    if net_credit is not None:
        # Max loss = wing width - net credit
        max_loss = wing_width - net_credit
        
        # Breakevens: center strike +/- net credit
        breakeven_low = center_strike - net_credit
        breakeven_high = center_strike + net_credit
    
    notes = f"Center: {center_strike}, Wings: {lower_wing:.2f}/{upper_wing:.2f}"
    if net_credit is not None:
        notes += f", Credit: ${net_credit:.2f}"
    
    return IronButterflyResult(
        strategy_type="Iron Butterfly",
        confidence=confidence,
        center_strike=center_strike,
        wing_width=wing_width,
        max_profit=max_profit,
        max_loss=max_loss,
        net_credit=net_credit,
        lower_wing=long_put['strike'],
        upper_wing=long_call['strike'],
        breakeven_low=breakeven_low,
        breakeven_high=breakeven_high,
        notes=notes
    )


def validate_iron_butterfly_quantities(legs: List[Dict]) -> bool:
    """
    Validate that all legs have matching quantities.
    
    Args:
        legs: List of 4 option legs
    
    Returns:
        True if quantities match, False otherwise
    """
    if len(legs) != 4:
        return False
    
    quantities = [abs(leg['quantity']) for leg in legs]
    base_qty = quantities[0]
    
    # All quantities should match (within 0.01 tolerance)
    return all(abs(qty - base_qty) < 0.01 for qty in quantities)
