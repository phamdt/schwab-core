"""
Account data transformers for Schwab API responses.
"""

from typing import Any, Dict, List, Optional
import logging

from .utils import resolve_field_priority

logger = logging.getLogger(__name__)


def parse_account_response(schwab_response: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse Schwab API account response into standardized format.
    
    The Schwab API returns accounts wrapped in 'securitiesAccount' objects.
    This function unwraps and standardizes the format.
    
    Account ID extraction priority:
    1. accountNumber
    2. accountId
    3. id
    4. number
    
    Balance extraction:
    - currentBalances: cashBalance, availableFunds, buyingPower, liquidationValue
    - initialBalances: availableFundsNonMarginableTrade
    
    Args:
        schwab_response: List of account objects from Schwab API
        
    Returns:
        List of standardized account dictionaries with keys:
        - account_id: str
        - account_type: str
        - balances: Dict with:
          - cash_balance: float
          - available_funds: float
          - buying_power: float
          - total_balance: float
          - available_funds_non_marginable: float
          
    Example:
        >>> response = [{
        ...     'securitiesAccount': {
        ...         'accountNumber': '12345',
        ...         'type': 'MARGIN',
        ...         'currentBalances': {'cashBalance': 10000},
        ...         'initialBalances': {'availableFundsNonMarginableTrade': 5000}
        ...     }
        ... }]
        >>> parse_account_response(response)
        [{'account_id': '12345', 'account_type': 'MARGIN', 'balances': {...}}]
    """
    if not isinstance(schwab_response, list):
        logger.warning(f"Expected list response, got {type(schwab_response)}")
        return []
    
    accounts = []
    
    for account_data in schwab_response:
        try:
            # Try to unwrap securitiesAccount
            if 'securitiesAccount' in account_data:
                securities_account = account_data['securitiesAccount']
                
                # Extract account ID with priority
                account_id = securities_account.get('accountNumber')
                if not account_id:
                    account_id = resolve_field_priority(
                        securities_account,
                        ['accountId', 'id', 'number'],
                        None
                    )
                
                if not account_id:
                    logger.warning(f"Could not extract account ID from: {securities_account}")
                    continue
                
                # Extract account type
                account_type = securities_account.get('type', 'Securities')
                
                # Extract balances
                current_balances = securities_account.get('currentBalances', {})
                initial_balances = securities_account.get('initialBalances', {})
                
                balances = {
                    'cash_balance': current_balances.get('cashBalance', 0.0),
                    'available_funds': current_balances.get('availableFunds', 0.0),
                    'buying_power': current_balances.get('buyingPower', 0.0),
                    'total_balance': current_balances.get('liquidationValue', 0.0),
                    'available_funds_non_marginable': initial_balances.get('availableFundsNonMarginableTrade', 0.0),
                }
                
                accounts.append({
                    'account_id': str(account_id),
                    'account_type': account_type,
                    'balances': balances,
                })
                
            else:
                # Handle case where securitiesAccount is not present
                account_id = resolve_field_priority(
                    account_data,
                    ['accountNumber', 'accountId', 'id', 'number'],
                    None
                )
                
                if not account_id:
                    logger.warning(f"Could not extract account ID from: {account_data}")
                    continue
                
                account_type = account_data.get('type', 'Unknown')
                
                # Try to extract balances if available
                current_balances = account_data.get('currentBalances', {})
                initial_balances = account_data.get('initialBalances', {})
                
                balances = {
                    'cash_balance': current_balances.get('cashBalance', 0.0) if current_balances else 0.0,
                    'available_funds': current_balances.get('availableFunds', 0.0) if current_balances else 0.0,
                    'buying_power': current_balances.get('buyingPower', 0.0) if current_balances else 0.0,
                    'total_balance': current_balances.get('liquidationValue', 0.0) if current_balances else 0.0,
                    'available_funds_non_marginable': initial_balances.get('availableFundsNonMarginableTrade', 0.0) if initial_balances else 0.0,
                }
                
                accounts.append({
                    'account_id': str(account_id),
                    'account_type': account_type,
                    'balances': balances,
                })
                
        except Exception as e:
            logger.error(f"Error parsing account: {e}", exc_info=True)
            logger.error(f"Problem account data: {account_data}")
            continue
    
    logger.info(f"Parsed {len(accounts)} accounts from Schwab response")
    return accounts


def extract_account_id(account_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract account ID from account data with field priority.
    
    Priority order:
    1. accountNumber
    2. accountId
    3. id
    4. number
    
    Args:
        account_data: Account object or securitiesAccount object
        
    Returns:
        Account ID string or None if not found
    """
    return resolve_field_priority(
        account_data,
        ['accountNumber', 'accountId', 'id', 'number'],
        None
    )


def extract_balances(
    current_balances: Optional[Dict[str, Any]] = None,
    initial_balances: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Extract and standardize balance information.
    
    Args:
        current_balances: Current balances dict from Schwab API
        initial_balances: Initial balances dict from Schwab API
        
    Returns:
        Standardized balances dictionary
    """
    current = current_balances or {}
    initial = initial_balances or {}
    
    return {
        'cash_balance': float(current.get('cashBalance', 0.0)),
        'available_funds': float(current.get('availableFunds', 0.0)),
        'buying_power': float(current.get('buyingPower', 0.0)),
        'total_balance': float(current.get('liquidationValue', 0.0)),
        'available_funds_non_marginable': float(initial.get('availableFundsNonMarginableTrade', 0.0)),
    }
