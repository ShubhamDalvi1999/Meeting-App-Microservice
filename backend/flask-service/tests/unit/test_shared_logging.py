"""
Tests for shared logging functionality.
"""

import json
import logging
import pytest
from meeting_shared.shared_logging import JSONFormatter, RequestIDLogFilter

def test_json_formatter():
    """Test that JSONFormatter formats logs correctly."""
    formatter = JSONFormatter(service_name="test-service")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Format the record
    formatted = formatter.format(record)
    log_data = json.loads(formatted)
    
    # Verify required fields
    assert log_data['service'] == "test-service"
    assert log_data['level'] == "INFO"
    assert log_data['message'] == "Test message"
    assert 'timestamp' in log_data
    assert log_data['logger'] == "test"

def test_json_formatter_with_exception():
    """Test that JSONFormatter handles exceptions correctly."""
    formatter = JSONFormatter(service_name="test-service")
    try:
        raise ValueError("Test error")
    except ValueError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=True
        )
    
    # Format the record
    formatted = formatter.format(record)
    log_data = json.loads(formatted)
    
    # Verify exception info
    assert 'exception' in log_data
    assert log_data['exception']['type'] == "ValueError"
    assert log_data['exception']['message'] == "Test error"

def test_request_id_filter(app):
    """Test that RequestIDLogFilter adds request context."""
    with app.test_request_context('/test', 
                                headers={'X-Request-ID': 'test-123',
                                       'X-Correlation-ID': 'corr-123'}):
        filter = RequestIDLogFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Apply filter
        filter.filter(record)
        
        # Verify request context
        assert record.request_id == "test-123"
        assert record.correlation_id == "corr-123"
        assert record.path == "/test"
        assert record.method == "GET"

def test_request_id_filter_no_context():
    """Test that RequestIDLogFilter handles missing request context."""
    filter = RequestIDLogFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Apply filter
    filter.filter(record)
    
    # Verify default values
    assert record.request_id == "no_request_id"
    assert record.correlation_id == "no_correlation_id"
    assert record.path == "/"
    assert record.method == "NONE" 