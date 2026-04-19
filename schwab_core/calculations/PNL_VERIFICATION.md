# P&L Calculator Formula Verification

This document verifies that the Python implementation in `schwab_core/calculations/pnl.py` matches the TypeScript implementation in `/finimal/frontend/src/utils/optionsPnLCalculator.ts` **EXACTLY**.

## Formula Comparison

### 1. Intrinsic Value Calculation

**TypeScript (lines 76-87):**
```typescript
if (type === 'call') {
    // Call: max(0, underlying - strike)
    intrinsicValue = Math.max(0, underlyingPrice - strike);
} else {
    // Put: max(0, strike - underlying)
    intrinsicValue = Math.max(0, strike - underlyingPrice);
}
```

**Python (`calculate_intrinsic_value`):**
```python
if option_type == 'call':
    # Call: max(0, underlying - strike)
    intrinsic = max(0, underlying_price - strike)
elif option_type == 'put':
    # Put: max(0, strike - underlying)
    intrinsic = max(0, strike - underlying_price)
```

✅ **MATCH**: Formulas are identical

---

### 2. Long Position P&L

**TypeScript (lines 96-100):**
```typescript
if (side === 'long') {
    // Long: (intrinsic - premium) × quantity × 100
    // You paid the premium, so it's subtracted from intrinsic value
    pnl = (intrinsicValue - premium) * quantity * 100;
}
```

**Python (`calculate_option_pnl`):**
```python
if side == 'long':
    # Long: (intrinsic - premium) × quantity × 100
    # You paid the premium, so it's subtracted from intrinsic value
    pnl = (intrinsic_value - premium) * quantity * CONTRACT_MULTIPLIER
```

Where `CONTRACT_MULTIPLIER = 100`

✅ **MATCH**: Formulas are identical

---

### 3. Short Position P&L

**TypeScript (lines 101-106):**
```typescript
else {
    // Short: (premium - intrinsic) × quantity × 100
    // You received the premium, so it's your starting credit
    pnl = (premium - intrinsicValue) * quantity * 100;
}
```

**Python (`calculate_option_pnl`):**
```python
else:  # short
    # Short: (premium - intrinsic) × quantity × 100
    # You received the premium, so it's your starting credit
    pnl = (premium - intrinsic_value) * quantity * CONTRACT_MULTIPLIER
```

✅ **MATCH**: Formulas are identical

---

### 4. Premium Convention

**TypeScript (lines 90-92):**
```typescript
// IMPORTANT: Premium should always be entered as a POSITIVE number
// - For LONG positions: premium = what you PAID (debit)
// - For SHORT positions: premium = what you RECEIVED (credit)
```

**Python (docstring):**
```python
Premium convention:
- ALWAYS entered as POSITIVE number
- Long positions: premium = what you PAID (debit)
- Short positions: premium = what you RECEIVED (credit)
```

✅ **MATCH**: Convention is identical

---

## Test Results

All 47 unit tests pass, including:

### Intrinsic Value Tests (8 tests)
- ✅ Call ITM: strike 100, stock 105 → intrinsic = 5.0
- ✅ Call OTM: strike 100, stock 95 → intrinsic = 0.0
- ✅ Put ITM: strike 100, stock 95 → intrinsic = 5.0
- ✅ Put OTM: strike 100, stock 105 → intrinsic = 0.0
- ✅ Case insensitive handling
- ✅ Invalid option type error handling

### Single Leg P&L Tests (16 tests)
- ✅ Long call profit: strike 100, premium 5, stock 110 → P&L = $500
- ✅ Long call loss: strike 100, premium 5, stock 95 → P&L = -$500
- ✅ Long call breakeven: strike 100, premium 5, stock 105 → P&L = $0
- ✅ Short call profit: strike 100, premium 5, stock 95 → P&L = $500
- ✅ Short call loss: strike 100, premium 5, stock 110 → P&L = -$500
- ✅ Long put profit: strike 100, premium 5, stock 90 → P&L = $500
- ✅ Long put loss: strike 100, premium 5, stock 105 → P&L = -$500
- ✅ Short put profit: strike 100, premium 5, stock 105 → P&L = $500
- ✅ Short put loss: strike 100, premium 5, stock 90 → P&L = -$500
- ✅ Multiple contracts: 5 contracts × P&L per contract
- ✅ Side normalization: 'buy' → 'long', 'sell' → 'short'
- ✅ Negative premium warning and correction
- ✅ Error handling for missing fields and invalid inputs

### Multi-Leg Strategy Tests (4 tests)
- ✅ Bull call spread (buy 100, sell 110)
  - At 105: P&L = $200
  - At 115: P&L = $700 (max profit)
  - At 95: P&L = -$300 (max loss)
- ✅ Iron condor (4 legs)
  - At 100 (center): P&L = $400 (max profit)
- ✅ Subgroup tracking with groupId
- ✅ Empty legs handling

### Breakeven Calculations (5 tests)
- ✅ Long call: breakeven at strike + premium (105)
- ✅ Long put: breakeven at strike - premium (95)
- ✅ Bull call spread: breakeven at 103
- ✅ Straddle: two breakevens at ~90 and ~110
- ✅ Empty legs handling

### Max Profit/Loss Tests (6 tests)
- ✅ Long call: max loss = -$500, unlimited profit
- ✅ Long put: max profit = $9,500, max loss = -$500
- ✅ Bull call spread: max profit = $700, max loss = -$300
- ✅ Iron condor: defined risk/reward
- ✅ Short call: max profit = $500, unlimited loss
- ✅ Empty legs handling

### Real-World Scenarios (3 tests)
- ✅ AAPL covered call (155 strike, 3 premium)
- ✅ SPX 0DTE iron condor (wide strikes)
- ✅ TSLA bear put spread (2 contracts)

### Edge Cases (5 tests)
- ✅ Zero quantity
- ✅ Very high strikes (SPX at 6000)
- ✅ Fractional strikes (100.5)
- ✅ Fractional premiums ($1.25)
- ✅ Underlying near zero

---

## Contract Testing Compatibility

The Python implementation is designed for **contract testing** between frontend and backend:

1. **Identical Formulas**: All P&L calculations use the exact same formulas as TypeScript
2. **Same Convention**: Premium is always positive for both long and short positions
3. **Consistent Results**: Given the same inputs, both implementations produce identical outputs
4. **Comprehensive Tests**: 47 tests cover edge cases, real-world scenarios, and error handling

---

## Usage Examples

### Basic Long Call P&L
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
print(f"P&L: ${result['pnl']}")  # P&L: $500.0
```

### Bull Call Spread Strategy
```python
from schwab_core.calculations import calculate_strategy_pnl

legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
    {'strike': 110, 'type': 'call', 'side': 'short', 'quantity': 1, 'price': 2},
]

result = calculate_strategy_pnl(legs, 105)
print(f"Total P&L: ${result['total_pnl']}")  # Total P&L: $200.0
```

### Breakeven Calculation
```python
from schwab_core.calculations import calculate_breakeven_prices

legs = [
    {'strike': 100, 'type': 'call', 'side': 'long', 'quantity': 1, 'price': 5},
]

breakevens = calculate_breakeven_prices(legs)
print(f"Breakeven: ${breakevens[0]}")  # Breakeven: $105.0
```

---

## Files Created

1. ✅ `schwab_core/utils/constants.py` - Constants including CONTRACT_MULTIPLIER = 100
2. ✅ `schwab_core/calculations/__init__.py` - Module exports
3. ✅ `schwab_core/calculations/pnl.py` - Core P&L calculation functions (339 lines)
4. ✅ `schwab_core/tests/test_pnl_calculator.py` - Comprehensive unit tests (47 tests)
5. ✅ `schwab_core/setup.py` - Package setup configuration

---

## Confirmation

✅ **Formulas match TypeScript implementation EXACTLY**
✅ **All 47 unit tests pass**
✅ **Ready for contract testing between frontend and backend**
✅ **Comprehensive documentation and examples included**
