"""
Unit tests for trade grouping functions
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategy.grouper import (
    group_by_time,
    group_by_expiration,
    group_by_underlying,
    group_by_expiration_and_underlying,
    group_by_order_id,
    extract_expiration_from_symbol,
    parse_entry_time,
)


class TestTimeGrouping:
    """Test time-based grouping"""
    
    def test_single_group_within_window(self):
        """Test trades within window are grouped together"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            {'id': 1, 'entry_time': base_time},
            {'id': 2, 'entry_time': base_time + timedelta(seconds=30)},
            {'id': 3, 'entry_time': base_time + timedelta(seconds=45)}
        ]
        
        groups = group_by_time(trades, window_seconds=60)
        
        assert len(groups) == 1
        assert len(groups[0]) == 3
    
    def test_multiple_groups(self):
        """Test trades outside window create separate groups"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            {'id': 1, 'entry_time': base_time},
            {'id': 2, 'entry_time': base_time + timedelta(seconds=30)},
            {'id': 3, 'entry_time': base_time + timedelta(seconds=120)},
            {'id': 4, 'entry_time': base_time + timedelta(seconds=130)}
        ]
        
        groups = group_by_time(trades, window_seconds=60)
        
        assert len(groups) == 2
        assert len(groups[0]) == 2
        assert len(groups[1]) == 2
    
    def test_empty_list(self):
        """Test empty trade list"""
        groups = group_by_time([])
        assert groups == []
    
    def test_trades_without_time(self):
        """Test trades without entry_time are separate groups"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            {'id': 1, 'entry_time': base_time},
            {'id': 2},
            {'id': 3}
        ]
        
        groups = group_by_time(trades)
        
        assert len(groups) == 3
        assert len(groups[0]) == 1
        assert groups[0][0]['id'] == 1
    
    def test_custom_window(self):
        """Test custom time window"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        trades = [
            {'id': 1, 'entry_time': base_time},
            {'id': 2, 'entry_time': base_time + timedelta(seconds=90)},
            {'id': 3, 'entry_time': base_time + timedelta(seconds=110)}
        ]
        
        # 60s window: should create 2 groups
        groups_60 = group_by_time(trades, window_seconds=60)
        assert len(groups_60) == 2
        
        # 120s window: should create 1 group
        groups_120 = group_by_time(trades, window_seconds=120)
        assert len(groups_120) == 1

    def test_iso8601_string_entry_times_group_like_datetime(self):
        """JSON ISO strings must group the same as datetime objects."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        trades_dt = [
            {"id": 1, "entry_time": base_time},
            {"id": 2, "entry_time": base_time + timedelta(seconds=30)},
            {"id": 3, "entry_time": base_time + timedelta(seconds=45)},
        ]
        trades_str = [
            {"id": 1, "entry_time": "2024-01-15T10:00:00Z"},
            {"id": 2, "entry_time": "2024-01-15T10:00:30Z"},
            {"id": 3, "entry_time": "2024-01-15T10:00:45Z"},
        ]
        g_dt = group_by_time(trades_dt, window_seconds=60)
        g_str = group_by_time(trades_str, window_seconds=60)
        assert len(g_dt) == len(g_str) == 1
        assert {x["id"] for x in g_dt[0]} == {x["id"] for x in g_str[0]}

    def test_mixed_string_and_datetime_entry_times(self):
        """Mixed str/datetime entry_times subtract safely after normalization."""
        base = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        trades = [
            {"id": 1, "entry_time": "2024-01-15T10:00:00Z"},
            {"id": 2, "entry_time": base + timedelta(seconds=20)},
        ]
        groups = group_by_time(trades, window_seconds=60)
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_unparseable_entry_time_treated_as_missing(self):
        """Invalid strings do not crash; all-unparseable collapses to one group (no timed splits)."""
        trades = [
            {"id": 1, "entry_time": "not-a-valid-date"},
            {"id": 2, "entry_time": "also-bad"},
        ]
        groups = group_by_time(trades, window_seconds=60)
        assert len(groups) == 1
        assert len(groups[0]) == 2


class TestParseEntryTime:
    """Tests for parse_entry_time helper."""

    def test_strict_rejects_garbage(self):
        with pytest.raises(ValueError):
            parse_entry_time("garbage", strict=True)

    def test_strict_accepts_iso_z(self):
        dt = parse_entry_time("2024-01-15T10:30:00Z", strict=True)
        assert dt is not None
        assert dt.tzinfo == timezone.utc

    def test_epoch_int(self):
        dt = parse_entry_time(1700000000, strict=True)
        assert dt.tzinfo == timezone.utc


class TestExpirationGrouping:
    """Test expiration-based grouping"""
    
    def test_group_by_expiration(self):
        """Test grouping by expiration date"""
        positions = [
            {'symbol': 'SPY_240115C450', 'expiration': '240115'},
            {'symbol': 'SPY_240115P445', 'expiration': '240115'},
            {'symbol': 'SPY_240122C450', 'expiration': '240122'},
            {'symbol': 'SPY', 'expiration': None}
        ]
        
        groups = group_by_expiration(positions)
        
        assert len(groups) == 3
        assert len(groups['240115']) == 2
        assert len(groups['240122']) == 1
        assert len(groups['no_expiration']) == 1
    
    def test_empty_list(self):
        """Test empty position list"""
        groups = group_by_expiration([])
        assert groups == {}


class TestUnderlyingGrouping:
    """Test underlying-based grouping"""
    
    def test_group_by_underlying(self):
        """Test grouping by underlying symbol"""
        positions = [
            {'symbol': 'SPY_240115C450', 'underlying_symbol': 'SPY'},
            {'symbol': 'SPY_240115P445', 'underlying_symbol': 'SPY'},
            {'symbol': 'AAPL_240122C180', 'underlying_symbol': 'AAPL'},
        ]
        
        groups = group_by_underlying(positions)
        
        assert len(groups) == 2
        assert len(groups['SPY']) == 2
        assert len(groups['AAPL']) == 1
    
    def test_fallback_to_symbol(self):
        """Test fallback to symbol field if underlying_symbol missing"""
        positions = [
            {'symbol': 'SPY'},
            {'symbol': 'AAPL'}
        ]
        
        groups = group_by_underlying(positions)
        
        assert len(groups) == 2
        assert len(groups['SPY']) == 1
        assert len(groups['AAPL']) == 1


class TestCombinedGrouping:
    """Test combined expiration and underlying grouping"""
    
    def test_group_by_both(self):
        """Test grouping by both underlying and expiration"""
        positions = [
            {'symbol': 'SPY_240115C450', 'underlying_symbol': 'SPY', 'expiration': '240115'},
            {'symbol': 'SPY_240115P445', 'underlying_symbol': 'SPY', 'expiration': '240115'},
            {'symbol': 'SPY_240122C450', 'underlying_symbol': 'SPY', 'expiration': '240122'},
            {'symbol': 'AAPL_240115C180', 'underlying_symbol': 'AAPL', 'expiration': '240115'},
        ]
        
        groups = group_by_expiration_and_underlying(positions)
        
        assert len(groups) == 3
        assert len(groups[('SPY', '240115')]) == 2
        assert len(groups[('SPY', '240122')]) == 1
        assert len(groups[('AAPL', '240115')]) == 1


class TestOrderIdGrouping:
    """Test order ID grouping"""
    
    def test_group_by_order_id(self):
        """Test grouping by order ID"""
        trades = [
            {'symbol': 'SPY_240115C450', 'order_id': 'ORDER1'},
            {'symbol': 'SPY_240115P445', 'order_id': 'ORDER1'},
            {'symbol': 'SPY_240122C450', 'order_id': 'ORDER2'},
        ]
        
        groups = group_by_order_id(trades)
        
        assert len(groups) == 2
        assert len(groups['ORDER1']) == 2
        assert len(groups['ORDER2']) == 1
    
    def test_missing_order_id(self):
        """Test trades without order_id"""
        trades = [
            {'symbol': 'SPY_240115C450', 'order_id': 'ORDER1'},
            {'symbol': 'SPY_240115P445'},
        ]
        
        groups = group_by_order_id(trades)
        
        assert len(groups) == 2
        assert len(groups['ORDER1']) == 1
        assert len(groups['no_order']) == 1


class TestExpirationExtraction:
    """Test expiration date extraction from symbols"""
    
    def test_occ_format_with_spaces(self):
        """Test OCC format with spaces"""
        symbol = 'SPXW  240115C04500000'
        expiration = extract_expiration_from_symbol(symbol)
        assert expiration == '240115'
    
    def test_underscore_format(self):
        """Test underscore format"""
        symbol = 'SPY_240115C450'
        expiration = extract_expiration_from_symbol(symbol)
        assert expiration == '240115'
    
    def test_underscore_format_put(self):
        """Test underscore format with PUT"""
        symbol = 'SPY_240122P445'
        expiration = extract_expiration_from_symbol(symbol)
        assert expiration == '240122'
    
    def test_invalid_symbol(self):
        """Test invalid symbol returns None"""
        assert extract_expiration_from_symbol('SPY') is None
        assert extract_expiration_from_symbol('') is None
        assert extract_expiration_from_symbol(None) is None
    
    def test_short_symbol(self):
        """Test symbol too short returns None"""
        symbol = 'SPY_24C450'
        expiration = extract_expiration_from_symbol(symbol)
        assert expiration is None
