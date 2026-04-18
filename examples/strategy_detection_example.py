#!/usr/bin/env python3
"""
Example usage of strategy detection module

This demonstrates how to use the schwab-core strategy detection
to identify multi-leg options strategies.
"""

from datetime import datetime
from strategy import detect_strategies, detect_strategy_from_legs


def example_vertical_spread():
    """Example: Detecting a Long Put Spread"""
    print("=" * 60)
    print("Example 1: Long Put Spread Detection")
    print("=" * 60)
    
    positions = [
        {
            'symbol': 'SPY_240115P450',
            'underlying_symbol': 'SPY',
            'option_type': 'PUT',
            'strike': 450,
            'side': 'BUY',
            'quantity': 1,
            'expiration': '240115',
            'entry_price': 5.0,  # $5 per share = $500 per contract
            'entry_time': datetime(2024, 1, 15, 10, 0, 0)
        },
        {
            'symbol': 'SPY_240115P445',
            'underlying_symbol': 'SPY',
            'option_type': 'PUT',
            'strike': 445,
            'side': 'SELL',
            'quantity': 1,
            'expiration': '240115',
            'entry_price': 3.0,  # $3 per share = $300 per contract
            'entry_time': datetime(2024, 1, 15, 10, 0, 0)
        }
    ]
    
    strategies = detect_strategies(positions)
    
    for strat in strategies:
        print(f"\n✅ Detected: {strat['strategy_type']}")
        print(f"   Confidence: {strat['confidence']:.1%}")
        print(f"   Strikes: {strat['strikes']}")
        print(f"   Net Debit: ${strat['net_debit_credit']:.2f} (per share)")
        print(f"   Max Profit: ${strat['max_profit']:.2f} (per share)")
        print(f"   Max Loss: ${strat['max_loss']:.2f} (per share)")
        print(f"   Risk/Reward: {strat['risk_reward_ratio']:.2f}")
        print(f"   Notes: {strat['notes']}")


def example_iron_butterfly():
    """Example: Detecting an Iron Butterfly"""
    print("\n" + "=" * 60)
    print("Example 2: Iron Butterfly Detection")
    print("=" * 60)
    
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    positions = [
        {
            'symbol': 'SPY_240115P450',
            'underlying_symbol': 'SPY',
            'option_type': 'PUT',
            'strike': 450,
            'side': 'BUY',
            'quantity': 1,
            'expiration': '240115',
            'entry_price': 20.0,
            'entry_time': base_time
        },
        {
            'symbol': 'SPY_240115P500',
            'underlying_symbol': 'SPY',
            'option_type': 'PUT',
            'strike': 500,
            'side': 'SELL',
            'quantity': 1,
            'expiration': '240115',
            'entry_price': 50.0,
            'entry_time': base_time
        },
        {
            'symbol': 'SPY_240115C500',
            'underlying_symbol': 'SPY',
            'option_type': 'CALL',
            'strike': 500,
            'side': 'SELL',
            'quantity': 1,
            'expiration': '240115',
            'entry_price': 50.0,
            'entry_time': base_time
        },
        {
            'symbol': 'SPY_240115C550',
            'underlying_symbol': 'SPY',
            'option_type': 'CALL',
            'strike': 550,
            'side': 'BUY',
            'quantity': 1,
            'expiration': '240115',
            'entry_price': 20.0,
            'entry_time': base_time
        }
    ]
    
    strategies = detect_strategies(positions)
    
    for strat in strategies:
        print(f"\n✅ Detected: {strat['strategy_type']}")
        print(f"   Confidence: {strat['confidence']:.1%}")
        print(f"   Center Strike: ${strat['center_strike']:.2f}")
        print(f"   Wing Width: ${strat['wing_width']:.2f}")
        print(f"   Max Profit: ${strat['max_profit']:.2f}")
        print(f"   Max Loss: ${strat['max_loss']:.2f}")
        print(f"   Breakevens: ${strat['breakeven_low']:.2f} - ${strat['breakeven_high']:.2f}")
        print(f"   Notes: {strat['notes']}")


def example_multiple_strategies():
    """Example: Detecting multiple strategies on different underlyings"""
    print("\n" + "=" * 60)
    print("Example 3: Multiple Strategies Detection")
    print("=" * 60)
    
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    positions = [
        # SPY Long Put Spread
        {
            'symbol': 'SPY_240115P450',
            'underlying_symbol': 'SPY',
            'option_type': 'PUT',
            'strike': 450,
            'side': 'BUY',
            'quantity': 1,
            'expiration': '240115',
            'entry_time': base_time
        },
        {
            'symbol': 'SPY_240115P445',
            'underlying_symbol': 'SPY',
            'option_type': 'PUT',
            'strike': 445,
            'side': 'SELL',
            'quantity': 1,
            'expiration': '240115',
            'entry_time': base_time
        },
        # AAPL Long Call Spread
        {
            'symbol': 'AAPL_240115C180',
            'underlying_symbol': 'AAPL',
            'option_type': 'CALL',
            'strike': 180,
            'side': 'BUY',
            'quantity': 1,
            'expiration': '240115',
            'entry_time': base_time
        },
        {
            'symbol': 'AAPL_240115C185',
            'underlying_symbol': 'AAPL',
            'option_type': 'CALL',
            'strike': 185,
            'side': 'SELL',
            'quantity': 1,
            'expiration': '240115',
            'entry_time': base_time
        }
    ]
    
    strategies = detect_strategies(positions)
    
    print(f"\n📊 Detected {len(strategies)} strategies:")
    for i, strat in enumerate(strategies, 1):
        print(f"\n{i}. {strat['strategy_type']}")
        print(f"   Underlying: {strat['underlying']}")
        print(f"   Expiration: {strat['expiration']}")
        print(f"   Confidence: {strat['confidence']:.1%}")
        print(f"   Legs: {len(strat['legs'])}")


def example_direct_detection():
    """Example: Direct detection from specific legs"""
    print("\n" + "=" * 60)
    print("Example 4: Direct Detection from Legs")
    print("=" * 60)
    
    legs = [
        {
            'option_type': 'CALL',
            'strike': 460,
            'side': 'BUY',
            'quantity': 1,
            'entry_price': 6.0  # $6 per share
        },
        {
            'option_type': 'CALL',
            'strike': 465,
            'side': 'SELL',
            'quantity': 1,
            'entry_price': 4.0  # $4 per share
        }
    ]
    
    strategy = detect_strategy_from_legs(legs)
    
    if strategy:
        print(f"\n✅ Detected: {strategy['strategy_type']}")
        print(f"   Confidence: {strategy['confidence']:.1%}")
        print(f"   Max Profit: ${strategy['max_profit']:.2f} (per share)")
        print(f"   Max Loss: ${strategy['max_loss']:.2f} (per share)")
    else:
        print("\n❌ No strategy detected")


if __name__ == '__main__':
    print("\n🎯 Strategy Detection Examples\n")
    
    example_vertical_spread()
    example_iron_butterfly()
    example_multiple_strategies()
    example_direct_detection()
    
    print("\n" + "=" * 60)
    print("✨ All examples completed successfully!")
    print("=" * 60 + "\n")
