"""
Symbol parsing and normalization utilities.

Handles parsing option symbols from various formats into components:
- Underlying symbol
- Strike price
- Expiration date
- Option type (CALL/PUT)
"""

import re
from datetime import datetime, date
from typing import Dict, Optional, List, Any

# Index symbols that use special formatting
INDEX_SYMBOLS = ['SPX', 'SPXW', 'NDX', 'RUT', 'VIX', 'DJX']


class OptionSymbolParseError(Exception):
    """Exception raised when unable to parse option symbol."""
    pass


def normalize_symbol_for_schwab(symbol: str) -> str:
    """
    Normalize symbol for Schwab API format.
    
    Args:
        symbol: Option symbol in any format
        
    Returns:
        Normalized symbol string
    """
    # Remove spaces
    symbol = symbol.strip()
    
    # For index options, ensure proper spacing
    for index in INDEX_SYMBOLS:
        if symbol.startswith(index):
            # SPX format: SPXW  251113C06815000
            # Ensure double space after symbol
            return symbol
    
    return symbol


def parse_option_type(symbol: str) -> str:
    """
    Extract option type (CALL/PUT) from symbol.
    
    Args:
        symbol: Option symbol
        
    Returns:
        'CALL' or 'PUT'
        
    Raises:
        OptionSymbolParseError: If option type cannot be determined
    """
    symbol_upper = symbol.upper()
    
    # Look for C or P indicator
    if 'C' in symbol_upper:
        # Find last C that's likely the option type
        for i in range(len(symbol_upper) - 1, -1, -1):
            if symbol_upper[i] == 'C':
                # Check if this is part of the option type (not underlying)
                # Usually followed by digits (strike)
                if i < len(symbol_upper) - 1 and symbol_upper[i + 1].isdigit():
                    return 'CALL'
    
    if 'P' in symbol_upper:
        # Find last P that's likely the option type
        for i in range(len(symbol_upper) - 1, -1, -1):
            if symbol_upper[i] == 'P':
                # Check if this is part of the option type (not underlying)
                if i < len(symbol_upper) - 1 and symbol_upper[i + 1].isdigit():
                    return 'PUT'
    
    raise OptionSymbolParseError(f"Cannot determine option type from symbol: {symbol}")


def parse_underlying_from_symbol(symbol: str) -> str:
    """
    Extract underlying ticker from option symbol.
    
    Args:
        symbol: Option symbol
        
    Returns:
        Underlying ticker symbol
        
    Raises:
        OptionSymbolParseError: If underlying cannot be extracted
    """
    # Check for index symbols first
    for index in INDEX_SYMBOLS:
        if symbol.upper().startswith(index):
            return index
    
    # Standard format: AAPL_012025C150 or AAPL 012025C150
    # Extract everything before date/strike
    match = re.match(r'^([A-Z]+)[_\s]', symbol.upper())
    if match:
        return match.group(1)
    
    # Try to find where the date pattern starts
    match = re.match(r'^([A-Z]+)(?=\d{6}[CP])', symbol.upper())
    if match:
        return match.group(1)
    
    raise OptionSymbolParseError(f"Cannot extract underlying from symbol: {symbol}")


def parse_expiration_from_symbol(symbol: str) -> date:
    """
    Extract expiration date from option symbol.
    
    Args:
        symbol: Option symbol
        
    Returns:
        Expiration date
        
    Raises:
        OptionSymbolParseError: If expiration cannot be parsed
    """
    # Look for 6-digit date pattern (MMDDYY or YYMMDD)
    # Common formats:
    # - AAPL_012025C150 -> 01/20/25
    # - SPX_010125C6840 -> 01/01/25
    # - SPXW  251113C06815000 -> 11/13/25
    
    # Try MMDDYY format (most common)
    match = re.search(r'(\d{2})(\d{2})(\d{2})[CP]', symbol)
    if match:
        month, day, year = match.groups()
        
        # Determine if it's MMDDYY or YYMMDD
        month_int = int(month)
        day_int = int(day)
        year_int = int(year)
        
        # If month > 12, it's likely YYMMDD format
        if month_int > 12:
            # YYMMDD format
            year_int = month_int + 2000
            month_int = day_int
            day_int = int(year)
        else:
            # MMDDYY format
            year_int = year_int + 2000
        
        try:
            return date(year_int, month_int, day_int)
        except ValueError as e:
            raise OptionSymbolParseError(f"Invalid date in symbol {symbol}: {e}")
    
    raise OptionSymbolParseError(f"Cannot parse expiration from symbol: {symbol}")


def parse_strike_from_symbol(symbol: str) -> float:
    """
    Extract strike price from option symbol.
    
    Args:
        symbol: Option symbol
        
    Returns:
        Strike price as float
        
    Raises:
        OptionSymbolParseError: If strike cannot be parsed
    """
    # Strike comes after the option type indicator (C or P)
    # Format examples:
    # - AAPL_012025C150 -> 150.0
    # - SPX_010125C6840 -> 6840.0
    # - SPXW  251113C06815000 -> 6815.0 (last 8 digits, divide by 1000)
    
    # Find the option type
    match = re.search(r'[CP](\d+)(?:\D|$)', symbol)
    if match:
        strike_str = match.group(1)
        
        # For index options with 8-digit strikes, divide by 1000
        if len(strike_str) >= 8:
            return float(strike_str) / 1000.0
        
        return float(strike_str)
    
    raise OptionSymbolParseError(f"Cannot parse strike from symbol: {symbol}")


def parse_option_symbol(symbol: str) -> Dict[str, Any]:
    """
    Parse option symbol into components.
    
    Args:
        symbol: Option symbol in any supported format
        
    Returns:
        Dictionary with:
        - underlying: Underlying ticker
        - strike: Strike price
        - expiration: Expiration date
        - option_type: 'CALL' or 'PUT'
        
    Raises:
        OptionSymbolParseError: If symbol cannot be parsed
        
    Examples:
        >>> parse_option_symbol("AAPL_012025C150")
        {
            'underlying': 'AAPL',
            'strike': 150.0,
            'expiration': date(2025, 1, 20),
            'option_type': 'CALL'
        }
        
        >>> parse_option_symbol("SPXW  251113C06815000")
        {
            'underlying': 'SPXW',
            'strike': 6815.0,
            'expiration': date(2025, 11, 13),
            'option_type': 'CALL'
        }
    """
    if not symbol:
        raise OptionSymbolParseError("Empty symbol")
    
    try:
        underlying = parse_underlying_from_symbol(symbol)
        strike = parse_strike_from_symbol(symbol)
        expiration = parse_expiration_from_symbol(symbol)
        option_type = parse_option_type(symbol)
        
        return {
            'underlying': underlying,
            'strike': strike,
            'expiration': expiration,
            'option_type': option_type
        }
    except Exception as e:
        if isinstance(e, OptionSymbolParseError):
            raise
        raise OptionSymbolParseError(f"Error parsing symbol {symbol}: {str(e)}")
