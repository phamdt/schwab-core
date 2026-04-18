"""
Unit tests for transformer utilities.
"""

import pytest
from schwab_core.transformers.utils import (
    resolve_field_priority,
    resolve_nested_field_priority,
)


class TestResolveFieldPriority:
    """Tests for resolve_field_priority function."""
    
    def test_first_field_found(self):
        """Test that first non-None field is returned."""
        data = {'field1': 100, 'field2': 200, 'field3': 300}
        result = resolve_field_priority(data, ['field1', 'field2', 'field3'])
        assert result == 100
    
    def test_skip_none_values(self):
        """Test that None values are skipped."""
        data = {'field1': None, 'field2': 200, 'field3': 300}
        result = resolve_field_priority(data, ['field1', 'field2', 'field3'])
        assert result == 200
    
    def test_skip_missing_fields(self):
        """Test that missing fields are skipped."""
        data = {'field2': 200, 'field3': 300}
        result = resolve_field_priority(data, ['field1', 'field2', 'field3'])
        assert result == 200
    
    def test_return_default_when_none_found(self):
        """Test that default is returned when no field found."""
        data = {'other': 100}
        result = resolve_field_priority(data, ['field1', 'field2'], default=999)
        assert result == 999
    
    def test_default_none(self):
        """Test that None is returned as default when not specified."""
        data = {'other': 100}
        result = resolve_field_priority(data, ['field1', 'field2'])
        assert result is None
    
    def test_zero_value_is_valid(self):
        """Test that 0 is considered a valid value."""
        data = {'field1': 0, 'field2': 200}
        result = resolve_field_priority(data, ['field1', 'field2'])
        assert result == 0
    
    def test_false_value_is_valid(self):
        """Test that False is considered a valid value."""
        data = {'field1': False, 'field2': True}
        result = resolve_field_priority(data, ['field1', 'field2'])
        assert result is False
    
    def test_empty_string_is_valid(self):
        """Test that empty string is considered a valid value."""
        data = {'field1': '', 'field2': 'value'}
        result = resolve_field_priority(data, ['field1', 'field2'])
        assert result == ''


class TestResolveNestedFieldPriority:
    """Tests for resolve_nested_field_priority function."""
    
    def test_simple_field(self):
        """Test with simple non-nested field."""
        data = {'symbol': 'AAPL'}
        result = resolve_nested_field_priority(data, ['symbol'])
        assert result == 'AAPL'
    
    def test_nested_field(self):
        """Test with nested field using dot notation."""
        data = {
            'instrument': {
                'symbol': 'AAPL'
            }
        }
        result = resolve_nested_field_priority(data, ['instrument.symbol'])
        assert result == 'AAPL'
    
    def test_deep_nested_field(self):
        """Test with deeply nested field."""
        data = {
            'level1': {
                'level2': {
                    'level3': 'value'
                }
            }
        }
        result = resolve_nested_field_priority(data, ['level1.level2.level3'])
        assert result == 'value'
    
    def test_priority_order(self):
        """Test that priority order is respected."""
        data = {
            'instrument': {'symbol': 'FIRST'},
            'symbol': 'SECOND'
        }
        result = resolve_nested_field_priority(data, ['instrument.symbol', 'symbol'])
        assert result == 'FIRST'
    
    def test_skip_missing_nested_path(self):
        """Test that missing nested paths are skipped."""
        data = {
            'symbol': 'FALLBACK'
        }
        result = resolve_nested_field_priority(data, ['instrument.symbol', 'symbol'])
        assert result == 'FALLBACK'
    
    def test_skip_none_values(self):
        """Test that None values are skipped."""
        data = {
            'instrument': {'symbol': None},
            'symbol': 'FALLBACK'
        }
        result = resolve_nested_field_priority(data, ['instrument.symbol', 'symbol'])
        assert result == 'FALLBACK'
    
    def test_partial_path_exists(self):
        """Test when partial path exists but not complete."""
        data = {
            'instrument': {},
            'symbol': 'FALLBACK'
        }
        result = resolve_nested_field_priority(data, ['instrument.symbol', 'symbol'])
        assert result == 'FALLBACK'
    
    def test_return_default_when_none_found(self):
        """Test that default is returned when no field found."""
        data = {'other': 'value'}
        result = resolve_nested_field_priority(
            data,
            ['instrument.symbol', 'symbol'],
            default='DEFAULT'
        )
        assert result == 'DEFAULT'
    
    def test_default_none(self):
        """Test that None is returned as default when not specified."""
        data = {'other': 'value'}
        result = resolve_nested_field_priority(data, ['instrument.symbol', 'symbol'])
        assert result is None
    
    def test_mixed_nested_and_simple(self):
        """Test mixing nested and simple field paths."""
        data = {
            'simple': 'FOUND'
        }
        result = resolve_nested_field_priority(
            data,
            ['nested.path', 'another.nested.path', 'simple']
        )
        assert result == 'FOUND'
    
    def test_non_dict_in_path(self):
        """Test handling when non-dict encountered in path."""
        data = {
            'instrument': 'STRING_NOT_DICT'
        }
        result = resolve_nested_field_priority(
            data,
            ['instrument.symbol', 'fallback'],
            default='DEFAULT'
        )
        assert result == 'DEFAULT'
    
    def test_zero_value_is_valid(self):
        """Test that 0 is considered a valid value."""
        data = {
            'instrument': {'price': 0},
            'price': 100
        }
        result = resolve_nested_field_priority(data, ['instrument.price', 'price'])
        assert result == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
