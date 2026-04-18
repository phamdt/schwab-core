"""
Greeks Calculator Module

Provides gamma exposure calculations and Greeks extraction utilities
for options trading analysis. Consolidates functionality from gamma
calculation services across the codebase.
"""
from typing import Dict, List, Optional, Any


def calculate_gamma_exposure(
    gamma: float,
    open_interest: int,
    contract_multiplier: int = 100
) -> float:
    """
    Calculate gamma exposure for an option contract.
    
    Gamma exposure represents the dollar amount of delta change per 1% move
    in the underlying. It's calculated as:
    
    Gamma Exposure = Gamma × Open Interest × Contract Multiplier
    
    Args:
        gamma: Gamma value for the contract (typically from Black-Scholes)
        open_interest: Number of open contracts
        contract_multiplier: Contract multiplier (default: 100 for standard equity options)
        
    Returns:
        Gamma exposure value in dollars
        
    Example:
        >>> calculate_gamma_exposure(gamma=0.05, open_interest=1000, contract_multiplier=100)
        5000.0
    """
    return gamma * open_interest * contract_multiplier


def calculate_net_gamma(
    call_gamma_exposure: float,
    put_gamma_exposure: float
) -> float:
    """
    Calculate net gamma exposure across calls and puts.
    
    Net gamma accounts for the directional difference between call and put gamma:
    - Calls have positive gamma (dealers are short gamma when retail buys)
    - Puts have negative gamma (directional exposure is opposite)
    
    Net Gamma = Call Gamma - Put Gamma
    
    Args:
        call_gamma_exposure: Total gamma exposure from call options
        put_gamma_exposure: Total gamma exposure from put options
        
    Returns:
        Net gamma exposure (positive = more call exposure, negative = more put exposure)
        
    Example:
        >>> calculate_net_gamma(call_gamma_exposure=10000, put_gamma_exposure=7000)
        3000.0
    """
    return call_gamma_exposure - put_gamma_exposure


def filter_strike_region(
    strikes: List[float],
    spot_price: float,
    pct_range: float = 0.15
) -> List[float]:
    """
    Filter strikes to a region around the spot price.
    
    For gamma analysis, we typically focus on strikes within ±15% of the
    current spot price, as these have the most market impact and liquidity.
    
    Args:
        strikes: List of strike prices to filter
        spot_price: Current underlying price
        pct_range: Percentage range around spot (default: 0.15 for ±15%)
        
    Returns:
        List of strikes within the specified range
        
    Example:
        >>> strikes = [90, 95, 100, 105, 110, 115, 120]
        >>> filter_strike_region(strikes, spot_price=100, pct_range=0.15)
        [90, 95, 100, 105, 110]
    """
    # Round bounds to avoid float drift (e.g. 100 * 1.15 can be 114.999...)
    # so boundary strikes still compare inclusively as intended.
    lower_bound = round(spot_price * (1 - pct_range), 6)
    upper_bound = round(spot_price * (1 + pct_range), 6)

    return [
        strike for strike in strikes
        if lower_bound <= strike <= upper_bound
    ]


def extract_greeks_from_contract(contract_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extract Greeks (delta, gamma, theta, vega) and IV from Schwab API contract data.
    
    The Schwab API nests Greeks in a 'greeks' object within the contract data:
    {
        "symbol": "SPY_041425C550",
        "bid": 1.25,
        "ask": 1.30,
        "volatility": 18.5,
        "greeks": {
            "delta": 0.45,
            "gamma": 0.05,
            "theta": -0.02,
            "vega": 0.15
        }
    }
    
    Args:
        contract_data: Contract data dictionary from Schwab API response
        
    Returns:
        Dictionary with extracted Greeks:
        {
            'delta': float or None,
            'gamma': float or None,
            'theta': float or None,
            'vega': float or None,
            'iv': float or None (implied volatility as percentage)
        }
        
    Raises:
        ValueError: If contract_data is None or empty
        
    Example:
        >>> contract = {
        ...     "greeks": {"delta": 0.5, "gamma": 0.05, "theta": -0.02, "vega": 0.15},
        ...     "volatility": 20.5
        ... }
        >>> extract_greeks_from_contract(contract)
        {'delta': 0.5, 'gamma': 0.05, 'theta': -0.02, 'vega': 0.15, 'iv': 20.5}
    """
    if not contract_data:
        raise ValueError("contract_data cannot be None or empty")
    
    # Extract nested Greeks object
    greeks = contract_data.get('greeks', {})
    
    # Extract individual Greeks, defaulting to None if not present
    result = {
        'delta': greeks.get('delta'),
        'gamma': greeks.get('gamma'),
        'theta': greeks.get('theta'),
        'vega': greeks.get('vega'),
        'iv': contract_data.get('volatility')  # IV is at top level
    }
    
    return result


def calculate_effective_gamma_exposure(
    gamma_exposure: float,
    distance_from_spot: float,
    spot_price: float
) -> float:
    """
    Calculate effective gamma exposure weighted by distance from spot.
    
    Gamma exposure has more impact when strikes are closer to the spot price.
    This function applies a distance-based weighting to reflect this reality.
    
    Effective Gamma = Gamma Exposure × (1 - |distance_pct|)
    
    Args:
        gamma_exposure: Raw gamma exposure value
        distance_from_spot: Absolute distance from spot price
        spot_price: Current underlying price
        
    Returns:
        Effective gamma exposure (weighted by proximity)
        
    Example:
        >>> # Strike at 100, spot at 105 (5% away)
        >>> calculate_effective_gamma_exposure(
        ...     gamma_exposure=10000,
        ...     distance_from_spot=5,
        ...     spot_price=105
        ... )
        9523.809523809524
    """
    if spot_price == 0:
        return 0.0
    
    distance_pct = abs(distance_from_spot) / spot_price
    weight = max(0.0, 1.0 - distance_pct)
    
    return gamma_exposure * weight
