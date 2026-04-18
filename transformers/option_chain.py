"""
Option chain data transformers for Schwab API responses.
"""

from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def extract_option_chain_strikes(
    chain_data: Dict[str, Any],
    expiration: str
) -> List[Dict[str, Any]]:
    """
    Extract option chain strikes for a specific expiration.
    
    Schwab option chain structure:
    - callExpDateMap: {expiration: {strike: [contract_data]}}
    - putExpDateMap: {expiration: {strike: [contract_data]}}
    
    Expiration format: "YYYY-MM-DD:DTE" (e.g., "2025-01-17:0")
    Strike format: String representation of float (e.g., "100.0")
    
    Args:
        chain_data: Raw option chain response from Schwab API
        expiration: Expiration string key (e.g., '2025-01-17:0')
        
    Returns:
        List of dictionaries with:
        - strike: float
        - call_contracts: List[Dict] (contracts at this strike)
        - put_contracts: List[Dict] (contracts at this strike)
        
    Example:
        >>> chain = {
        ...     'callExpDateMap': {
        ...         '2025-01-17:0': {
        ...             '100.0': [{'symbol': 'AAPL250117C00100000'}]
        ...         }
        ...     },
        ...     'putExpDateMap': {
        ...         '2025-01-17:0': {
        ...             '100.0': [{'symbol': 'AAPL250117P00100000'}]
        ...         }
        ...     }
        ... }
        >>> extract_option_chain_strikes(chain, '2025-01-17:0')
        [{'strike': 100.0, 'call_contracts': [...], 'put_contracts': [...]}]
    """
    call_exp_map = chain_data.get('callExpDateMap', {})
    put_exp_map = chain_data.get('putExpDateMap', {})
    
    # Collect all unique strikes
    strikes_set = set()
    
    # Get strikes from calls
    if expiration in call_exp_map:
        for strike_str in call_exp_map[expiration].keys():
            try:
                strike_val = float(strike_str)
                if strike_val > 0:
                    strikes_set.add(strike_val)
            except (ValueError, TypeError):
                logger.debug(f"Ignoring non-numeric call strike '{strike_str}' for {expiration}")
    
    # Get strikes from puts
    if expiration in put_exp_map:
        for strike_str in put_exp_map[expiration].keys():
            try:
                strike_val = float(strike_str)
                if strike_val > 0:
                    strikes_set.add(strike_val)
            except (ValueError, TypeError):
                logger.debug(f"Ignoring non-numeric put strike '{strike_str}' for {expiration}")
    
    # Sort strikes
    strikes = sorted(strikes_set)
    
    # Build result list with contracts
    result = []
    for strike in strikes:
        strike_str = str(strike)
        
        # Get call contracts at this strike
        call_contracts = []
        if expiration in call_exp_map and strike_str in call_exp_map[expiration]:
            call_contracts = call_exp_map[expiration][strike_str]
            # Ensure it's a list
            if not isinstance(call_contracts, list):
                call_contracts = [call_contracts]
        
        # Get put contracts at this strike
        put_contracts = []
        if expiration in put_exp_map and strike_str in put_exp_map[expiration]:
            put_contracts = put_exp_map[expiration][strike_str]
            # Ensure it's a list
            if not isinstance(put_contracts, list):
                put_contracts = [put_contracts]
        
        result.append({
            'strike': strike,
            'call_contracts': call_contracts,
            'put_contracts': put_contracts,
        })
    
    logger.info(f"Extracted {len(result)} strikes for expiration {expiration}")
    return result


def extract_expirations(chain_data: Dict[str, Any]) -> List[str]:
    """
    Extract all available expiration dates from option chain.
    
    Args:
        chain_data: Raw option chain response from Schwab API
        
    Returns:
        Sorted list of expiration strings (format: "YYYY-MM-DD:DTE")
    """
    expirations_set = set()
    
    # Get expirations from calls
    call_exp_map = chain_data.get('callExpDateMap', {})
    expirations_set.update(call_exp_map.keys())
    
    # Get expirations from puts
    put_exp_map = chain_data.get('putExpDateMap', {})
    expirations_set.update(put_exp_map.keys())
    
    # Sort chronologically (format allows lexicographic sorting)
    return sorted(expirations_set)


def parse_expiration_string(expiration: str) -> Dict[str, Any]:
    """
    Parse Schwab expiration string into components.
    
    Format: "YYYY-MM-DD:DTE"
    
    Args:
        expiration: Expiration string (e.g., "2025-01-17:0")
        
    Returns:
        Dictionary with:
        - date: str (YYYY-MM-DD)
        - dte: int (days to expiration)
        
    Example:
        >>> parse_expiration_string("2025-01-17:0")
        {'date': '2025-01-17', 'dte': 0}
    """
    try:
        date_part, dte_part = expiration.split(':')
        return {
            'date': date_part,
            'dte': int(dte_part),
        }
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid expiration format '{expiration}': {e}")
        return {
            'date': expiration,
            'dte': None,
        }


def get_strikes_list(chain_data: Dict[str, Any], expiration: str) -> List[float]:
    """
    Get sorted list of strike prices for an expiration.
    
    This is a convenience function that returns just the strike prices
    without the contract data.
    
    Args:
        chain_data: Raw option chain response from Schwab API
        expiration: Expiration string key
        
    Returns:
        Sorted list of strike prices as floats
    """
    strikes_with_contracts = extract_option_chain_strikes(chain_data, expiration)
    return [item['strike'] for item in strikes_with_contracts]
