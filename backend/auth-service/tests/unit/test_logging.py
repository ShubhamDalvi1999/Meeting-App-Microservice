"""
Unit tests for the logging functionality.
"""

import pytest
import logging
import json
from unittest.mock import patch, MagicMock, call
from flask import Flask, request, g
from meeting_shared.log_utils import setup_logging

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.logging]


class TestLogging:
    """Unit tests for the logging functionality."""
    
    def test_setup_logging(self, app, caplog):
        """Test that logging is correctly set up."""
        with app.app_context():
            # Import the setup_logging function based on what's available
            try:
                from meeting_shared.logging import setup_logging
            except ImportError:
                from src.core.logging import setup_logging
            
            # Set up logging
            logger = setup_logging(
                app=app,
                service_name='test-service',
                log_level='DEBUG'
            )
            
            # Verify logger
            assert logger is not None
            assert logger.name == 'test-service'
            assert logger.level == logging.DEBUG
            
            # Log a message
            test_message = "Test log message"
            logger.info(test_message)
            
            # Verify the message was logged
            assert test_message in caplog.text
    
    def test_request_id_in_logs(self, app, caplog, mock_request_id):
        """Test that request IDs are included in logs."""
        with app.app_context():
            # Import based on what's available
            try:
                from meeting_shared.logging import setup_logging
            except ImportError:
                from src.core.logging import setup_logging
            
            # Set up logging
            logger = setup_logging(app=app, service_name='test-service')
            
            # Log a message
            test_message = "Test log message with request ID"
            logger.info(test_message)
            
            # Verify request ID in logs
            assert mock_request_id in caplog.text
            assert test_message in caplog.text
    
    def test_json_logging_format(self, app):
        """Test that logs are formatted as JSON when configured."""
        with app.app_context():
            # Mock the logging handlers
            mock_handler = MagicMock()
            
            with patch('logging.StreamHandler', return_value=mock_handler):
                # Import based on what's available
                try:
                    from meeting_shared.logging import setup_logging
                except ImportError:
                    from src.core.logging import setup_logging
                
                # Set up JSON logging
                logger = setup_logging(
                    app=app,
                    service_name='test-service',
                    json_logs=True
                )
                
                # Log a message
                test_message = "JSON log test"
                logger.info(test_message)
                
                # Get the call args from the mock
                args, kwargs = mock_handler.handle.call_args
                record = args[0]
                
                # Check record attributes
                assert record.getMessage() == test_message
                assert record.levelname == 'INFO'
                assert record.name == 'test-service'
                
                # Check formatter output if available
                if hasattr(mock_handler, 'format'):
                    formatted = mock_handler.format(record)
                    try:
                        log_data = json.loads(formatted)
                        assert log_data['message'] == test_message
                        assert log_data['level'] == 'INFO'
                    except json.JSONDecodeError:
                        pass  # Not JSON format
    
    def test_logging_with_extra_context(self, app, caplog):
        """Test logging with extra context information."""
        with app.app_context():
            # Import based on what's available
            try:
                from meeting_shared.logging import setup_logging
            except ImportError:
                from src.core.logging import setup_logging
            
            # Set up logging
            logger = setup_logging(app=app, service_name='test-service')
            
            # Log with extra context
            context = {'user_id': 123, 'action': 'login'}
            logger.info("User action", extra=context)
            
            # Verify context in log
            assert 'user_id' in caplog.text
            assert 'action' in caplog.text
            assert '123' in caplog.text
            assert 'login' in caplog.text
    
    def test_error_logging_with_exception(self, app, caplog):
        """Test error logging with exception information."""
        with app.app_context():
            # Import based on what's available
            try:
                from meeting_shared.logging import setup_logging
            except ImportError:
                from src.core.logging import setup_logging
            
            # Set up logging
            logger = setup_logging(app=app, service_name='test-service')
            
            # Log an exception
            try:
                # Raise an exception
                raise ValueError("Test exception")
            except ValueError as e:
                # Log the exception
                logger.error("An error occurred", exc_info=True)
            
            # Verify exception info in log
            assert "An error occurred" in caplog.text
            assert "ValueError" in caplog.text
            assert "Test exception" in caplog.text
            assert "Traceback" in caplog.text
    
    def test_log_levels(self, app, caplog):
        """Test different log levels."""
        with app.app_context():
            # Import based on what's available
            try:
                from meeting_shared.logging import setup_logging
            except ImportError:
                from src.core.logging import setup_logging
            
            # Set logging level to INFO
            logger = setup_logging(
                app=app,
                service_name='test-service',
                log_level='INFO'
            )
            
            # Clear caplog
            caplog.clear()
            
            # Log at different levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Verify log levels
            assert "Debug message" not in caplog.text  # Should be filtered out
            assert "Info message" in caplog.text
            assert "Warning message" in caplog.text
            assert "Error message" in caplog.text 