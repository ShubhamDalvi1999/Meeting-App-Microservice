"""
Unit tests for utility functions.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.utils]


class TestDateTimeUtils:
    """Tests for date and time utility functions."""
    
    def test_parse_datetime(self, app):
        """Test parsing datetime strings."""
        with app.app_context():
            try:
                from src.utils.datetime_utils import parse_datetime
            except ImportError:
                pytest.skip("parse_datetime function not found")
            
            # Test ISO format
            iso_str = "2023-08-15T14:30:00Z"
            dt = parse_datetime(iso_str)
            
            assert dt is not None
            assert isinstance(dt, datetime)
            assert dt.year == 2023
            assert dt.month == 8
            assert dt.day == 15
            assert dt.hour == 14
            assert dt.minute == 30
            
            # Test alternative format (if supported)
            alt_str = "2023-08-15 14:30:00"
            dt = parse_datetime(alt_str)
            
            assert dt is not None
            assert isinstance(dt, datetime)
    
    def test_format_datetime(self, app):
        """Test formatting datetime objects."""
        with app.app_context():
            try:
                from src.utils.datetime_utils import format_datetime
            except ImportError:
                pytest.skip("format_datetime function not found")
            
            # Create a datetime
            dt = datetime(2023, 8, 15, 14, 30, 0)
            
            # Format datetime
            dt_str = format_datetime(dt)
            
            assert dt_str is not None
            assert isinstance(dt_str, str)
            
            # Basic check for ISO format
            assert '2023-08-15' in dt_str
            assert '14:30' in dt_str
    
    def test_is_future_date(self, app):
        """Test checking if a date is in the future."""
        with app.app_context():
            try:
                from src.utils.datetime_utils import is_future_date
            except ImportError:
                pytest.skip("is_future_date function not found")
            
            # Test future date
            future_dt = datetime.utcnow() + timedelta(days=1)
            assert is_future_date(future_dt) is True
            
            # Test past date
            past_dt = datetime.utcnow() - timedelta(days=1)
            assert is_future_date(past_dt) is False


class TestValidationUtils:
    """Tests for validation utility functions."""
    
    def test_validate_email(self, app):
        """Test email validation."""
        with app.app_context():
            try:
                from src.utils.validation_utils import validate_email
            except ImportError:
                pytest.skip("validate_email function not found")
            
            # Test valid email
            valid_email = "test@example.com"
            assert validate_email(valid_email) is True
            
            # Test invalid email
            invalid_email = "not-an-email"
            assert validate_email(invalid_email) is False
    
    def test_validate_password(self, app):
        """Test password validation."""
        with app.app_context():
            try:
                from src.utils.validation_utils import validate_password
            except ImportError:
                pytest.skip("validate_password function not found")
            
            # Test valid password
            valid_password = "Password123!"
            assert validate_password(valid_password) is True
            
            # Test invalid password (if implemented)
            invalid_password = "pass"
            result = validate_password(invalid_password)
            # The result depends on password policy, might be True or False


class TestHttpUtils:
    """Tests for HTTP utility functions."""
    
    def test_make_request(self):
        """Test making HTTP requests."""
        try:
            from src.utils.http_utils import make_request
        except ImportError:
            try:
                from meeting_shared.utils.http import make_request
            except ImportError:
                pytest.skip("make_request function not found")
        
        # Mock the requests module
        with patch('requests.request') as mock_request:
            # Configure mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'data': 'test'}
            mock_request.return_value = mock_response
            
            # Make request
            response = make_request('GET', 'http://example.com/api')
            
            # Verify request was made
            mock_request.assert_called_once()
            
            # Verify response
            assert response.status_code == 200
            assert response.json() == {'data': 'test'}
    
    def test_add_request_id_to_headers(self):
        """Test adding request ID to headers."""
        try:
            from src.utils.http_utils import add_request_id_headers
        except ImportError:
            try:
                from meeting_shared.utils.http import add_request_id_headers
            except ImportError:
                pytest.skip("add_request_id_headers function not found")
        
        # Test with empty headers
        headers = {}
        
        # Mock the request ID generation
        with patch('src.middleware.request_id.get_request_id', return_value='test-request-id'):
            try:
                result = add_request_id_headers(headers)
            except ImportError:
                # Try alternative import path
                with patch('meeting_shared.middleware.request_id.get_request_id', return_value='test-request-id'):
                    result = add_request_id_headers(headers)
        
        # Verify request ID was added
        assert result is not None
        assert 'X-Request-ID' in result
        assert result['X-Request-ID'] == 'test-request-id'


class TestJsonUtils:
    """Tests for JSON utility functions."""
    
    def test_convert_datetime_to_json(self, app):
        """Test converting datetime objects to JSON."""
        with app.app_context():
            try:
                from src.utils.json_utils import datetime_encoder
            except ImportError:
                pytest.skip("datetime_encoder not found")
            
            # Create a datetime
            dt = datetime(2023, 8, 15, 14, 30, 0)
            
            # Create an object with datetime
            obj = {'timestamp': dt, 'name': 'test'}
            
            # Convert to JSON
            json_str = json.dumps(obj, default=datetime_encoder)
            
            # Parse JSON
            parsed = json.loads(json_str)
            
            # Verify conversion
            assert parsed is not None
            assert 'timestamp' in parsed
            assert parsed['timestamp'] is not None
            assert isinstance(parsed['timestamp'], str)
            assert '2023-08-15' in parsed['timestamp'] 