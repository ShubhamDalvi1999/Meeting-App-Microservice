"""
Integration tests for request ID propagation in the auth service.
"""

import pytest
import json
import uuid
import re
from unittest.mock import patch, MagicMock

# Add pytest mark for test categories
pytestmark = [pytest.mark.integration, pytest.mark.logging]


class TestRequestIdPropagation:
    """Integration tests for request ID propagation in auth service."""
    
    def test_request_id_in_response_headers(self, client, mock_request_id):
        """Test that request IDs are included in response headers."""
        # Make a request with a custom request ID
        response = client.get(
            '/health',
            headers={'X-Request-ID': mock_request_id}
        )
        
        assert response.status_code == 200
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == mock_request_id
    
    def test_request_id_in_json_response(self, client, mock_request_id):
        """Test that request IDs are included in JSON response bodies."""
        # Make a request with a custom request ID
        response = client.get(
            '/health',
            headers={'X-Request-ID': mock_request_id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] == mock_request_id
    
    def test_request_id_generation(self, client):
        """Test that request IDs are generated if not provided."""
        # Make a request without providing a request ID
        response = client.get('/health')
        
        assert response.status_code == 200
        
        # Check that a request ID was generated and added to the response
        assert 'X-Request-ID' in response.headers
        generated_request_id = response.headers['X-Request-ID']
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', generated_request_id)
        
        # Check JSON response body
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] == generated_request_id
    
    def test_correlation_id_preservation(self, client):
        """Test that correlation IDs are preserved in responses."""
        correlation_id = str(uuid.uuid4())
        
        # Make a request with a correlation ID
        response = client.get(
            '/health',
            headers={'X-Correlation-ID': correlation_id}
        )
        
        assert response.status_code == 200
        assert 'X-Correlation-ID' in response.headers
        assert response.headers['X-Correlation-ID'] == correlation_id
    
    def test_request_id_in_error_responses(self, client, mock_request_id):
        """Test that request IDs are included in error responses."""
        # Make a request to a non-existent endpoint
        response = client.get(
            '/nonexistent-endpoint',
            headers={'X-Request-ID': mock_request_id}
        )
        
        assert response.status_code == 404
        
        # Check headers
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == mock_request_id
        
        # Check JSON response body
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] == mock_request_id
    
    def test_request_id_in_auth_operations(self, client, db, mock_request_id):
        """Test that request IDs are maintained during authentication operations."""
        # Register a new user with a request ID
        user_data = {
            'email': 'testrequestid@example.com',
            'password': 'Password123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json',
            headers={'X-Request-ID': mock_request_id}
        )
        
        assert response.status_code == 201
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == mock_request_id
        
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] == mock_request_id
        
        # Now login with the same user and a different request ID
        login_request_id = str(uuid.uuid4())
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json',
            headers={'X-Request-ID': login_request_id}
        )
        
        assert response.status_code == 200
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == login_request_id
        
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] == login_request_id
        
        # Extract tokens for further tests
        access_token = data['access_token']
        
        # Test accessing profile with a third request ID
        profile_request_id = str(uuid.uuid4())
        response = client.get(
            '/api/users/me',
            headers={
                'Authorization': f'Bearer {access_token}',
                'X-Request-ID': profile_request_id
            }
        )
        
        assert response.status_code == 200
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == profile_request_id
        
        data = json.loads(response.data)
        # User data doesn't include request_id in the response
        assert data['email'] == user_data['email']
    
    def test_request_id_in_service_token_operations(self, client, mock_request_id):
        """Test that request IDs are maintained during service token operations."""
        # Create app config for service token auth
        from src.app import app
        app.config['SERVICE_TOKEN_ENABLED'] = True
        app.config['SERVICE_NAME'] = 'test-service'
        app.config['SERVICE_SECRET'] = 'test-secret'
        
        # Get a service token with a request ID
        response = client.post(
            '/api/auth/service-token',
            data=json.dumps({
                'service_name': 'test-service',
                'service_secret': 'test-secret'
            }),
            content_type='application/json',
            headers={'X-Request-ID': mock_request_id}
        )
        
        assert response.status_code == 200
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == mock_request_id
        
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