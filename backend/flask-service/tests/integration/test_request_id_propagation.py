"""
Integration tests for request ID propagation between services.
"""

import pytest
import json
import uuid
import re
from unittest.mock import patch, MagicMock

# Add pytest mark for test categories
pytestmark = [pytest.mark.integration, pytest.mark.logging]


class TestRequestIdPropagation:
    """Integration tests for request ID propagation between services."""
    
    def test_request_id_in_service_calls(self, client, mock_auth_service, auth_header, mock_request_id):
        """Test that request IDs are propagated to dependent services."""
        # Call an endpoint that will make a request to the auth service
        response = client.get(
            '/api/meetings',
            headers={**auth_header, 'X-Request-ID': mock_request_id}
        )
        
        assert response.status_code == 200
        
        # Check the request headers used for the mock auth service call
        request_headers = mock_auth_service.request_history[0].headers
        assert 'X-Request-ID' in request_headers
        assert request_headers['X-Request-ID'] == mock_request_id
    
    def test_correlation_id_in_service_calls(self, client, mock_auth_service, auth_header):
        """Test that correlation IDs are propagated to dependent services."""
        correlation_id = str(uuid.uuid4())
        
        # Call an endpoint that will make a request to the auth service
        response = client.get(
            '/api/meetings',
            headers={**auth_header, 'X-Correlation-ID': correlation_id}
        )
        
        assert response.status_code == 200
        
        # Check the request headers used for the mock auth service call
        request_headers = mock_auth_service.request_history[0].headers
        assert 'X-Correlation-ID' in request_headers
        assert request_headers['X-Correlation-ID'] == correlation_id
    
    def test_request_id_generation_and_propagation(self, client, mock_auth_service, auth_header):
        """Test that request IDs are generated if not provided and propagated."""
        # Call an endpoint without providing a request ID
        response = client.get(
            '/api/meetings',
            headers=auth_header
        )
        
        assert response.status_code == 200
        
        # Check that a request ID was generated and added to the response
        assert 'X-Request-ID' in response.headers
        generated_request_id = response.headers['X-Request-ID']
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', generated_request_id)
        
        # Check the request headers used for the mock auth service call
        request_headers = mock_auth_service.request_history[0].headers
        assert 'X-Request-ID' in request_headers
        assert request_headers['X-Request-ID'] == generated_request_id
    
    def test_request_id_in_service_error_responses(self, client, mock_auth_service, auth_header, mock_request_id):
        """Test that request IDs are included in error responses from service calls."""
        # Configure mock to return an error response
        mock_auth_service.reset()
        mock_auth_service.add_response(
            'GET', 
            '/api/users/me',
            status=401,
            json={
                'message': 'Invalid token',
                'status_code': 401,
                'details': {},
                'timestamp': '2023-01-01T12:00:00Z',
                'request_id': mock_request_id
            }
        )
        
        # Call an endpoint that will make a request to the auth service
        response = client.get(
            '/api/meetings/invalid',
            headers={**auth_header, 'X-Request-ID': mock_request_id}
        )
        
        # Should get an error response from our service, mirroring auth service error
        assert response.status_code == 401
        
        # Check that the request ID is in the response
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] == mock_request_id
    
    def test_http_util_request_id_propagation(self, app):
        """Test that the HTTP util functions propagate request IDs."""
        with app.app_context():
            # Try to import from shared module first
            try:
                from meeting_shared.utils.http import make_request, add_request_id_to_headers
            except ImportError:
                from src.utils.http import make_request, add_request_id_to_headers
            
            # Mock the requests.request function
            with patch('requests.request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": "test"}
                mock_request.return_value = mock_response
                
                # Set up a request context with a request ID
                test_request_id = str(uuid.uuid4())
                with app.test_request_context(headers={'X-Request-ID': test_request_id}):
                    # Make a request using our utility function
                    response = make_request('GET', 'http://test-service/api/endpoint')
                    
                    # Check that the request ID was propagated
                    args, kwargs = mock_request.call_args
                    assert 'headers' in kwargs
                    assert 'X-Request-ID' in kwargs['headers']
                    assert kwargs['headers']['X-Request-ID'] == test_request_id
    
    def test_add_request_id_to_headers_function(self, app):
        """Test the add_request_id_to_headers utility function."""
        with app.app_context():
            # Try to import from shared module first
            from meeting_shared.utils.http import add_request_id_to_headers
            from meeting_shared.middleware.request_id import get_request_id
            
            # Set up a request context with a request ID
            test_request_id = str(uuid.uuid4())
            with app.test_request_context(headers={'X-Request-ID': test_request_id}):
                # Add request ID to empty headers
                headers = {}
                add_request_id_to_headers(headers)
                assert 'X-Request-ID' in headers
                assert headers['X-Request-ID'] == test_request_id
                
                # Add request ID to existing headers
                headers = {'Content-Type': 'application/json'}
                add_request_id_to_headers(headers)
                assert 'X-Request-ID' in headers
                assert headers['X-Request-ID'] == test_request_id
                assert 'Content-Type' in headers
                
                # Should not override existing request ID
                headers = {'X-Request-ID': 'existing-id'}
                add_request_id_to_headers(headers)
                assert headers['X-Request-ID'] == 'existing-id'
    
    def test_logging_with_request_id(self, app, caplog):
        """Test that request IDs are included in log messages."""
        with app.app_context():
            import logging
            
            # Set up a request context with a request ID
            test_request_id = str(uuid.uuid4())
            with app.test_request_context(headers={'X-Request-ID': test_request_id}):
                # Log a message
                logger = logging.getLogger('test_logger')
                logger.info("Test log message")
                
                # Check that the log record includes the request ID
                for record in caplog.records:
                    if record.name == 'test_logger':
                        assert record.request_id == test_request_id 