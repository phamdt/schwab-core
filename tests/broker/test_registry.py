"""Tests for broker registry."""

import pytest

from broker.registry import get_broker, list_brokers, register_broker
from broker.base import BrokerAdapter, Position, Account, OptionChainStrike


def test_list_brokers_includes_defaults():
    brokers = list_brokers()
    assert "schwab" in brokers
    assert "tradier" in brokers


def test_get_broker_schwab():
    adapter = get_broker("schwab")
    assert adapter.name == "schwab"


def test_get_broker_tradier():
    adapter = get_broker("tradier")
    assert adapter.name == "tradier"


def test_get_broker_case_insensitive():
    assert get_broker("Schwab").name == "schwab"
    assert get_broker("TRADIER").name == "tradier"


def test_get_broker_unknown_raises():
    with pytest.raises(KeyError, match="Unknown broker"):
        get_broker("robinhood")


def test_register_custom_broker():
    class StubAdapter(BrokerAdapter):
        @property
        def name(self):
            return "stub"

        def parse_positions(self, raw):
            return []

        def parse_accounts(self, raw):
            return []

        def parse_option_chain(self, raw, expiration):
            return []

        def list_expirations(self, raw):
            return []

    register_broker(StubAdapter())
    adapter = get_broker("stub")
    assert adapter.name == "stub"
    assert "stub" in list_brokers()


def test_register_non_adapter_raises():
    with pytest.raises(TypeError):
        register_broker("not-an-adapter")  # type: ignore
