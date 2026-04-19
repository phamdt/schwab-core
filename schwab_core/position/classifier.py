"""Position classification utilities for Schwab trading data.

This module consolidates position classification logic from multiple sources:
- Quantity extraction and normalization
- Credit/debit spread classification
- Position direction (long/short) detection
- Position effect (opening/closing) extraction
"""

from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


def classify_position_direction(position: Dict[str, Any]) -> str:
    """Classify position direction as LONG or SHORT.
    
    Determines position direction by checking longQuantity and shortQuantity fields.
    Positive quantity = LONG, negative quantity = SHORT.
    
    Args:
        position: Position dict with longQuantity/shortQuantity fields
        
    Returns:
        "LONG" or "SHORT"
        
    Examples:
        >>> classify_position_direction({"longQuantity": 10})
        "LONG"
        >>> classify_position_direction({"shortQuantity": -5})
        "SHORT"
    """
    long_qty = position.get('longQuantity', 0) or 0
    short_qty = position.get('shortQuantity', 0) or 0
    
    # Check longQuantity first (standard Schwab API field)
    if long_qty != 0:
        return "LONG"
    elif short_qty != 0:
        return "SHORT"
    
    # Fallback: check combined quantity field
    quantity = position.get('quantity', 0) or 0
    if quantity >= 0:
        return "LONG"
    else:
        return "SHORT"


def normalize_quantity(position: Dict[str, Any]) -> float:
    """Extract and normalize quantity from position dict.
    
    Priority order:
    1. longQuantity/shortQuantity (Schwab standard)
    2. quantity field
    3. nested instrument.longQuantity/shortQuantity
    4. nested instrument.quantity
    
    Returns signed quantity: positive = long, negative = short.
    Handles missing fields gracefully by defaulting to 0.
    
    Args:
        position: Position dict with quantity information
        
    Returns:
        Signed quantity (positive=long, negative=short)
        
    Examples:
        >>> normalize_quantity({"longQuantity": 10})
        10.0
        >>> normalize_quantity({"shortQuantity": 5})
        -5.0
        >>> normalize_quantity({"quantity": 3})
        3.0
    """
    def _get_quantity(data: Dict[str, Any]) -> Optional[float]:
        """Helper to get quantity from longQuantity/shortQuantity."""
        if 'longQuantity' in data or 'shortQuantity' in data:
            long_qty = data.get('longQuantity', 0) or 0
            short_qty = data.get('shortQuantity', 0) or 0
            if long_qty != 0:
                return float(long_qty)
            elif short_qty != 0:
                return -float(short_qty)
            else:
                return 0.0
        return None
    
    # Priority 1: Check longQuantity and shortQuantity (Schwab API standard)
    quantity = _get_quantity(position)
    if quantity is not None:
        return quantity
    
    # Priority 2: Check combined quantity field
    if 'quantity' in position:
        return float(position.get('quantity', 0) or 0)
    
    # Priority 3 & 4: Check nested instrument object
    if 'instrument' in position:
        # First try nested longQuantity/shortQuantity
        nested_qty = _get_quantity(position['instrument'])
        if nested_qty is not None:
            return nested_qty
        
        # Then try nested quantity field
        if 'quantity' in position['instrument']:
            return float(position['instrument'].get('quantity', 0) or 0)
    
    # Default to 0 if quantity not found anywhere
    return 0.0


def classify_credit_debit(legs: List[Dict[str, Any]]) -> Tuple[str, float]:
    """Classify spread as credit or debit based on premiums.
    
    Calculates net debit/credit by summing:
    - Long leg costs (premiums paid)
    - Short leg credits (premiums received)
    
    Net calculation: sum(long costs) - sum(short credits)
    - Positive result = DEBIT (paid more than received)
    - Negative result = CREDIT (received more than paid)
    
    Args:
        legs: List of leg dicts with entry_price and quantity fields
        
    Returns:
        Tuple of (classification, amount) where:
        - classification is "CREDIT" or "DEBIT"
        - amount is absolute value of net premium
        Returns ("UNKNOWN", 0.0) if no premium data available
        
    Examples:
        >>> legs = [
        ...     {"entry_price": 2.50, "quantity": 1},
        ...     {"entry_price": 1.50, "quantity": -1}
        ... ]
        >>> classify_credit_debit(legs)
        ("DEBIT", 1.0)
    """
    long_cost = 0.0
    short_credit = 0.0
    has_premium_data = False
    
    for leg in legs:
        entry_price = leg.get('entry_price')
        quantity = leg.get('quantity', 0)
        
        if entry_price is None:
            continue
            
        has_premium_data = True
        
        # For BUY leg (positive quantity): we pay the premium (cost)
        # For SELL leg (negative quantity): we receive the premium (credit)
        if quantity > 0:
            long_cost += entry_price * abs(quantity)
        elif quantity < 0:
            short_credit += entry_price * abs(quantity)
    
    # If no premium data available, return unknown
    if not has_premium_data:
        logger.warning("No premium data available in legs for credit/debit classification")
        return ("UNKNOWN", 0.0)
    
    # Calculate net debit/credit
    # Positive = net debit (paid more than received)
    # Negative = net credit (received more than paid)
    net_debit_credit = long_cost - short_credit
    
    if net_debit_credit > 0:
        return ("DEBIT", abs(net_debit_credit))
    elif net_debit_credit < 0:
        return ("CREDIT", abs(net_debit_credit))
    else:
        # Edge case: net is exactly 0
        return ("NEUTRAL", 0.0)


def extract_position_effect(transaction: Dict[str, Any]) -> str:
    """Extract position effect from transaction data.
    
    Checks positionEffect field in transferItems to determine if
    transaction is opening or closing a position.
    
    Args:
        transaction: Transaction dict with transferItems array
        
    Returns:
        "OPENING", "CLOSING", or "UNKNOWN" if not determinable
        
    Examples:
        >>> extract_position_effect({
        ...     "transferItems": [{"positionEffect": "OPENING"}]
        ... })
        "OPENING"
    """
    # Check transferItems array
    transfer_items = transaction.get('transferItems', [])
    if not transfer_items:
        logger.warning("No transferItems found in transaction")
        return "UNKNOWN"
    
    # Check first transfer item for positionEffect
    position_effect = transfer_items[0].get('positionEffect')
    
    if position_effect:
        # Normalize to uppercase
        effect = str(position_effect).upper()
        if effect in ("OPENING", "CLOSING"):
            return effect
        else:
            logger.warning(f"Unexpected positionEffect value: {position_effect}")
            return "UNKNOWN"
    
    logger.warning("No positionEffect field found in transferItems")
    return "UNKNOWN"


def is_credit_strategy(strategy_type: str, quantity: float, asset_type: str) -> bool:
    """Determine if a strategy is typically a credit strategy.
    
    Based on frontend logic from creditPositionAnalysis.ts.
    Credit strategies typically receive premium upfront.
    
    Args:
        strategy_type: Strategy name (e.g., "iron-butterfly", "short put spread")
        quantity: Position quantity (negative indicates short)
        asset_type: Asset type (e.g., "OPTION")
        
    Returns:
        True if strategy is typically a credit strategy
        
    Examples:
        >>> is_credit_strategy("iron-butterfly", -1, "OPTION")
        True
        >>> is_credit_strategy("long call spread", 1, "OPTION")
        False
    """
    is_short = quantity < 0
    strategy_lower = strategy_type.lower()
    
    # Known credit strategies
    credit_keywords = [
        'iron-butterfly',
        'iron-condor',
        'iron butterfly',
        'iron condor',
        'credit',
        'credit spread',
        'short call spread',
        'short put spread',
        'vertical spread'
    ]
    
    # Check if any credit keyword is in strategy name
    for keyword in credit_keywords:
        if keyword in strategy_lower:
            return True
    
    # Short option positions are typically credit strategies
    if is_short and asset_type == 'OPTION':
        return True
    
    return False
