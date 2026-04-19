"""Tests for TradierAdapter — verifies canonical output shape."""

import pytest
from schwab_core.broker.tradier import TradierAdapter


@pytest.fixture()
def adapter():
    return TradierAdapter()


TRADIER_POSITIONS_RESPONSE = {
    "positions": {
        "position": [
            {
                "cost_basis": 3000.0,
                "date_acquired": "2024-01-10T00:00:00.000Z",
                "id": 1,
                "quantity": 10.0,
                "symbol": "MSFT",
            }
        ]
    }
}

TRADIER_SINGLE_POSITION_RESPONSE = {
    "positions": {
        "position": {
            "cost_basis": 500.0,
            "date_acquired": "2024-02-01T00:00:00.000Z",
            "id": 2,
            "quantity": 5.0,
            "symbol": "GOOG",
        }
    }
}

TRADIER_BALANCES_RESPONSE = {
    "balances": {
        "account_number": "ABC123",
        "account_type": "margin",
        "total_equity": 75000.0,
        "total_cash": 8000.0,
        "cash": {"cash_available": 8000.0},
        "margin": {"stock_buying_power": 16000.0},
    }
}

TRADIER_CHAIN_RESPONSE = {
    "options": {
        "option": [
            {
                "symbol": "AAPL240119C00150000",
                "type": "call",
                "strike": 150.0,
                "expiration_date": "2024-01-19",
                "bid": 1.20,
                "ask": 1.30,
                "last": 1.25,
                "volume": 200,
                "open_interest": 1000,
                "greeks": {"delta": 0.55, "gamma": 0.02, "theta": -0.04, "vega": 0.10},
            },
            {
                "symbol": "AAPL240119P00150000",
                "type": "put",
                "strike": 150.0,
                "expiration_date": "2024-01-19",
                "bid": 0.80,
                "ask": 0.90,
                "last": 0.85,
                "volume": 150,
                "open_interest": 800,
                "greeks": {"delta": -0.45, "gamma": 0.02, "theta": -0.03, "vega": 0.09},
            },
            {
                "symbol": "AAPL240126C00155000",
                "type": "call",
                "strike": 155.0,
                "expiration_date": "2024-01-26",
                "bid": 0.50,
                "ask": 0.60,
                "last": 0.55,
                "volume": 50,
                "open_interest": 300,
                "greeks": {},
            },
        ]
    }
}


class TestTradierAdapterName:
    def test_name(self, adapter):
        assert adapter.name == "tradier"


class TestTradierParsePositions:
    def test_list_position(self, adapter):
        result = adapter.parse_positions(TRADIER_POSITIONS_RESPONSE)
        assert len(result) == 1
        pos = result[0]
        assert pos["symbol"] == "MSFT"
        assert pos["quantity"] == 10.0
        assert pos["entry_price"] == pytest.approx(300.0)
        assert pos["asset_type"] == "EQUITY"

    def test_single_position_dict_wrapped(self, adapter):
        result = adapter.parse_positions(TRADIER_SINGLE_POSITION_RESPONSE)
        assert len(result) == 1
        assert result[0]["symbol"] == "GOOG"

    def test_null_positions_returns_empty(self, adapter):
        assert adapter.parse_positions({"positions": "null"}) == []

    def test_none_response_returns_empty(self, adapter):
        assert adapter.parse_positions(None) == []

    def test_empty_positions_key(self, adapter):
        assert adapter.parse_positions({"positions": {}}) == []


class TestTradierParseAccounts:
    def test_account_shape(self, adapter):
        result = adapter.parse_accounts(TRADIER_BALANCES_RESPONSE)
        assert len(result) == 1
        acct = result[0]
        assert acct["account_id"] == "ABC123"
        assert acct["account_type"] == "MARGIN"
        assert acct["balances"]["total_balance"] == 75000.0
        assert acct["balances"]["cash_balance"] == 8000.0
        assert acct["balances"]["buying_power"] == 16000.0

    def test_missing_balances_returns_empty(self, adapter):
        assert adapter.parse_accounts({}) == []


class TestTradierOptionChain:
    def test_list_expirations(self, adapter):
        exps = adapter.list_expirations(TRADIER_CHAIN_RESPONSE)
        assert exps == ["2024-01-19", "2024-01-26"]

    def test_parse_option_chain_filters_expiration(self, adapter):
        result = adapter.parse_option_chain(TRADIER_CHAIN_RESPONSE, "2024-01-19")
        assert len(result) == 1
        strike = result[0]
        assert strike["strike"] == 150.0
        assert len(strike["call_contracts"]) == 1
        assert len(strike["put_contracts"]) == 1

    def test_option_contract_greeks(self, adapter):
        result = adapter.parse_option_chain(TRADIER_CHAIN_RESPONSE, "2024-01-19")
        call = result[0]["call_contracts"][0]
        assert call["delta"] == pytest.approx(0.55)
        assert call["gamma"] == pytest.approx(0.02)

    def test_unknown_expiration_returns_empty(self, adapter):
        result = adapter.parse_option_chain(TRADIER_CHAIN_RESPONSE, "2099-12-31")
        assert result == []

    def test_null_options_returns_empty(self, adapter):
        assert adapter.parse_option_chain({"options": "null"}, "2024-01-19") == []
