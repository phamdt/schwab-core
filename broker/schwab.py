"""
Schwab broker adapter.

Delegates to existing schwab-core transformers so no logic is duplicated.
"""

from typing import Any, List

from .base import BrokerAdapter, Account, OptionChainStrike, Position
from transformers.positions import transform_position_to_trade
from transformers.accounts import parse_account_response
from transformers.option_chain import (
    extract_option_chain_strikes,
    extract_expirations,
    parse_expiration_string,
)
import logging

logger = logging.getLogger(__name__)


class SchwabAdapter(BrokerAdapter):
    """Adapter that wraps schwab-core transformers into the canonical interface."""

    @property
    def name(self) -> str:
        return "schwab"

    def parse_positions(self, raw: Any) -> List[Position]:
        """
        Args:
            raw: List of Schwab position dicts (from /accounts/{id}/positions)

        Returns:
            List of canonical Position dicts
        """
        if not isinstance(raw, list):
            logger.warning("SchwabAdapter.parse_positions: expected list, got %s", type(raw))
            return []

        results: List[Position] = []
        for pos in raw:
            try:
                results.append(transform_position_to_trade(pos))  # type: ignore[arg-type]
            except (ValueError, KeyError) as exc:
                logger.error("SchwabAdapter: skipping position — %s", exc)
        return results

    def parse_accounts(self, raw: Any) -> List[Account]:
        """
        Args:
            raw: List of Schwab account objects (from /accounts)

        Returns:
            List of canonical Account dicts
        """
        return parse_account_response(raw)  # type: ignore[return-value]

    def parse_option_chain(
        self,
        raw: Any,
        expiration: str,
    ) -> List[OptionChainStrike]:
        """
        Args:
            raw: Schwab option chain response dict
            expiration: Expiration in Schwab format "YYYY-MM-DD:DTE" or plain "YYYY-MM-DD"

        Returns:
            List of OptionChainStrike dicts
        """
        strikes = extract_option_chain_strikes(raw, expiration)
        return strikes  # type: ignore[return-value]

    def list_expirations(self, raw: Any) -> List[str]:
        """
        Returns expiration dates as YYYY-MM-DD strings (strips the ':DTE' suffix).
        """
        raw_expirations = extract_expirations(raw)
        dates = []
        for exp in raw_expirations:
            parsed = parse_expiration_string(exp)
            dates.append(parsed["date"])
        return sorted(set(dates))
