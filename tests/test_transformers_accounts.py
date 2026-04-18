"""
Unit tests for account transformers.
"""

import pytest
from schwab_core.transformers.accounts import (
    parse_account_response,
    extract_account_id,
    extract_balances,
)


class TestParseAccountResponse:
    """Tests for parse_account_response function."""
    
    def test_standard_securities_account(self):
        """Test parsing standard securitiesAccount wrapper."""
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
            }
        ]
        
        accounts = parse_account_response(schwab_response)
        
        assert len(accounts) == 1
        assert accounts[0]['account_id'] == '12345678'
        assert accounts[0]['account_type'] == 'MARGIN'
        assert accounts[0]['balances']['cash_balance'] == 10000.0
        assert accounts[0]['balances']['available_funds'] == 8000.0
        assert accounts[0]['balances']['buying_power'] == 16000.0
        assert accounts[0]['balances']['total_balance'] == 25000.0
        assert accounts[0]['balances']['available_funds_non_marginable'] == 5000.0
    
    def test_multiple_accounts(self):
        """Test parsing multiple accounts."""
        schwab_response = [
            {
                'securitiesAccount': {
                    'accountNumber': '11111111',
                    'type': 'CASH',
                    'currentBalances': {'cashBalance': 5000.0},
                    'initialBalances': {}
                }
            },
            {
                'securitiesAccount': {
                    'accountNumber': '22222222',
                    'type': 'MARGIN',
                    'currentBalances': {'cashBalance': 10000.0},
                    'initialBalances': {}
                }
            }
        ]
        
        accounts = parse_account_response(schwab_response)
        
        assert len(accounts) == 2
        assert accounts[0]['account_id'] == '11111111'
        assert accounts[1]['account_id'] == '22222222'
    
    def test_account_without_securities_wrapper(self):
        """Test parsing account without securitiesAccount wrapper."""
        schwab_response = [
            {
                'accountNumber': '99999999',
                'type': 'IRA',
                'currentBalances': {'cashBalance': 15000.0},
                'initialBalances': {}
            }
        ]
        
        accounts = parse_account_response(schwab_response)
        
        assert len(accounts) == 1
        assert accounts[0]['account_id'] == '99999999'
        assert accounts[0]['account_type'] == 'IRA'
    
    def test_fallback_account_id_fields(self):
        """Test fallback to accountId when accountNumber missing."""
        schwab_response = [
            {
                'securitiesAccount': {
                    'accountId': 'ACCT-123',
                    'type': 'CASH',
                    'currentBalances': {},
                    'initialBalances': {}
                }
            }
        ]
        
        accounts = parse_account_response(schwab_response)
        
        assert len(accounts) == 1
        assert accounts[0]['account_id'] == 'ACCT-123'
    
    def test_missing_account_id_skips_account(self):
        """Test that accounts without ID are skipped."""
        schwab_response = [
            {
                'securitiesAccount': {
                    'type': 'UNKNOWN',
                    'currentBalances': {},
                    'initialBalances': {}
                }
            }
        ]
        
        accounts = parse_account_response(schwab_response)
        
        assert len(accounts) == 0
    
    def test_missing_balances_defaults_to_zero(self):
        """Test that missing balances default to 0.0."""
        schwab_response = [
            {
                'securitiesAccount': {
                    'accountNumber': '12345678',
                    'type': 'CASH'
                    # No balances provided
                }
            }
        ]
        
        accounts = parse_account_response(schwab_response)
        
        assert accounts[0]['balances']['cash_balance'] == 0.0
        assert accounts[0]['balances']['available_funds'] == 0.0
    
    def test_empty_response(self):
        """Test handling of empty response."""
        schwab_response = []
        
        accounts = parse_account_response(schwab_response)
        
        assert len(accounts) == 0
    
    def test_invalid_response_type(self):
        """Test handling of non-list response."""
        schwab_response = {'error': 'Invalid'}
        
        accounts = parse_account_response(schwab_response)
        
        assert len(accounts) == 0


class TestExtractAccountId:
    """Tests for extract_account_id function."""
    
    def test_account_number(self):
        """Test extraction of accountNumber."""
        account_data = {'accountNumber': '12345678'}
        assert extract_account_id(account_data) == '12345678'
    
    def test_account_id(self):
        """Test extraction of accountId."""
        account_data = {'accountId': 'ACCT-123'}
        assert extract_account_id(account_data) == 'ACCT-123'
    
    def test_id_field(self):
        """Test extraction of id field."""
        account_data = {'id': '999'}
        assert extract_account_id(account_data) == '999'
    
    def test_number_field(self):
        """Test extraction of number field."""
        account_data = {'number': '777'}
        assert extract_account_id(account_data) == '777'
    
    def test_priority_order(self):
        """Test that accountNumber takes priority."""
        account_data = {
            'accountNumber': 'FIRST',
            'accountId': 'SECOND',
            'id': 'THIRD',
            'number': 'FOURTH'
        }
        assert extract_account_id(account_data) == 'FIRST'
    
    def test_missing_all_fields(self):
        """Test handling when no ID fields present."""
        account_data = {'type': 'CASH'}
        assert extract_account_id(account_data) is None


class TestExtractBalances:
    """Tests for extract_balances function."""
    
    def test_complete_balances(self):
        """Test extraction of complete balances."""
        current = {
            'cashBalance': 10000.0,
            'availableFunds': 8000.0,
            'buyingPower': 16000.0,
            'liquidationValue': 25000.0
        }
        initial = {
            'availableFundsNonMarginableTrade': 5000.0
        }
        
        balances = extract_balances(current, initial)
        
        assert balances['cash_balance'] == 10000.0
        assert balances['available_funds'] == 8000.0
        assert balances['buying_power'] == 16000.0
        assert balances['total_balance'] == 25000.0
        assert balances['available_funds_non_marginable'] == 5000.0
    
    def test_none_balances(self):
        """Test handling of None balances."""
        balances = extract_balances(None, None)
        
        assert balances['cash_balance'] == 0.0
        assert balances['available_funds'] == 0.0
        assert balances['buying_power'] == 0.0
        assert balances['total_balance'] == 0.0
        assert balances['available_funds_non_marginable'] == 0.0
    
    def test_empty_balances(self):
        """Test handling of empty balance dicts."""
        balances = extract_balances({}, {})
        
        assert balances['cash_balance'] == 0.0
        assert balances['available_funds'] == 0.0
    
    def test_partial_balances(self):
        """Test handling of partial balances."""
        current = {'cashBalance': 5000.0}
        
        balances = extract_balances(current, None)
        
        assert balances['cash_balance'] == 5000.0
        assert balances['available_funds'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
