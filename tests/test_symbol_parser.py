"""Tests for schwab_core.symbol.parser module."""

import pytest
from schwab_core.symbol import (
    normalize_symbol_for_schwab,
    parse_strike_from_symbol,
    parse_expiration_from_symbol,
    OptionSymbolParseError,
    INDEX_SYMBOL_MAP,
)


class TestNormalizeSymbolForSchwab:
    """Tests for normalize_symbol_for_schwab."""

    def test_index_symbols_get_dollar_prefix(self):
        assert normalize_symbol_for_schwab("SPX") == "$SPX"
        assert normalize_symbol_for_schwab("VIX") == "$VIX"
        assert normalize_symbol_for_schwab("DJI") == "$DJI"
        assert normalize_symbol_for_schwab("NDX") == "$NDX"
        assert normalize_symbol_for_schwab("RUT") == "$RUT"

    def test_index_alias_mapping(self):
        assert normalize_symbol_for_schwab("XSP") == "$SPX"
        assert normalize_symbol_for_schwab("COMP") == "$COMP"

    def test_already_prefixed_unchanged(self):
        assert normalize_symbol_for_schwab("$SPX") == "$SPX"
        assert normalize_symbol_for_schwab("$VIX") == "$VIX"

    def test_stock_symbols_unchanged(self):
        assert normalize_symbol_for_schwab("AAPL") == "AAPL"
        assert normalize_symbol_for_schwab("TSLA") == "TSLA"
        assert normalize_symbol_for_schwab("SPY") == "SPY"

    def test_strips_whitespace(self):
        assert normalize_symbol_for_schwab("  SPX  ") == "$SPX"
        assert normalize_symbol_for_schwab(" AAPL ") == "AAPL"

    def test_case_insensitive_lookup(self):
        assert normalize_symbol_for_schwab("spx") == "$SPX"
        assert normalize_symbol_for_schwab("vix") == "$VIX"

    def test_all_mapped_symbols_covered(self):
        for raw, expected in INDEX_SYMBOL_MAP.items():
            assert normalize_symbol_for_schwab(raw) == expected


class TestParseStrikeFromSymbol:

    def test_standard_format(self):
        assert parse_strike_from_symbol("AAPL_012025C150") == 150.0

    def test_index_8_digit_strike(self):
        assert parse_strike_from_symbol("SPXW  251113C06815000") == 6815.0

    def test_raises_on_bad_symbol(self):
        with pytest.raises(OptionSymbolParseError):
            parse_strike_from_symbol("NOSYMBOL")


class TestParseExpirationFromSymbol:

    def test_standard_format(self):
        result = parse_expiration_from_symbol("AAPL_012025C150")
        assert result.month == 1
        assert result.day == 20
        assert result.year == 2025

    def test_raises_on_bad_symbol(self):
        with pytest.raises(OptionSymbolParseError):
            parse_expiration_from_symbol("NOSYMBOL")
