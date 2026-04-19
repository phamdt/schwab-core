"""Tests for SchwabAdapter — verifies canonical output shape."""

import pytest
from schwab_core.broker.schwab import SchwabAdapter


@pytest.fixture()
def adapter():
    return SchwabAdapter()


SCHWAB_POSITION = {
    "longQuantity": 2.0,
    "averagePrice": 150.0,
    "marketValue": 320.0,
    "instrument": {
        "symbol": "AAPL",
        "assetType": "EQUITY",
        "description": "Apple Inc",
    },
}

SCHWAB_OPTION_POSITION = {
    "shortQuantity": 1.0,
    "averagePrice": 3.50,
    "marketValue": -350.0,
    "instrument": {
        "symbol": "AAPL240119C00150000",
        "assetType": "OPTION",
        "underlyingSymbol": "AAPL",
        "description": "AAPL 01/19/24 Call",
    },
}

SCHWAB_ACCOUNT_RESPONSE = [
    {
        "securitiesAccount": {
            "accountNumber": "123456789",
            "type": "MARGIN",
            "currentBalances": {
                "cashBalance": 5000.0,
                "availableFunds": 10000.0,
                "buyingPower": 20000.0,
                "liquidationValue": 50000.0,
            },
            "initialBalances": {
                "availableFundsNonMarginableTrade": 4000.0,
            },
        }
    }
]

SCHWAB_CHAIN = {
    "callExpDateMap": {
        "2024-01-19:5": {
            "150.0": [{"symbol": "AAPL240119C00150000", "bid": 1.0, "ask": 1.5}],
        }
    },
    "putExpDateMap": {
        "2024-01-19:5": {
            "150.0": [{"symbol": "AAPL240119P00150000", "bid": 0.5, "ask": 0.8}],
        }
    },
}


class TestSchwabAdapterName:
    def test_name(self, adapter):
        assert adapter.name == "schwab"


class TestSchwabParsePositions:
    def test_equity_position_shape(self, adapter):
        result = adapter.parse_positions([SCHWAB_POSITION])
        assert len(result) == 1
        pos = result[0]
        assert pos["symbol"] == "AAPL"
        assert pos["quantity"] == 2.0
        assert pos["entry_price"] == 150.0
        assert pos["asset_type"] == "EQUITY"

    def test_option_position_is_short(self, adapter):
        result = adapter.parse_positions([SCHWAB_OPTION_POSITION])
        assert len(result) == 1
        pos = result[0]
        assert pos["quantity"] == -1.0
        assert pos["asset_type"] == "OPTION"
        assert pos["underlying_symbol"] == "AAPL"

    def test_empty_list(self, adapter):
        assert adapter.parse_positions([]) == []

    def test_non_list_returns_empty(self, adapter):
        assert adapter.parse_positions({}) == []

    def test_missing_symbol_skipped(self, adapter):
        bad = {"longQuantity": 1.0, "instrument": {}}
        result = adapter.parse_positions([bad])
        assert result == []


class TestSchwabParseAccounts:
    def test_account_shape(self, adapter):
        result = adapter.parse_accounts(SCHWAB_ACCOUNT_RESPONSE)
        assert len(result) == 1
        acct = result[0]
        assert acct["account_id"] == "123456789"
        assert acct["account_type"] == "MARGIN"
        assert acct["balances"]["cash_balance"] == 5000.0
        assert acct["balances"]["buying_power"] == 20000.0

    def test_empty_response(self, adapter):
        assert adapter.parse_accounts([]) == []


class TestSchwabOptionChain:
    def test_list_expirations_strips_dte(self, adapter):
        exps = adapter.list_expirations(SCHWAB_CHAIN)
        assert exps == ["2024-01-19"]

    def test_parse_option_chain_strike(self, adapter):
        result = adapter.parse_option_chain(SCHWAB_CHAIN, "2024-01-19:5")
        assert len(result) == 1
        strike = result[0]
        assert strike["strike"] == 150.0
        assert len(strike["call_contracts"]) == 1
        assert len(strike["put_contracts"]) == 1

    def test_unknown_expiration_returns_empty(self, adapter):
        result = adapter.parse_option_chain(SCHWAB_CHAIN, "2099-01-01:999")
        assert result == []
