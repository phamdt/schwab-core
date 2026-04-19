"""
Utility functions for data transformers.
"""

from typing import Any, Dict, List, Optional


def resolve_field_priority(
    data: Dict[str, Any],
    field_priority_list: List[str],
    default: Any = None
) -> Any:
    """
    Resolve a field value by trying each field in priority order.
    
    Returns the first non-None value found, or the default if none found.
    
    Args:
        data: Dictionary to search for fields
        field_priority_list: List of field names in priority order
        default: Default value to return if no field found
        
    Returns:
        First non-None value found, or default
        
    Example:
        >>> data = {'lastPrice': 10.5, 'currentPrice': None}
        >>> resolve_field_priority(data, ['marketPrice', 'lastPrice', 'currentPrice'])
        10.5
    """
    for field in field_priority_list:
        if field in data and data[field] is not None:
            return data[field]
    return default


def resolve_nested_field_priority(
    data: Dict[str, Any],
    field_paths: List[str],
    default: Any = None
) -> Any:
    """
    Resolve a nested field value by trying each path in priority order.
    
    Supports dot notation for nested fields (e.g., 'instrument.symbol').
    
    Args:
        data: Dictionary to search for nested fields
        field_paths: List of field paths in priority order (supports 'parent.child' notation)
        default: Default value to return if no field found
        
    Returns:
        First non-None value found, or default
        
    Example:
        >>> data = {'instrument': {'symbol': 'AAPL'}, 'symbol': None}
        >>> resolve_nested_field_priority(data, ['instrument.symbol', 'symbol'])
        'AAPL'
    """
    for path in field_paths:
        parts = path.split('.')
        current = data
        
        try:
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    current = None
                    break
            
            if current is not None:
                return current
        except (TypeError, KeyError):
            continue
    
    return default
