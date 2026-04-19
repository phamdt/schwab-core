"""
Trade Grouping Module

Groups trades and positions by time, expiration, and underlying symbol
for strategy detection.
"""
from __future__ import annotations

from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def _to_utc_aware(dt: datetime) -> datetime:
    """Normalize datetimes to UTC-aware for safe comparison and subtraction."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_datetime_string(s: str) -> Optional[datetime]:
    """Parse common API / ISO 8601 datetime strings to datetime."""
    raw = s.strip()
    if not raw:
        return None

    # ISO 8601 with Z suffix (JSON / RFC 3339)
    if raw.endswith("Z") and "T" in raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
    ):
        try:
            parsed = datetime.strptime(raw, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue

    return None


def parse_entry_time(value: Any, *, strict: bool = False) -> Optional[datetime]:
    """
    Coerce ``entry_time`` from JSON (str), datetime, or numeric epoch to UTC-aware datetime.

    Used by ``group_by_time`` and can be called at API boundaries with ``strict=True``
    to reject invalid formats with :class:`ValueError`.

    Args:
        value: ISO string, :class:`datetime`, int/float epoch seconds, or empty/None.
        strict: If True, invalid non-empty strings and unsupported types raise ValueError.

    Returns:
        UTC-aware datetime, or None if missing/empty/non-coercible (non-strict).
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return _to_utc_aware(value)
    if isinstance(value, str):
        if not value.strip():
            return None
        parsed = _parse_datetime_string(value)
        if parsed is None:
            if strict:
                raise ValueError(f"Invalid entry_time string: {value!r}")
            logger.warning("Could not parse entry_time string %r; treating as missing", value)
            return None
        return _to_utc_aware(parsed)
    if isinstance(value, (int, float)):
        # Epoch seconds (JSON rarely sends float for time, but tolerate it)
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OSError, OverflowError, ValueError) as e:
            if strict:
                raise ValueError(f"Invalid entry_time numeric value: {value!r}") from e
            logger.warning("Could not parse entry_time number %r; treating as missing", value)
            return None
    if strict:
        raise ValueError(
            f"entry_time must be string, datetime, or epoch number, got {type(value).__name__}"
        )
    return None


def group_by_time(trades: List[Dict], window_seconds: int = 60) -> List[List[Dict]]:
    """
    Group trades that occur within a time window.
    
    This helps identify strategy legs that were opened together
    even if they have different order IDs.
    
    Args:
        trades: List of trade dictionaries with 'entry_time' field
        window_seconds: Time window in seconds (default 60)
    
    Returns:
        List of trade groups, where each group is a list of trades
        that occurred within the time window
    """
    if not trades:
        return []
    
    # Filter trades with parseable entry times (strings from JSON, datetimes, epoch)
    valid_trades = [t for t in trades if parse_entry_time(t.get("entry_time"), strict=False)]
    
    if not valid_trades:
        # No parseable times — analyze as one batch (multi-leg detection, invalid strings included)
        return [trades] if trades else []
    
    def _sort_key(trade: Dict) -> datetime:
        dt = parse_entry_time(trade.get("entry_time"), strict=False)
        assert dt is not None  # valid_trades only
        return dt
    
    # Sort by entry time (UTC-normalized)
    sorted_trades = sorted(valid_trades, key=_sort_key)
    
    groups = []
    current_group = [sorted_trades[0]]
    base_time = parse_entry_time(sorted_trades[0].get("entry_time"), strict=False)
    assert base_time is not None
    
    for trade in sorted_trades[1:]:
        trade_time = parse_entry_time(trade.get("entry_time"), strict=False)
        assert trade_time is not None
        time_diff = abs((trade_time - base_time).total_seconds())
        
        if time_diff <= window_seconds:
            # Within window, add to current group
            current_group.append(trade)
        else:
            # Outside window, start new group
            groups.append(current_group)
            current_group = [trade]
            base_time = trade_time
    
    # Add last group
    if current_group:
        groups.append(current_group)
    
    # Add trades without entry times (or unparseable) as separate groups
    trades_without_time = [
        t for t in trades if not parse_entry_time(t.get("entry_time"), strict=False)
    ]
    for trade in trades_without_time:
        groups.append([trade])
    
    logger.debug(f"Grouped {len(trades)} trades into {len(groups)} time groups (window={window_seconds}s)")
    
    return groups


def group_by_expiration(positions: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group positions by expiration date.
    
    Args:
        positions: List of position dictionaries with 'expiration' field
    
    Returns:
        Dictionary mapping expiration date -> list of positions
    """
    groups = defaultdict(list)
    
    for pos in positions:
        expiration = pos.get('expiration')
        if expiration:
            groups[expiration].append(pos)
        else:
            # No expiration (e.g., stock position)
            groups['no_expiration'].append(pos)
    
    logger.debug(f"Grouped {len(positions)} positions into {len(groups)} expiration groups")
    
    return dict(groups)


def group_by_underlying(positions: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group positions by underlying symbol.
    
    Args:
        positions: List of position dictionaries with 'underlying_symbol' or 'symbol' field
    
    Returns:
        Dictionary mapping underlying symbol -> list of positions
    """
    groups = defaultdict(list)
    
    for pos in positions:
        underlying = pos.get('underlying_symbol') or pos.get('symbol')
        if underlying:
            groups[underlying].append(pos)
        else:
            logger.warning(f"Position missing underlying symbol: {pos}")
            groups['unknown'].append(pos)
    
    logger.debug(f"Grouped {len(positions)} positions into {len(groups)} underlying groups")
    
    return dict(groups)


def group_by_expiration_and_underlying(positions: List[Dict]) -> Dict[tuple, List[Dict]]:
    """
    Group positions by both expiration and underlying symbol.
    
    This is useful for detecting strategies on the same underlying
    with the same expiration.
    
    Args:
        positions: List of position dictionaries
    
    Returns:
        Dictionary mapping (underlying, expiration) -> list of positions
    """
    groups = defaultdict(list)
    
    for pos in positions:
        underlying = pos.get('underlying_symbol') or pos.get('symbol')
        expiration = pos.get('expiration') or 'no_expiration'
        
        if underlying:
            key = (underlying, expiration)
            groups[key].append(pos)
        else:
            logger.warning(f"Position missing underlying symbol: {pos}")
    
    logger.debug(
        f"Grouped {len(positions)} positions into {len(groups)} "
        f"underlying+expiration groups"
    )
    
    return dict(groups)


def extract_expiration_from_symbol(symbol: str) -> Optional[str]:
    """
    Extract expiration date from option symbol.
    
    Supports multiple formats:
    - OCC format: "SPXW  240115C04500000" (6 chars ticker + 6 chars date)
    - Underscore format: "SPXW_240115C4500"
    
    Args:
        symbol: Option symbol
    
    Returns:
        Expiration date string (YYMMDD format) or None
    """
    if not symbol:
        return None
    
    # OCC format with spaces
    if ' ' in symbol and len(symbol) >= 12:
        # Find the space position, date comes after ticker
        parts = symbol.split()
        if len(parts) >= 2 and len(parts[1]) >= 6:
            return parts[1][:6]
    
    # Underscore format
    elif '_' in symbol:
        parts = symbol.split('_')
        if len(parts) >= 2:
            opt_part = parts[1]
            # Find C or P position
            for i, char in enumerate(opt_part):
                if char in ['C', 'P']:
                    if i >= 6:
                        return opt_part[:6]
                    break
    
    return None


def group_by_order_id(trades: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group trades by order ID.
    
    Args:
        trades: List of trade dictionaries with 'order_id' field
    
    Returns:
        Dictionary mapping order_id -> list of trades
    """
    groups = defaultdict(list)
    
    for trade in trades:
        order_id = trade.get('order_id') or 'no_order'
        groups[order_id].append(trade)
    
    logger.debug(f"Grouped {len(trades)} trades into {len(groups)} order groups")
    
    return dict(groups)
