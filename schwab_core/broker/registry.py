"""
Broker registry — resolve a BrokerAdapter by name.

Usage:
    from broker import get_broker

    adapter = get_broker("schwab")        # or "tradier"
    positions = adapter.parse_positions(raw_api_response)

Adding a 3rd broker:
    from broker.registry import register_broker
    from broker.my_broker import MyBrokerAdapter

    register_broker(MyBrokerAdapter())
"""

from typing import Dict

from .base import BrokerAdapter
from .schwab import SchwabAdapter
from .tradier import TradierAdapter

_registry: Dict[str, BrokerAdapter] = {}


def _bootstrap() -> None:
    for adapter in (SchwabAdapter(), TradierAdapter()):
        _registry[adapter.name] = adapter


_bootstrap()


def get_broker(name: str) -> BrokerAdapter:
    """
    Return the registered BrokerAdapter for *name*.

    Args:
        name: Broker identifier (e.g. 'schwab', 'tradier')

    Raises:
        KeyError: If broker is not registered

    Returns:
        BrokerAdapter instance
    """
    adapter = _registry.get(name.lower())
    if adapter is None:
        available = ", ".join(sorted(_registry))
        raise KeyError(f"Unknown broker '{name}'. Available: {available}")
    return adapter


def register_broker(adapter: BrokerAdapter) -> None:
    """
    Register a custom BrokerAdapter so it can be retrieved by name.

    Args:
        adapter: Instance of a BrokerAdapter subclass
    """
    if not isinstance(adapter, BrokerAdapter):
        raise TypeError(f"Expected BrokerAdapter, got {type(adapter)}")
    _registry[adapter.name.lower()] = adapter


def list_brokers() -> list[str]:
    """Return sorted list of registered broker names."""
    return sorted(_registry)
