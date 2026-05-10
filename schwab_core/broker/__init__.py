"""
Broker abstraction layer — Schwab response normalization (extensible via register_broker).

Tradier market-data HTTP belongs in the ``tradier-market`` package, not here.
"""

from .base import BrokerAdapter, Position, Account, OptionContract, OptionChainStrike
from .registry import get_broker, register_broker, list_brokers

__all__ = [
    "BrokerAdapter",
    "Position",
    "Account",
    "OptionContract",
    "OptionChainStrike",
    "get_broker",
    "register_broker",
    "list_brokers",
]
