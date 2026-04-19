"""
Broker abstraction layer — swap between Schwab, Tradier, or any future broker
by name without changing consumer code.
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
