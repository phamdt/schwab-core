"""
Unit tests for option chain transformers.
"""

import pytest
from schwab_core.transformers.option_chain import (
    extract_option_chain_strikes,
    extract_expirations,
    parse_expiration_string,
    get_strikes_list,
)


class TestExtractOptionChainStrikes:
    """Tests for extract_option_chain_strikes function."""
    
    def test_complete_chain_data(self):
        """Test extraction with complete call and put data."""
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
                    '105.0': [{'symbol': 'AAPL250117P00105000', 'bid': 4.0}],
                    '110.0': [{'symbol': 'AAPL250117P00110000', 'bid': 6.0}]
                }
            }
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 3
        assert result[0]['strike'] == 100.0
        assert result[1]['strike'] == 105.0
        assert result[2]['strike'] == 110.0
        
        # Check call contracts
        assert len(result[0]['call_contracts']) == 1
        assert result[0]['call_contracts'][0]['symbol'] == 'AAPL250117C00100000'
        
        # Check put contracts
        assert len(result[0]['put_contracts']) == 1
        assert result[0]['put_contracts'][0]['symbol'] == 'AAPL250117P00100000'
        
        # Check strike with only puts
        assert len(result[2]['call_contracts']) == 0
        assert len(result[2]['put_contracts']) == 1
    
    def test_only_calls(self):
        """Test extraction with only call contracts."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '150.0': [{'symbol': 'AAPL250117C00150000'}]
                }
            },
            'putExpDateMap': {}
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 1
        assert result[0]['strike'] == 150.0
        assert len(result[0]['call_contracts']) == 1
        assert len(result[0]['put_contracts']) == 0
    
    def test_only_puts(self):
        """Test extraction with only put contracts."""
        chain_data = {
            'callExpDateMap': {},
            'putExpDateMap': {
                '2025-01-17:0': {
                    '150.0': [{'symbol': 'AAPL250117P00150000'}]
                }
            }
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 1
        assert result[0]['strike'] == 150.0
        assert len(result[0]['call_contracts']) == 0
        assert len(result[0]['put_contracts']) == 1
    
    def test_wrong_expiration(self):
        """Test extraction with non-existent expiration."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '100.0': [{'symbol': 'AAPL250117C00100000'}]
                }
            },
            'putExpDateMap': {}
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-02-17:0')
        
        assert len(result) == 0
    
    def test_invalid_strike_ignored(self):
        """Test that invalid strike strings are ignored."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '100.0': [{'symbol': 'AAPL250117C00100000'}],
                    'invalid': [{'symbol': 'INVALID'}],
                    '105.0': [{'symbol': 'AAPL250117C00105000'}]
                }
            },
            'putExpDateMap': {}
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 2
        assert result[0]['strike'] == 100.0
        assert result[1]['strike'] == 105.0
    
    def test_negative_strike_ignored(self):
        """Test that negative strikes are ignored."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '100.0': [{'symbol': 'AAPL250117C00100000'}],
                    '-50.0': [{'symbol': 'INVALID'}]
                }
            },
            'putExpDateMap': {}
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 1
        assert result[0]['strike'] == 100.0
    
    def test_strikes_sorted(self):
        """Test that strikes are returned in sorted order."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '110.0': [{'symbol': 'C110'}],
                    '100.0': [{'symbol': 'C100'}],
                    '105.0': [{'symbol': 'C105'}]
                }
            },
            'putExpDateMap': {}
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 3
        assert result[0]['strike'] == 100.0
        assert result[1]['strike'] == 105.0
        assert result[2]['strike'] == 110.0
    
    def test_duplicate_strikes_merged(self):
        """Test that duplicate strikes from calls/puts are merged."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '100.0': [{'symbol': 'C100'}]
                }
            },
            'putExpDateMap': {
                '2025-01-17:0': {
                    '100.0': [{'symbol': 'P100'}]
                }
            }
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 1
        assert result[0]['strike'] == 100.0
        assert len(result[0]['call_contracts']) == 1
        assert len(result[0]['put_contracts']) == 1
    
    def test_empty_chain_data(self):
        """Test handling of empty chain data."""
        chain_data = {
            'callExpDateMap': {},
            'putExpDateMap': {}
        }
        
        result = extract_option_chain_strikes(chain_data, '2025-01-17:0')
        
        assert len(result) == 0


class TestExtractExpirations:
    """Tests for extract_expirations function."""
    
    def test_multiple_expirations(self):
        """Test extraction of multiple expirations."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {},
                '2025-02-21:35': {}
            },
            'putExpDateMap': {
                '2025-01-17:0': {},
                '2025-03-21:63': {}
            }
        }
        
        expirations = extract_expirations(chain_data)
        
        assert len(expirations) == 3
        assert '2025-01-17:0' in expirations
        assert '2025-02-21:35' in expirations
        assert '2025-03-21:63' in expirations
    
    def test_expirations_sorted(self):
        """Test that expirations are sorted chronologically."""
        chain_data = {
            'callExpDateMap': {
                '2025-03-21:63': {},
                '2025-01-17:0': {},
                '2025-02-21:35': {}
            },
            'putExpDateMap': {}
        }
        
        expirations = extract_expirations(chain_data)
        
        assert expirations == ['2025-01-17:0', '2025-02-21:35', '2025-03-21:63']
    
    def test_duplicates_removed(self):
        """Test that duplicate expirations are removed."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {}
            },
            'putExpDateMap': {
                '2025-01-17:0': {}
            }
        }
        
        expirations = extract_expirations(chain_data)
        
        assert len(expirations) == 1
        assert expirations[0] == '2025-01-17:0'
    
    def test_empty_chain(self):
        """Test handling of empty chain."""
        chain_data = {
            'callExpDateMap': {},
            'putExpDateMap': {}
        }
        
        expirations = extract_expirations(chain_data)
        
        assert len(expirations) == 0


class TestParseExpirationString:
    """Tests for parse_expiration_string function."""
    
    def test_standard_format(self):
        """Test parsing standard expiration format."""
        result = parse_expiration_string('2025-01-17:0')
        
        assert result['date'] == '2025-01-17'
        assert result['dte'] == 0
    
    def test_dte_with_days(self):
        """Test parsing with days to expiration."""
        result = parse_expiration_string('2025-02-21:35')
        
        assert result['date'] == '2025-02-21'
        assert result['dte'] == 35
    
    def test_invalid_format(self):
        """Test handling of invalid format."""
        result = parse_expiration_string('2025-01-17')
        
        assert result['date'] == '2025-01-17'
        assert result['dte'] is None
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = parse_expiration_string('')
        
        assert result['date'] == ''
        assert result['dte'] is None


class TestGetStrikesList:
    """Tests for get_strikes_list function."""
    
    def test_returns_only_strikes(self):
        """Test that only strike prices are returned."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '100.0': [{'symbol': 'C100'}],
                    '105.0': [{'symbol': 'C105'}],
                    '110.0': [{'symbol': 'C110'}]
                }
            },
            'putExpDateMap': {}
        }
        
        strikes = get_strikes_list(chain_data, '2025-01-17:0')
        
        assert strikes == [100.0, 105.0, 110.0]
        assert all(isinstance(s, float) for s in strikes)
    
    def test_sorted_strikes(self):
        """Test that strikes are sorted."""
        chain_data = {
            'callExpDateMap': {
                '2025-01-17:0': {
                    '110.0': [{}],
                    '100.0': [{}],
                    '105.0': [{}]
                }
            },
            'putExpDateMap': {}
        }
        
        strikes = get_strikes_list(chain_data, '2025-01-17:0')
        
        assert strikes == [100.0, 105.0, 110.0]
    
    def test_empty_result(self):
        """Test with no strikes."""
        chain_data = {
            'callExpDateMap': {},
            'putExpDateMap': {}
        }
        
        strikes = get_strikes_list(chain_data, '2025-01-17:0')
        
        assert strikes == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
