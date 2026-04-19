"""
Main Strategy Detection Module

Coordinates all strategy detection functions and provides
a unified interface for detecting multi-leg options strategies.
"""
from typing import List, Dict, Optional
import logging

from .vertical_spread import detect_vertical_spread, calculate_vertical_spread_metrics
from .iron_butterfly import detect_iron_butterfly, validate_iron_butterfly_quantities
from .grouper import (
    group_by_time,
    group_by_expiration_and_underlying,
    extract_expiration_from_symbol
)

logger = logging.getLogger(__name__)


def detect_strategies(
    positions: List[Dict],
    time_grouping: bool = True,
    time_window_seconds: int = 60
) -> List[Dict]:
    """
    Detect multi-leg options strategies from a list of positions.
    
    This is the main entry point for strategy detection. It:
    1. Groups positions by underlying and expiration
    2. Optionally groups by time window
    3. Attempts to detect known strategies (vertical spreads, iron butterflies)
    4. Returns detected strategies with confidence scores
    
    Args:
        positions: List of position dictionaries with keys:
            - symbol: Option symbol
            - underlying_symbol: Underlying ticker
            - option_type: 'PUT' or 'CALL'
            - strike: Strike price
            - side: 'BUY' or 'SELL'
            - quantity: Number of contracts
            - expiration: Optional expiration date
            - entry_price: Optional premium
            - entry_time: Optional entry timestamp
        time_grouping: Whether to group by entry time (default True)
        time_window_seconds: Time window for grouping (default 60)
    
    Returns:
        List of detected strategies, each with:
            - strategy_type: Type of strategy detected
            - confidence: Confidence score (0-1)
            - legs: List of positions that form the strategy
            - Additional strategy-specific fields
    """
    if not positions:
        return []
    
    detected_strategies = []
    
    # Group by underlying and expiration
    grouped = group_by_expiration_and_underlying(positions)
    
    logger.info(f"Analyzing {len(positions)} positions in {len(grouped)} groups")
    
    for (underlying, expiration), group_positions in grouped.items():
        logger.debug(f"Processing group: {underlying} {expiration} ({len(group_positions)} positions)")
        
        # Further group by time if requested
        if time_grouping and len(group_positions) > 1:
            time_groups = group_by_time(group_positions, window_seconds=time_window_seconds)
        else:
            time_groups = [group_positions]
        
        for time_group in time_groups:
            # Try to detect strategies within this group
            strategies = _detect_strategies_in_group(time_group, underlying, expiration)
            detected_strategies.extend(strategies)
    
    logger.info(f"Detected {len(detected_strategies)} strategies")
    
    return detected_strategies


def _detect_strategies_in_group(
    positions: List[Dict],
    underlying: str,
    expiration: str
) -> List[Dict]:
    """
    Detect strategies within a single group of positions.
    
    Args:
        positions: List of positions to analyze
        underlying: Underlying symbol
        expiration: Expiration date
    
    Returns:
        List of detected strategies
    """
    strategies = []
    used_positions = set()
    
    # Sort positions by strike to help with pattern matching
    sorted_positions = sorted(positions, key=lambda p: p.get('strike', 0))
    
    # Try to detect 4-leg strategies first (iron butterfly)
    if len(sorted_positions) >= 4:
        # Try all combinations of 4 positions
        from itertools import combinations
        for combo in combinations(range(len(sorted_positions)), 4):
            if any(i in used_positions for i in combo):
                continue
            
            legs = [sorted_positions[i] for i in combo]
            result = detect_iron_butterfly(legs)
            
            if result and result.confidence >= 0.75:
                strategy = {
                    'strategy_type': result.strategy_type,
                    'confidence': result.confidence,
                    'underlying': underlying,
                    'expiration': expiration,
                    'legs': legs,
                    'center_strike': result.center_strike,
                    'wing_width': result.wing_width,
                    'max_profit': result.max_profit,
                    'max_loss': result.max_loss,
                    'breakeven_low': result.breakeven_low,
                    'breakeven_high': result.breakeven_high,
                    'notes': result.notes
                }
                strategies.append(strategy)
                used_positions.update(combo)
                logger.info(f"Detected {result.strategy_type}: {result.notes}")
                break  # Only match each position once
    
    # Try to detect 2-leg strategies (vertical spreads)
    if len(sorted_positions) >= 2:
        from itertools import combinations
        for combo in combinations(range(len(sorted_positions)), 2):
            if any(i in used_positions for i in combo):
                continue
            
            legs = [sorted_positions[i] for i in combo]
            result = detect_vertical_spread(legs)
            
            if result and result.confidence >= 0.80:
                metrics = calculate_vertical_spread_metrics(result)
                
                strategy = {
                    'strategy_type': result.strategy_type,
                    'confidence': result.confidence,
                    'underlying': underlying,
                    'expiration': expiration,
                    'legs': legs,
                    'strikes': result.strikes,
                    'long_strike': result.long_strike,
                    'short_strike': result.short_strike,
                    'option_type': result.option_type,
                    'net_debit_credit': result.net_debit_credit,
                    'width': metrics['width'],
                    'max_profit': metrics['max_profit'],
                    'max_loss': metrics['max_loss'],
                    'risk_reward_ratio': metrics['risk_reward_ratio'],
                    'notes': result.notes
                }
                strategies.append(strategy)
                used_positions.update(combo)
                logger.info(f"Detected {result.strategy_type}: {result.notes}")
    
    # Mark unused positions as single legs
    for i, pos in enumerate(sorted_positions):
        if i not in used_positions:
            option_type = pos.get('option_type', 'UNKNOWN')
            side = pos.get('side', 'UNKNOWN')
            strike = pos.get('strike', 0)
            
            strategy = {
                'strategy_type': 'Single Leg',
                'confidence': 1.0,
                'underlying': underlying,
                'expiration': expiration,
                'legs': [pos],
                'notes': f"{side} {strike} {option_type}"
            }
            strategies.append(strategy)
    
    return strategies


def detect_strategy_from_legs(legs: List[Dict]) -> Optional[Dict]:
    """
    Detect a single strategy from a specific set of legs.
    
    This is useful when you already know which legs should form a strategy
    and just want to classify it.
    
    Args:
        legs: List of option legs
    
    Returns:
        Detected strategy dictionary or None
    """
    if len(legs) == 2:
        result = detect_vertical_spread(legs)
        if result and result.confidence >= 0.80:
            metrics = calculate_vertical_spread_metrics(result)
            return {
                'strategy_type': result.strategy_type,
                'confidence': result.confidence,
                'legs': legs,
                'strikes': result.strikes,
                'long_strike': result.long_strike,
                'short_strike': result.short_strike,
                'option_type': result.option_type,
                'net_debit_credit': result.net_debit_credit,
                'width': metrics['width'],
                'max_profit': metrics['max_profit'],
                'max_loss': metrics['max_loss'],
                'risk_reward_ratio': metrics['risk_reward_ratio'],
                'notes': result.notes
            }
    
    elif len(legs) == 4:
        result = detect_iron_butterfly(legs)
        if result and result.confidence >= 0.75:
            return {
                'strategy_type': result.strategy_type,
                'confidence': result.confidence,
                'legs': legs,
                'center_strike': result.center_strike,
                'wing_width': result.wing_width,
                'max_profit': result.max_profit,
                'max_loss': result.max_loss,
                'breakeven_low': result.breakeven_low,
                'breakeven_high': result.breakeven_high,
                'notes': result.notes
            }
    
    return None
