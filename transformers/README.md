# Schwab Core - Data Transformers Module

This module provides data transformers that parse Schwab API responses into standardized formats. The transformers handle the complexity and inconsistency of Schwab API response structures, providing clean, predictable data for downstream processing.

## Overview

The transformers module consists of 4 main components:

1. **positions.py** - Transform position data to standardized trades
2. **accounts.py** - Parse account data with balance information
3. **option_chain.py** - Extract option chain strikes and expirations
4. **utils.py** - Utility functions for field resolution

## Installation

```python
from schwab_core.transformers import (
    transform_position_to_trade,
    parse_account_response,
    extract_option_chain_strikes,
    resolve_field_priority
)
```

## Position Transformers

### `transform_position_to_trade(position: Dict) -> Dict`

Transforms a Schwab API position into a standardized Trade dictionary.

**Features:**
- Handles long/short positions with `longQuantity`/`shortQuantity`
- Extracts symbol from multiple locations with fallbacks
- Resolves prices using field priority rules
- Calculates P&L: `(current_price - entry_price) * quantity`
- Handles both equity and option positions

**Example:**

```python
schwab_position = {
    'instrument': {
        'symbol': 'AAPL',
        'assetType': 'EQUITY',
        'description': 'Apple Inc.'
    },
    'longQuantity': 100,
    'shortQuantity': 0,
    'averagePrice': 150.0,
    'marketPrice': 155.0,
    'marketValue': 15500.0
}

trade = transform_position_to_trade(schwab_position)
# Result:
# {
#     'symbol': 'AAPL',
#     'quantity': 100.0,
#     'entry_price': 150.0,
#     'current_price': 155.0,
#     'profit': 500.0,
#     'market_value': 15500.0,
#     'asset_type': 'EQUITY',
#     ...
# }
```

### Field Priority Rules

The transformer uses the following priority order for field resolution:

**Entry Price:**
1. `averagePrice`
2. `price`
3. `purchasePrice`
4. `averageCost`
5. Calculated from `costBasis / quantity`

**Current Price:**
1. `marketPrice`
2. `lastPrice`
3. `currentPrice`
4. Calculated from `marketValue / quantity` (or `/ (quantity * 100)` for options)
5. Fall back to `entry_price`

**Market Value:**
1. `marketValue`
2. `currentValue`
3. `currentValueUSD`
4. Calculated from `current_price * quantity` (or `* quantity * 100` for options)

**Symbol:**
1. `instrument.symbol`
2. `position.symbol`
3. Parsed from `instrument.description` (for options)

## Account Transformers

### `parse_account_response(schwab_response: List[Dict]) -> List[Dict]`

Parses Schwab API account response, unwrapping the `securitiesAccount` wrapper and extracting balances.

**Features:**
- Unwraps `securitiesAccount` wrapper
- Extracts account ID with fallback fields
- Parses current and initial balances
- Returns standardized account dictionaries

**Example:**

```python
schwab_response = [{
    'securitiesAccount': {
        'accountNumber': '12345678',
        'type': 'MARGIN',
        'currentBalances': {
            'cashBalance': 10000.0,
            'availableFunds': 8000.0,
            'buyingPower': 16000.0,
            'liquidationValue': 25000.0
        },
        'initialBalances': {
            'availableFundsNonMarginableTrade': 5000.0
        }
    }
}]

accounts = parse_account_response(schwab_response)
# Result:
# [{
#     'account_id': '12345678',
#     'account_type': 'MARGIN',
#     'balances': {
#         'cash_balance': 10000.0,
#         'available_funds': 8000.0,
#         'buying_power': 16000.0,
#         'total_balance': 25000.0,
#         'available_funds_non_marginable': 5000.0
#     }
# }]
```

### Account ID Priority

The parser uses the following priority order for account ID:
1. `accountNumber`
2. `accountId`
3. `id`
4. `number`

## Option Chain Transformers

### `extract_option_chain_strikes(chain_data: Dict, expiration: str) -> List[Dict]`

Extracts option chain strikes for a specific expiration date.

**Features:**
- Parses `callExpDateMap` and `putExpDateMap` structures
- Handles expiration format: `"YYYY-MM-DD:DTE"` (e.g., `"2025-01-17:0"`)
- Converts strike keys from string to float
- Returns sorted strikes with call and put contracts

**Example:**

```python
chain_data = {
    'callExpDateMap': {
        '2025-01-17:0': {
            '100.0': [{'symbol': 'AAPL250117C00100000', 'bid': 5.0}],
            '105.0': [{'symbol': 'AAPL250117C00105000', 'bid': 3.0}]
        }
    },
    'putExpDateMap': {
        '2025-01-17:0': {
            '100.0': [{'symbol': 'AAPL250117P00100000', 'bid': 2.0}],
            '105.0': [{'symbol': 'AAPL250117P00105000', 'bid': 4.0}]
        }
    }
}

strikes = extract_option_chain_strikes(chain_data, '2025-01-17:0')
# Result:
# [
#     {
#         'strike': 100.0,
#         'call_contracts': [{'symbol': 'AAPL250117C00100000', 'bid': 5.0}],
#         'put_contracts': [{'symbol': 'AAPL250117P00100000', 'bid': 2.0}]
#     },
#     {
#         'strike': 105.0,
#         'call_contracts': [{'symbol': 'AAPL250117C00105000', 'bid': 3.0}],
#         'put_contracts': [{'symbol': 'AAPL250117P00105000', 'bid': 4.0}]
#     }
# ]
```

### Additional Option Chain Functions

- **`extract_expirations(chain_data: Dict) -> List[str]`** - Get all available expiration dates
- **`parse_expiration_string(expiration: str) -> Dict`** - Parse expiration string into date and DTE
- **`get_strikes_list(chain_data: Dict, expiration: str) -> List[float]`** - Get just the strike prices

## Utility Functions

### `resolve_field_priority(data: Dict, field_priority_list: List[str], default=None) -> Any`

Resolves a field value by trying each field in priority order.

**Example:**

```python
data = {'lastPrice': 10.5, 'currentPrice': None}
price = resolve_field_priority(data, ['marketPrice', 'lastPrice', 'currentPrice'])
# Returns: 10.5
```

### `resolve_nested_field_priority(data: Dict, field_paths: List[str], default=None) -> Any`

Resolves nested field values using dot notation.

**Example:**

```python
data = {
    'instrument': {'symbol': 'AAPL'},
    'symbol': 'FALLBACK'
}
symbol = resolve_nested_field_priority(data, ['instrument.symbol', 'symbol'])
# Returns: 'AAPL'
```

## Error Handling

All transformers handle missing or invalid data gracefully:

- **Missing fields**: Use fallback values or defaults
- **Invalid types**: Skip and try next priority
- **Negative prices**: Convert to absolute value (Schwab returns negative for short positions)
- **Missing symbols**: Raise `ValueError` in `transform_position_to_trade`

## Testing

The module includes comprehensive unit tests with 96 test cases covering:

- Long and short position handling
- Field priority resolution
- Edge cases (missing data, invalid formats)
- Multiple account types
- Option chain structures
- Nested field extraction

Run tests:

```bash
cd /home/pham_danny_t/schwab-core
python -m pytest tests/test_transformers_*.py -v
```

## Test Coverage

- **Utils**: 20 tests (field resolution, nested paths)
- **Positions**: 38 tests (quantity, symbol, prices, P&L)
- **Accounts**: 18 tests (account parsing, ID extraction, balances)
- **Option Chains**: 20 tests (strikes, expirations, contracts)

**Total**: 96 tests, 100% passing ✓

## Module Structure

```
schwab-core/transformers/
├── __init__.py          # Public API exports
├── positions.py         # Position → Trade transformers
├── accounts.py          # Account response parsers
├── option_chain.py      # Option chain extractors
└── utils.py            # Field resolution utilities
```

## Source Attribution

This module was extracted from the finimal codebase:

- `positions.py`: From `finimal/app/services/trade_service.py` (lines 513-775)
- `accounts.py`: From `finimal/app/routes/accounts_routes.py` (lines 103-193)
- `option_chain.py`: From `finimal/app/services/gamma_calculation_service.py` (lines 689-736)

## Dependencies

- Python 3.8+
- No external dependencies (uses stdlib only)
- pytest (for running tests)

## Contributing

When adding new transformers:

1. Follow field priority patterns
2. Handle missing/invalid data gracefully
3. Add comprehensive unit tests
4. Document field priority rules
5. Use type hints and docstrings

## License

Part of the schwab-core package. See main project LICENSE.
