"""
Position data transformers for Schwab API responses.
"""

from typing import Any, Dict, Optional
import logging

from .utils import resolve_field_priority, resolve_nested_field_priority

logger = logging.getLogger(__name__)


def normalize_quantity(position: Dict[str, Any]) -> float:
    """
    Extract quantity from a position, handling longQuantity/shortQuantity fields.
    
    Schwab API provides both longQuantity and shortQuantity. This function:
    - Returns positive value for long positions (longQuantity > 0)
    - Returns negative value for short positions (shortQuantity > 0)
    - Checks multiple locations: direct fields, nested in instrument
    
    Args:
        position: Position data from Schwab API
        
    Returns:
        Quantity as float (positive for long, negative for short)
    """
    # Check direct longQuantity/shortQuantity first (most reliable)
    if 'longQuantity' in position or 'shortQuantity' in position:
        long_qty = position.get('longQuantity', 0) or 0
        short_qty = position.get('shortQuantity', 0) or 0
        if long_qty != 0:
            return float(long_qty)
        elif short_qty != 0:
            return float(-short_qty)
    
    # Check combined 'quantity' field
    if 'quantity' in position:
        return float(position.get('quantity', 0) or 0)
    
    # Check nested in instrument
    instrument = position.get('instrument', {})
    if isinstance(instrument, dict):
        if 'longQuantity' in instrument or 'shortQuantity' in instrument:
            long_qty = instrument.get('longQuantity', 0) or 0
            short_qty = instrument.get('shortQuantity', 0) or 0
            if long_qty != 0:
                return float(long_qty)
            elif short_qty != 0:
                return float(-short_qty)
        
        if 'quantity' in instrument:
            return float(instrument.get('quantity', 0) or 0)
    
    return 0.0


def extract_symbol(position: Dict[str, Any]) -> Optional[str]:
    """
    Extract symbol from a position, checking multiple locations.
    
    Priority order:
    1. instrument.symbol
    2. position.symbol
    3. For options: parse from description
    
    Args:
        position: Position data from Schwab API
        
    Returns:
        Symbol string or None if not found
    """
    instrument = position.get('instrument', {})
    
    # Check instrument.symbol first
    if isinstance(instrument, dict) and instrument.get('symbol'):
        return instrument['symbol']
    
    # Check position.symbol
    if position.get('symbol'):
        return position['symbol']
    
    # For options, try parsing description
    if isinstance(instrument, dict) and instrument.get('assetType') == 'OPTION':
        description = instrument.get('description', '')
        if description:
            # Description format is typically "SYMBOL MM/DD/YY ..." 
            parts = description.split()
            if parts:
                return parts[0]
    
    return None


def extract_entry_price(position: Dict[str, Any], quantity: float) -> float:
    """
    Extract entry price from a position with field priority.
    
    Priority order:
    1. averagePrice
    2. costBasis (if quantity available, calculate per-share)
    3. price
    4. purchasePrice
    5. averageCost
    
    Args:
        position: Position data from Schwab API
        quantity: Position quantity (for cost basis calculation)
        
    Returns:
        Entry price as float (defaults to 0.0 if not found)
    """
    # Try direct price fields first
    entry_price = resolve_field_priority(
        position,
        ['averagePrice', 'price', 'purchasePrice', 'averageCost'],
        None
    )
    
    if entry_price is not None:
        return float(entry_price)
    
    # Try calculating from cost basis
    if 'costBasis' in position and quantity != 0:
        cost_basis = position['costBasis']
        if cost_basis is not None:
            return float(cost_basis) / abs(quantity)
    
    return 0.0


def extract_current_price(
    position: Dict[str, Any],
    quantity: float,
    asset_type: str,
    entry_price: float
) -> float:
    """
    Extract current price from a position with field priority and calculation fallbacks.
    
    Priority order:
    1. Direct price fields: marketPrice, lastPrice, currentPrice
    2. Calculate from marketValue (if quantity available)
       - For options: marketValue / (quantity * 100)
       - For equities: marketValue / quantity
    3. Fall back to entry_price
    
    Args:
        position: Position data from Schwab API
        quantity: Position quantity
        asset_type: Asset type string ('OPTION', 'EQUITY', etc.)
        entry_price: Entry price (used as fallback)
        
    Returns:
        Current price as float
    """
    # Try direct price fields first
    current_price = resolve_field_priority(
        position,
        ['marketPrice', 'lastPrice', 'currentPrice'],
        None
    )
    
    # Schwab may return negative prices for short positions, use absolute value
    if current_price is not None:
        return abs(float(current_price))
    
    # Try calculating from market value
    market_value = resolve_field_priority(
        position,
        ['marketValue', 'currentValue', 'currentValueUSD'],
        None
    )
    
    if market_value is not None and quantity != 0:
        abs_market_value = abs(float(market_value))
        abs_quantity = abs(quantity)
        
        if asset_type == 'OPTION':
            # Options: marketValue = current_price * quantity * 100
            return abs_market_value / (abs_quantity * 100)
        else:
            # Equities: marketValue = current_price * quantity
            return abs_market_value / abs_quantity
    
    # Fall back to entry price
    return float(entry_price)


def calculate_profit(
    current_price: float,
    entry_price: float,
    quantity: float
) -> float:
    """
    Calculate profit/loss for a position.
    
    Formula: (current_price - entry_price) * quantity
    
    Args:
        current_price: Current market price
        entry_price: Entry price
        quantity: Position quantity
        
    Returns:
        Profit/loss as float
    """
    return (current_price - entry_price) * quantity


def calculate_market_value(
    current_price: float,
    quantity: float,
    asset_type: str
) -> float:
    """
    Calculate market value for a position.
    
    For options: market_value = current_price * quantity * 100
    For equities: market_value = current_price * quantity
    
    Note: Preserves sign (negative for short/credit, positive for long/debit)
    
    Args:
        current_price: Current market price
        quantity: Position quantity (can be negative for short positions)
        asset_type: Asset type string ('OPTION', 'EQUITY', etc.)
        
    Returns:
        Market value as float
    """
    if asset_type == 'OPTION':
        return current_price * quantity * 100
    else:
        return current_price * quantity


def transform_position_to_trade(position: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a Schwab API position into a standardized Trade dict.
    
    Extracts and normalizes:
    - Symbol (from multiple locations)
    - Quantity (handling long/short positions)
    - Prices (entry and current, with fallbacks)
    - P&L calculation
    - Market value
    - Asset type and metadata
    
    Args:
        position: Position object from Schwab API
        
    Returns:
        Standardized Trade dictionary with keys:
        - symbol: str
        - quantity: float
        - entry_price: float
        - current_price: float
        - profit: float
        - market_value: float
        - asset_type: str
        - description: str
        - underlying_symbol: str (for options)
        
    Raises:
        ValueError: If symbol cannot be extracted
    """
    # Extract symbol
    symbol = extract_symbol(position)
    if not symbol:
        raise ValueError(f"Could not extract symbol from position: {position}")
    
    # Extract quantity
    quantity = normalize_quantity(position)
    
    # Determine asset type
    instrument = position.get('instrument', {})
    asset_type = 'UNKNOWN'
    if isinstance(instrument, dict):
        asset_type = instrument.get('assetType', position.get('assetType', 'UNKNOWN'))
    else:
        asset_type = position.get('assetType', 'UNKNOWN')
    
    # Extract prices
    entry_price = extract_entry_price(position, quantity)
    current_price = extract_current_price(position, quantity, asset_type, entry_price)
    
    # Calculate derived values
    profit = calculate_profit(current_price, entry_price, quantity)
    
    # Get or calculate market value
    market_value = resolve_field_priority(
        position,
        ['marketValue', 'currentValue', 'currentValueUSD'],
        None
    )
    
    if market_value is None:
        market_value = calculate_market_value(current_price, quantity, asset_type)
    else:
        market_value = float(market_value)
    
    # Extract additional metadata
    description = ""
    underlying_symbol = None
    if isinstance(instrument, dict):
        description = instrument.get('description', position.get('description', ''))
        if asset_type == 'OPTION' and 'underlyingSymbol' in instrument:
            underlying_symbol = instrument['underlyingSymbol']
    
    # Extract performance metrics
    total_pnl = resolve_field_priority(
        position,
        ['totalPnL', 'unrealizedPnL'],
        profit
    )
    
    day_pnl = resolve_field_priority(
        position,
        ['dayPnL', 'dailyPnL'],
        0.0
    )
    
    percent_of_account = position.get('percentOfAccount', 0.0)
    
    # Build standardized trade dict
    trade = {
        'symbol': symbol,
        'quantity': quantity,
        'entry_price': entry_price,
        'current_price': current_price,
        'profit': profit,
        'market_value': market_value,
        'asset_type': asset_type,
        'description': description,
        'total_pnl': float(total_pnl) if total_pnl is not None else None,
        'day_pnl': float(day_pnl) if day_pnl is not None else None,
        'percent_of_account': float(percent_of_account) if percent_of_account else None,
    }
    
    # Add optional fields
    if underlying_symbol:
        trade['underlying_symbol'] = underlying_symbol
    
    # Preserve strategy info if present
    if 'strategy_group_id' in position:
        trade['strategy_group_id'] = position['strategy_group_id']
    if 'strategy_type' in position:
        trade['strategy_type'] = position['strategy_type']
    
    return trade
