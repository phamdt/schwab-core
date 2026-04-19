# P&L Calculator API Reference

Quick reference for using the P&L calculator module.

## Installation

```bash
pip install -e /path/to/schwab_core
```

## Functions

### 1. `calculate_intrinsic_value(strike, underlying_price, option_type)`

Calculate intrinsic value of an option.

**Parameters:**
- `strike` (float): Strike price
- `underlying_price` (float): Current underlying price
- `option_type` (str): 'call' or 'put' (case-insensitive)

**Returns:** `float` - Intrinsic value (always >= 0)

**Example:**
```python
from schwab_core.calculations import calculate_intrinsic_value

intrinsic = calculate_intrinsic_value(100, 105, 'call')  # 5.0
intrinsic = calculate_intrinsic_value(100, 95, 'put')    # 5.0
```

---

### 2. `calculate_option_pnl(leg, underlying_price, calculation_type='expiration')`

Calculate P&L for a single option leg.

**Parameters:**
- `leg` (Dict): Option leg with keys:
  - `strike` (float): Strike price
  - `type` (str): 'call' or 'put'
  - `side` (str): 'long', 'short', 'buy', or 'sell'
  - `quantity` (int): Number of contracts
  - `price` (float): Premium (ALWAYS positive)
  - `groupId` (str, optional): Group identifier
- `underlying_price` (float): Current underlying price
- `calculation_type` (str): 'expiration' (default) or 'current'

**Returns:** `Dict` with keys:
- `pnl` (float): Profit/loss in dollars
- `intrinsic_value` (float): Intrinsic value per share
- `premium_value` (float): Premium per share
- `strike`, `type`, `side`, `quantity`: Passthrough fields

**Example:**
```python
from schwab_core.calculations import calculate_option_pnl

leg = {
    'strike': 100,
    'type': 'call',
    'side': 'long',
    'quantity': 1,
    'price': 5
}

result = calculate_option_pnl(leg, 110)
print(f"P&L: ${result['pnl']}")              # P&L: $500.0
print(f"Intrinsic: ${result['intrinsic_value']}")  # Intrinsic: $10.0
```

---

### 3. `calculate_strategy_pnl(legs, underlying_price, calculation_type='expiration')`

Calculate P&L for multi-leg strategy.

**Parameters:**
- `legs` (List[Dict]): List of option legs (see `calculate_option_pnl` for leg format)
- `underlying_price` (float): Current underlying price
- `calculation_type` (str): 'expiration' (default) or 'current'

**Returns:** `Dict` with keys:
- `total_pnl` (float): Sum of all leg P&Ls
- `leg_pnls` (List[Dict]): Individual leg P&L results
- `subgroups` (Dict[str, float]): P&L by groupId
- `underlying_price` (float): Price at which P&L was calculated

**Example:**
```python
from schwab_core.calculations import calculate_strategy_pnl

# Bull call spread
legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
    {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
]

result = calculate_strategy_pnl(legs, 105)
print(f"Total P&L: ${result['total_pnl']}")  # Total P&L: $200.0

# Access individual leg results
for leg_pnl in result['leg_pnls']:
    print(f"{leg_pnl['side']} {leg_pnl['type']} {leg_pnl['strike']}: ${leg_pnl['pnl']}")
```

---

### 4. `calculate_breakeven_prices(legs)`

Calculate breakeven points for a strategy.

**Parameters:**
- `legs` (List[Dict]): List of option legs

**Returns:** `List[float]` - Sorted list of breakeven prices

**Example:**
```python
from schwab_core.calculations import calculate_breakeven_prices

legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
    {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
]

breakevens = calculate_breakeven_prices(legs)
print(f"Breakeven: ${breakevens[0]}")  # Breakeven: $103.0
```

---

### 5. `calculate_max_profit_loss(legs)`

Calculate maximum profit and loss for a strategy.

**Parameters:**
- `legs` (List[Dict]): List of option legs

**Returns:** `Dict` with keys:
- `max_profit` (float or None): Maximum profit (None if unlimited)
- `max_profit_price` (float or None): Price at max profit
- `max_loss` (float or None): Maximum loss (None if unlimited)
- `max_loss_price` (float or None): Price at max loss

**Example:**
```python
from schwab_core.calculations import calculate_max_profit_loss

legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
    {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
]

result = calculate_max_profit_loss(legs)
print(f"Max Profit: ${result['max_profit']}")   # Max Profit: $700.0
print(f"Max Loss: ${result['max_loss']}")       # Max Loss: $-300.0
```

---

## Common Strategies

### Long Call
```python
legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5}
]
```

### Long Put
```python
legs = [
    {'strike': 100, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 5}
]
```

### Bull Call Spread
```python
legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
    {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2}
]
```

### Bear Put Spread
```python
legs = [
    {'strike': 100, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 5},
    {'strike': 90, 'type': 'put', 'side': 'short', 'quantity': 1, 'price': 2}
]
```

### Iron Condor
```python
legs = [
    {'strike': 90, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 1},
    {'strike': 95, 'type': 'put', 'side': 'short', 'quantity': 1, 'price': 3},
    {'strike': 105, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 3},
    {'strike': 110, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 1}
]
```

### Straddle
```python
legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
    {'strike': 100, 'type': 'put', 'side': 'long', 'quantity': 1, 'price': 5}
]
```

---

## Constants

```python
from schwab_core.utils.constants import (
    CONTRACT_MULTIPLIER,      # 100
    PRICE_PRECISION,          # 2 decimal places
    PNL_PRECISION,            # 2 decimal places
)
```

---

## Error Handling

All functions validate inputs and raise appropriate errors:

- `ValueError`: Missing required fields, invalid option type, invalid strike, invalid side
- Warnings logged for: Negative premium (auto-corrected), invalid quantity

---

## Important Notes

1. **Premium Convention**: ALWAYS use positive premiums
   - Long: premium = amount you PAID (debit)
   - Short: premium = amount you RECEIVED (credit)

2. **Side Normalization**: 'buy' → 'long', 'sell' → 'short'

3. **Contract Multiplier**: All P&L values are automatically multiplied by 100 (standard contract size)

4. **Calculation Type**: Currently only 'expiration' is fully supported (uses intrinsic value)

5. **Precision**: All results rounded to 2 decimal places for prices and P&L
