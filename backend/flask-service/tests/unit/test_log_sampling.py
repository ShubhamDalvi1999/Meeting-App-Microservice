"""
Unit tests for log sampling functionality.
"""

import pytest
import logging
import random
from meeting_shared.shared_logging.sampling import (
    SamplingConfig, 
    LogSampler, 
    SamplingLogFilter,
    configure_sampling,
    should_log
)

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.logging]

class TestSamplingConfig:
    """Tests for the SamplingConfig class."""
    
    def test_default_config(self):
        """Test default sampling configuration."""
        config = SamplingConfig()
        assert config.default_rate == 1.0
        assert config.path_rates == {}
        assert config.method_rates == {}
        assert config.level_rates == {}
    
    def test_custom_rates(self):
        """Test custom sampling rates."""
        config = SamplingConfig(
            default_rate=0.5,
            path_rates={
                r'^/api/health': 0.1,
                r'^/api/metrics': 0.2
            },
            method_rates={
                'GET': 0.3,
                'POST': 0.4
            },
            level_rates={
                'DEBUG': 0.1,
                'INFO': 0.5,
                'ERROR': 1.0
            }
        )
        
        assert config.default_rate == 0.5
        assert len(config.path_patterns) == 2
        assert config.method_rates['GET'] == 0.3
        assert config.method_rates['POST'] == 0.4
        
        # Test level normalization
        assert logging.DEBUG in config.level_rates
        assert logging.INFO in config.level_rates
        assert logging.ERROR in config.level_rates
    
    def test_rate_bounds(self):
        """Test that rates are bounded between 0 and 1."""
        config = SamplingConfig(
            default_rate=2.0,  # Should be capped at 1.0
            path_rates={
                r'^/api/test': -0.5  # Should be floored at 0.0
            }
        )
        
        assert config.default_rate == 1.0
        assert config.get_rate_for_path('/api/test') == 0.0
    
    def test_get_rate_for_path(self):
        """Test getting sampling rate for a path."""
        config = SamplingConfig(
            default_rate=0.5,
            path_rates={
                r'^/api/health': 0.1,
                r'^/api/users/\d+': 0.2
            }
        )
        
        assert config.get_rate_for_path('/api/health') == 0.1
        assert config.get_rate_for_path('/api/health/check') == 0.1
        assert config.get_rate_for_path('/api/users/123') == 0.2
        assert config.get_rate_for_path('/api/other') == 0.5
    
    def test_get_rate_for_method(self):
        """Test getting sampling rate for an HTTP method."""
        config = SamplingConfig(
            default_rate=0.5,
            method_rates={
                'GET': 0.3,
                'POST': 0.4
            }
        )
        
        assert config.get_rate_for_method('GET') == 0.3
        assert config.get_rate_for_method('get') == 0.3
        assert config.get_rate_for_method('POST') == 0.4
        assert config.get_rate_for_method('DELETE') == 0.5
    
    def test_get_rate_for_level(self):
        """Test getting sampling rate for a log level."""
        config = SamplingConfig(
            default_rate=0.5,
            level_rates={
                'DEBUG': 0.1,
                'INFO': 0.5,
                logging.ERROR: 1.0
            }
        )
        
        assert config.get_rate_for_level('DEBUG') == 0.1
        assert config.get_rate_for_level(logging.DEBUG) == 0.1
        assert config.get_rate_for_level('INFO') == 0.5
        assert config.get_rate_for_level(logging.ERROR) == 1.0
        assert config.get_rate_for_level('WARNING') == 0.5


class TestLogSampler:
    """Tests for the LogSampler class."""
    
    def test_default_sampler(self):
        """Test default log sampler."""
        sampler = LogSampler()
        assert sampler.config.default_rate == 1.0
        
        # Default sampler should log everything
        assert sampler.should_log()
    
    def test_custom_sampler(self):
        """Test custom log sampler."""
        config = SamplingConfig(
            default_rate=0.5,
            path_rates={
                r'^/api/health': 0.1
            }
        )
        sampler = LogSampler(config)
        
        # Test with path
        assert sampler.should_log(path='/api/other') != sampler.should_log(path='/api/health')
    
    def test_deterministic_sampling(self):
        """Test that sampling is deterministic for the same inputs."""
        sampler = LogSampler(SamplingConfig(default_rate=0.5))
        
        # Same inputs should give same results
        path = '/api/test'
        method = 'GET'
        level = logging.INFO
        
        result1 = sampler.should_log(path, method, level)
        result2 = sampler.should_log(path, method, level)
        
        # First two calls with same parameters should have same result
        # (because count is 1, then 2, and both 1 and 2 have same result with rate=0.5)
        assert result1 == result2
        
        # Third call might be different because count is now 3
        result3 = sampler.should_log(path, method, level)
        
        # Different inputs should potentially give different results
        different_path = '/api/other'
        assert sampler.should_log(different_path, method, level) != sampler.should_log(path, method, level)


class TestSamplingLogFilter:
    """Tests for the SamplingLogFilter class."""
    
    def test_filter(self):
        """Test filtering log records."""
        config = SamplingConfig(
            default_rate=0.5,
            path_rates={
                r'^/api/health': 0.1
            },
            level_rates={
                'DEBUG': 0.1,
                'ERROR': 1.0
            }
        )
        sampler = LogSampler(config)
        filter = SamplingLogFilter(sampler)
        
        # Create a record with path
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.path = '/api/health'
        
        # Filter should use the sampler
        assert filter.filter(record) == sampler.should_log(path='/api/health', level=logging.INFO)
        
        # Error records should always be logged
        error_record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error message',
            args=(),
            exc_info=None
        )
        error_record.path = '/api/health'
        
        assert filter.filter(error_record) == True


class TestGlobalFunctions:
    """Tests for global sampling functions."""
    
    def test_configure_sampling(self):
        """Test configuring the default sampler."""
        # Create a deterministic test
        config = SamplingConfig(default_rate=0.0)  # Never log
        configure_sampling(config)
        assert should_log() == False
        
        # Reset to default
        configure_sampling(SamplingConfig(default_rate=1.0))  # Always log
        assert should_log() == True 