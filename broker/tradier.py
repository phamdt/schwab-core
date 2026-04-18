"""
Tradier broker adapter.

Maps Tradier REST API responses to the canonical broker interface.

Tradier position response shape (GET /v1/accounts/{id}/positions):
  {
    "positions": {
      "position": [
        {
          "cost_basis": 1234.56,
          "date_acquired": "2024-01-15T...",
          "id": 123,
          "quantity": 10.0,
          "symbol": "AAPL"
        }
      ]
    }
  }

Tradier account/balances response shape (GET /v1/accounts/{id}/balances):
  {
    "balances": {
      "account_number": "...",
      "account_type": "margin",
      "cash": { "cash_available": ..., "sweep": ..., "unsettled_funds": ... },
      "margin": { "fed_call": ..., "maintenance_call": ..., "option_buying_power": ...,
                  "stock_buying_power": ..., "stock_short_value": ... },
      "total_equity": ...,
      "total_cash": ...
    }
  }

Tradier option chain response shape (GET /v1/markets/options/chains):
  {
    "options": {
      "option": [
        {
          "symbol": "AAPL240119C00150000",
          "description": "...",
          "exch": "...",
          "type": "call",
          "last": 1.23,
          "change": ...,
          "volume": 100,
          "open": ...,
          "high": ...,
          "low": ...,
          "close": ...,
          "bid": 1.20,
          "ask": 1.25,
          "underlying": "AAPL",
          "strike": 150.0,
          "expiration_date": "2024-01-19",
          "open_interest": 500,
          "greeks": { "delta": 0.55, "gamma": 0.02, "theta": -0.05, "vega": 0.10 }
        }
      ]
    }
  }
"""

from typing import Any, Dict, List, Optional
import logging

from .base import (
    Account,
    AccountBalances,
    BrokerAdapter,
    OptionChainStrike,
    OptionContract,
    Position,
)

logger = logging.getLogger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _parse_tradier_position(pos: Dict[str, Any]) -> Optional[Position]:
    """Map a single Tradier position dict to a canonical Position."""
    symbol = pos.get("symbol")
    if not symbol:
        logger.warning("TradierAdapter: position missing symbol, skipping")
        return None

    quantity = _safe_float(pos.get("quantity", 0))
    cost_basis = _safe_float(pos.get("cost_basis", 0))
    entry_price = cost_basis / abs(quantity) if quantity != 0 else 0.0

    # Tradier positions API does not include real-time market price —
    # callers should enrich with a quotes call if needed.
    current_price = _safe_float(pos.get("current_price", entry_price))

    profit = (current_price - entry_price) * quantity

    # Tradier doesn't distinguish OPTION vs EQUITY in the positions endpoint;
    # detect options by OCC symbol length (> 6 chars with digits/letters pattern).
    asset_type = "OPTION" if len(symbol) > 6 and any(c.isdigit() for c in symbol[1:]) else "EQUITY"

    return Position(
        symbol=symbol,
        quantity=quantity,
        entry_price=entry_price,
        current_price=current_price,
        profit=profit,
        market_value=current_price * quantity * (100 if asset_type == "OPTION" else 1),
        asset_type=asset_type,
        description=pos.get("description", ""),
        total_pnl=profit,
        day_pnl=None,
        percent_of_account=None,
    )


def _parse_tradier_option(opt: Dict[str, Any]) -> OptionContract:
    """Map a single Tradier option dict to a canonical OptionContract."""
    greeks = opt.get("greeks") or {}
    return OptionContract(
        symbol=opt.get("symbol", ""),
        strike=_safe_float(opt.get("strike")),
        expiration_date=opt.get("expiration_date", ""),
        option_type=str(opt.get("type", "")).upper(),
        bid=_safe_float(opt.get("bid")),
        ask=_safe_float(opt.get("ask")),
        last=_safe_float(opt.get("last")),
        volume=int(opt.get("volume") or 0),
        open_interest=int(opt.get("open_interest") or 0),
        delta=_safe_float(greeks.get("delta")) if greeks.get("delta") is not None else None,
        gamma=_safe_float(greeks.get("gamma")) if greeks.get("gamma") is not None else None,
        theta=_safe_float(greeks.get("theta")) if greeks.get("theta") is not None else None,
        vega=_safe_float(greeks.get("vega")) if greeks.get("vega") is not None else None,
        implied_volatility=_safe_float(opt.get("iv")) if opt.get("iv") is not None else None,
    )


class TradierAdapter(BrokerAdapter):
    """Adapter for the Tradier REST API."""

    @property
    def name(self) -> str:
        return "tradier"

    def parse_positions(self, raw: Any) -> List[Position]:
        """
        Args:
            raw: Tradier /accounts/{id}/positions response dict

        Returns:
            List of canonical Position dicts
        """
        positions_wrapper = (raw or {}).get("positions", {})
        if not positions_wrapper or positions_wrapper == "null":
            return []

        raw_positions = positions_wrapper.get("position", [])
        if isinstance(raw_positions, dict):
            raw_positions = [raw_positions]

        results: List[Position] = []
        for pos in raw_positions:
            parsed = _parse_tradier_position(pos)
            if parsed is not None:
                results.append(parsed)
        return results

    def parse_accounts(self, raw: Any) -> List[Account]:
        """
        Args:
            raw: Tradier /accounts/{id}/balances response dict

        Returns:
            List of canonical Account dicts (single-element for Tradier)
        """
        balances_data = (raw or {}).get("balances", {})
        if not balances_data:
            logger.warning("TradierAdapter.parse_accounts: no 'balances' key in response")
            return []

        account_id = str(balances_data.get("account_number", ""))
        account_type = str(balances_data.get("account_type", "unknown")).upper()

        margin = balances_data.get("margin") or {}
        cash = balances_data.get("cash") or {}

        buying_power = _safe_float(
            margin.get("stock_buying_power") or cash.get("cash_available")
        )
        cash_balance = _safe_float(balances_data.get("total_cash"))
        total_balance = _safe_float(balances_data.get("total_equity"))

        balances: AccountBalances = {
            "cash_balance": cash_balance,
            "available_funds": buying_power,
            "buying_power": buying_power,
            "total_balance": total_balance,
            "available_funds_non_marginable": _safe_float(cash.get("cash_available")),
        }

        return [Account(account_id=account_id, account_type=account_type, balances=balances)]

    def parse_option_chain(
        self,
        raw: Any,
        expiration: str,
    ) -> List[OptionChainStrike]:
        """
        Args:
            raw: Tradier /markets/options/chains response dict
            expiration: YYYY-MM-DD string to filter by

        Returns:
            List of OptionChainStrike dicts for the given expiration
        """
        options_wrapper = (raw or {}).get("options", {})
        if not options_wrapper or options_wrapper == "null":
            return []

        raw_options = options_wrapper.get("option", [])
        if isinstance(raw_options, dict):
            raw_options = [raw_options]

        # Filter to requested expiration and group by strike
        strikes_map: Dict[float, OptionChainStrike] = {}
        for opt in raw_options:
            if opt.get("expiration_date") != expiration:
                continue

            strike = _safe_float(opt.get("strike"))
            if strike not in strikes_map:
                strikes_map[strike] = OptionChainStrike(
                    strike=strike, call_contracts=[], put_contracts=[]
                )

            contract = _parse_tradier_option(opt)
            option_type = str(opt.get("type", "")).lower()
            if option_type == "call":
                strikes_map[strike]["call_contracts"].append(contract)
            elif option_type == "put":
                strikes_map[strike]["put_contracts"].append(contract)

        return [strikes_map[k] for k in sorted(strikes_map)]

    def list_expirations(self, raw: Any) -> List[str]:
        """
        Returns sorted YYYY-MM-DD expiration strings found in the chain response.
        """
        options_wrapper = (raw or {}).get("options", {})
        if not options_wrapper or options_wrapper == "null":
            return []

        raw_options = options_wrapper.get("option", [])
        if isinstance(raw_options, dict):
            raw_options = [raw_options]

        dates = sorted({opt.get("expiration_date", "") for opt in raw_options if opt.get("expiration_date")})
        return dates
