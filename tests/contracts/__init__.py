"""
Contract Tests for schwab-core Library

This package contains contract tests that verify frontend/backend parity
between the TypeScript frontend and Python backend implementations.

Test Files:
- test_pnl_parity.py: P&L calculation verification (TypeScript vs Python)
- test_position_parity.py: Position classification verification
- test_strategy_parity.py: Strategy detection verification

Usage:
    pytest schwab-core/tests/contracts/        # Run all contract tests
    pytest schwab-core/tests/contracts/test_pnl_parity.py -v    # Run specific test file

Contract Testing Philosophy:
- Each test has an "expected" value from the original implementation
- Tests use real-world values from production data
- Tests include edge cases that caused bugs historically
- Tests MUST fail if formulas diverge between implementations

Author: Contract Testing Suite
Date: 2026-04-05
"""

__all__ = [
    "test_pnl_parity",
    "test_position_parity",
    "test_strategy_parity",
]
