"""
Example usage of schwab-core transformers.

This script demonstrates how to use the data transformers to parse
Schwab API responses into standardized formats.
"""
import sys
from pathlib import Path

# Add parent directory to path for schwab_core imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from schwab_core.transformers import (
    transform_position_to_trade,
    parse_account_response,
    extract_option_chain_strikes,
    extract_expirations,
    parse_expiration_string,
)


def example_position_transform():
    """Example: Transform position data to trade."""
    print("\n=== Position → Trade Transformation ===\n")
    
    # Example equity position
    equity_position = {
        'instrument': {
            'symbol': 'AAPL',
            'assetType': 'EQUITY',
            'description': 'Apple Inc.'
        },
        'longQuantity': 100,
        'shortQuantity': 0,
        'averagePrice': 150.0,
        'marketPrice': 155.0,
        'marketValue': 15500.0,
        'totalPnL': 500.0
    }
    
    trade = transform_position_to_trade(equity_position)
    print(f"Symbol: {trade['symbol']}")
    print(f"Quantity: {trade['quantity']}")
    print(f"Entry Price: ${trade['entry_price']:.2f}")
    print(f"Current Price: ${trade['current_price']:.2f}")
    print(f"Profit: ${trade['profit']:.2f}")
    print(f"Market Value: ${trade['market_value']:.2f}")
    
    # Example option position
    print("\n--- Option Position ---\n")
    option_position = {
        'instrument': {
            'symbol': 'AAPL250117C00150000',
            'assetType': 'OPTION',
            'description': 'AAPL 01/17/25 $150 Call',
            'underlyingSymbol': 'AAPL'
        },
        'longQuantity': 10,
        'shortQuantity': 0,
        'averagePrice': 3.50,
        'marketPrice': 5.00,
        'marketValue': 5000.0
    }
    
    option_trade = transform_position_to_trade(option_position)
    print(f"Symbol: {option_trade['symbol']}")
    print(f"Underlying: {option_trade['underlying_symbol']}")
    print(f"Contracts: {option_trade['quantity']}")
    print(f"Entry Price: ${option_trade['entry_price']:.2f}")
    print(f"Current Price: ${option_trade['current_price']:.2f}")
    print(f"Profit: ${option_trade['profit']:.2f}")


def example_account_parse():
    """Example: Parse account response."""
    print("\n\n=== Account Response Parsing ===\n")
    
    schwab_response = [
        {
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
        },
        {
            'securitiesAccount': {
                'accountNumber': '87654321',
                'type': 'CASH',
                'currentBalances': {
                    'cashBalance': 5000.0,
                    'availableFunds': 5000.0,
                    'buyingPower': 5000.0,
                    'liquidationValue': 5000.0
                },
                'initialBalances': {
                    'availableFundsNonMarginableTrade': 5000.0
                }
            }
        }
    ]
    
    accounts = parse_account_response(schwab_response)
    
    for account in accounts:
        print(f"Account ID: {account['account_id']}")
        print(f"Type: {account['account_type']}")
        print(f"  Cash Balance: ${account['balances']['cash_balance']:,.2f}")
        print(f"  Buying Power: ${account['balances']['buying_power']:,.2f}")
        print(f"  Total Balance: ${account['balances']['total_balance']:,.2f}")
        print()


def example_option_chain():
    """Example: Extract option chain strikes."""
    print("\n=== Option Chain Extraction ===\n")
    
    chain_data = {
        'callExpDateMap': {
            '2025-01-17:0': {
                '145.0': [{'symbol': 'AAPL250117C00145000', 'bid': 10.5, 'ask': 10.7}],
                '150.0': [{'symbol': 'AAPL250117C00150000', 'bid': 7.0, 'ask': 7.2}],
                '155.0': [{'symbol': 'AAPL250117C00155000', 'bid': 4.5, 'ask': 4.7}]
            },
            '2025-02-21:35': {
                '145.0': [{'symbol': 'AAPL250221C00145000', 'bid': 12.0, 'ask': 12.3}],
                '150.0': [{'symbol': 'AAPL250221C00150000', 'bid': 9.0, 'ask': 9.3}]
            }
        },
        'putExpDateMap': {
            '2025-01-17:0': {
                '145.0': [{'symbol': 'AAPL250117P00145000', 'bid': 2.0, 'ask': 2.2}],
                '150.0': [{'symbol': 'AAPL250117P00150000', 'bid': 4.5, 'ask': 4.7}],
                '155.0': [{'symbol': 'AAPL250117P00155000', 'bid': 7.5, 'ask': 7.8}]
            },
            '2025-02-21:35': {
                '145.0': [{'symbol': 'AAPL250221P00145000', 'bid': 3.5, 'ask': 3.8}],
                '150.0': [{'symbol': 'AAPL250221P00150000', 'bid': 6.0, 'ask': 6.3}]
            }
        }
    }
    
    # Get all expirations
    expirations = extract_expirations(chain_data)
    print(f"Available Expirations: {expirations}\n")
    
    # Parse expiration info
    for exp in expirations:
        exp_info = parse_expiration_string(exp)
        print(f"Expiration: {exp_info['date']} ({exp_info['dte']} DTE)")
    
    print("\n--- Strikes for 2025-01-17 ---\n")
    
    # Extract strikes for specific expiration
    strikes = extract_option_chain_strikes(chain_data, '2025-01-17:0')
    
    print(f"{'Strike':<10} {'Call Bid':<10} {'Put Bid':<10}")
    print("-" * 30)
    for strike_data in strikes:
        strike = strike_data['strike']
        call_bid = strike_data['call_contracts'][0]['bid'] if strike_data['call_contracts'] else 0
        put_bid = strike_data['put_contracts'][0]['bid'] if strike_data['put_contracts'] else 0
        print(f"${strike:<9.2f} ${call_bid:<9.2f} ${put_bid:<9.2f}")


def example_short_position():
    """Example: Handle short position."""
    print("\n\n=== Short Position Handling ===\n")
    
    short_position = {
        'instrument': {
            'symbol': 'TSLA',
            'assetType': 'EQUITY'
        },
        'longQuantity': 0,
        'shortQuantity': 50,
        'averagePrice': 200.0,
        'marketPrice': 190.0,
        'marketValue': -9500.0
    }
    
    trade = transform_position_to_trade(short_position)
    print(f"Symbol: {trade['symbol']}")
    print(f"Quantity: {trade['quantity']} (negative = short)")
    print(f"Entry Price: ${trade['entry_price']:.2f}")
    print(f"Current Price: ${trade['current_price']:.2f}")
    print(f"Profit: ${trade['profit']:.2f} (price dropped = profit)")


if __name__ == '__main__':
    print("=" * 60)
    print("Schwab Core Transformers - Usage Examples")
    print("=" * 60)
    
    example_position_transform()
    example_account_parse()
    example_option_chain()
    example_short_position()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)
