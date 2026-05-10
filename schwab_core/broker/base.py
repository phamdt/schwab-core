"""
Canonical broker adapter interface.

All brokers must implement BrokerAdapter and produce the typed dicts defined here.
Consumers should depend only on this module — never on broker-specific transformers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict


class Position(TypedDict, total=False):
    symbol: str
    quantity: float                 # positive = long, negative = short
    entry_price: float
    current_price: float
    profit: float
    market_value: float
    asset_type: str                 # "OPTION" | "EQUITY" | "UNKNOWN"
    description: str
    underlying_symbol: Optional[str]
    total_pnl: Optional[float]
    day_pnl: Optional[float]
    percent_of_account: Optional[float]
    strategy_group_id: Optional[str]
    strategy_type: Optional[str]


class Account(TypedDict):
    account_id: str
    account_type: str
    balances: "AccountBalances"


class AccountBalances(TypedDict):
    cash_balance: float
    available_funds: float
    buying_power: float
    total_balance: float
    available_funds_non_marginable: float


class OptionContract(TypedDict, total=False):
    symbol: str
    strike: float
    expiration_date: str            # YYYY-MM-DD
    option_type: str                # "CALL" | "PUT"
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    implied_volatility: Optional[float]


class OptionChainStrike(TypedDict):
    strike: float
    call_contracts: List[OptionContract]
    put_contracts: List[OptionContract]


class BrokerAdapter(ABC):
    """
    Abstract base class every broker adapter must implement.

    Input is the raw API response dict from the respective broker.
    Output is always one of the canonical typed dicts above.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique broker identifier (e.g. 'schwab')."""

    @abstractmethod
    def parse_positions(self, raw: Any) -> List[Position]:
        """
        Transform raw broker position data into a list of canonical Position dicts.

        Args:
            raw: Raw API response (format varies per broker)

        Returns:
            List of Position dicts
        """

    @abstractmethod
    def parse_accounts(self, raw: Any) -> List[Account]:
        """
        Transform raw broker account data into a list of canonical Account dicts.

        Args:
            raw: Raw API response (format varies per broker)

        Returns:
            List of Account dicts
        """

    @abstractmethod
    def parse_option_chain(
        self,
        raw: Any,
        expiration: str,
    ) -> List[OptionChainStrike]:
        """
        Transform raw broker option chain data for a single expiration.

        Args:
            raw: Raw API response (format varies per broker)
            expiration: Expiration date string (YYYY-MM-DD)

        Returns:
            List of OptionChainStrike dicts sorted by strike ascending
        """

    @abstractmethod
    def list_expirations(self, raw: Any) -> List[str]:
        """
        Return sorted list of available expiration date strings (YYYY-MM-DD).

        Args:
            raw: Raw API response (format varies per broker)

        Returns:
            Sorted list of YYYY-MM-DD strings
        """
