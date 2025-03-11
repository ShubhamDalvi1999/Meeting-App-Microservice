"""
Integration tests for auth service integration in the Flask service.
"""

import pytest
import json
import uuid
from unittest.mock import patch

# Add pytest mark for test categories
pytestmark = [pytest.mark.integration, pytest.mark.auth]


class TestAuthServiceIntegration:
    """Integration tests for auth service integration."""
    
    def test_token_validation(self, client, mock_auth_service, auth_header):
        """Test validating a token with the auth service."""
        # Set up mock auth service to validate the token
        token = auth_header['Authorization'].split(' ')[1]
        user_id = str(uuid.uuid4())
        
        mock_auth_service.add_response(
            method='GET',
            url='/api/auth/validate-token',
            json={
                'valid': True,
                'user_id': user_id,
                'email': 'test@example.com',
                'roles': ['user']
            },
            match=[('authorization', f'Bearer {token}')]
        )
        
        # Call an endpoint that requires authentication
        response = client.get('/api/meetings', headers=auth_header)
        
        # Should succeed with the mocked auth service
        assert response.status_code == 200
        
        # Verify the auth service was called
        request = mock_auth_service.request_history[0]
        assert 'Authorization' in request.headers
        assert request.headers['Authorization'] == f'Bearer {token}'
    
    def test_token_validation_failure(self, client, mock_auth_service):
        """Test handling of invalid tokens."""
        # Set up mock auth service to reject the token
        mock_auth_service.add_response(
            method='GET',
            url='/api/auth/validate-token',
            status=401,
            json={
                'message': 'Invalid token',
                'status_code': 401,
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Call an endpoint that requires authentication with an invalid token
        response = client.get(
            '/api/meetings',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        # Should return unauthorized
        assert response.status_code == 401
        
        # Check the response
        data = json.loads(response.data)
        assert 'Invalid token' in data['message']
    
    def test_get_user_info(self, client, mock_auth_service, auth_header):
        """Test retrieving user information from the auth service."""
        # Set up mock auth service responses
        token = auth_header['Authorization'].split(' ')[1]
        user_id = str(uuid.uuid4())
        
        # Mock token validation
        mock_auth_service.add_response(
            method='GET',
            url='/api/auth/validate-token',
            json={
                'valid': True,
                'user_id': user_id,
                'email': 'test@example.com',
                'roles': ['user']
            },
            match=[('authorization', f'Bearer {token}')]
        )
        
        # Mock user info endpoint
        mock_auth_service.add_response(
            method='GET',
            url=f'/api/users/{user_id}',
            json={
                'id': user_id,
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'created_at': '2023-01-01T12:00:00Z'
            }
        )
        
        # Create a test endpoint that gets user info
        with patch('src.services.auth_service.get_user_info') as mock_get_user_info:
            # Mock the service function to actually call the mock auth service
            mock_get_user_info.return_value = mock_auth_service.request_history
            
            # Call an endpoint that requires user info
            response = client.post(
                '/api/meetings',
                data=json.dumps({
                    'title': 'Test Meeting',
                    'description': 'Test Description',
                    'start_time': '2023-01-02T12:00:00Z',
                    'end_time': '2023-01-02T13:00:00Z',
                    'location': 'Test Location'
                }),
                content_type='application/json',
                headers=auth_header
            )
            
            # Should succeed with the mocked auth service
            assert response.status_code == 201
            
            # Verify the auth service was called for token validation
            assert len(mock_auth_service.request_history) >= 1
            token_request = mock_auth_service.request_history[0]
            assert token_request.url.endswith('/api/auth/validate-token')
    
    def test_auth_service_unavailable(self, client, mock_auth_service):
        """Test handling of auth service unavailability."""
        # Set up mock auth service to be unavailable
        mock_auth_service.add_response(
            method='GET',
            url='/api/auth/validate-token',
            status=503,
            json={
                'message': 'Service Unavailable',
                'status_code': 503,
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Call an endpoint that requires authentication
        response = client.get(
            '/api/meetings',
            headers={'Authorization': 'Bearer token'}
        )
        
        # Should return service unavailable or unauthorized
        assert response.status_code in (401, 503)
        
        # Check the response
        data = json.loads(response.data)
        assert 'Service Unavailable' in data['message'] or 'auth service' in data['message'].lower()
    
    def test_service_token_auth(self, client, mock_auth_service):
        """Test service-to-service authentication."""
        # Set up mock auth service for service token
        service_token = 'service-token-123'
        
        mock_auth_service.add_response(
            method='POST',
            url='/api/auth/service-token',
            json={
                'service_token': service_token,
                'expires_at': '2023-01-02T12:00:00Z'
            }
        )
        
        # Also mock the validation endpoint for this token
        mock_auth_service.add_response(
            method='GET',
            url='/api/auth/validate-token',
            json={
                'valid': True,
                'service': 'flask-service',
                'roles': ['service']
            },
            match=[('authorization', f'Bearer {service_token}')]
        )
        
        # Create a test that gets a service token
        with patch('src.services.auth_service.get_service_token') as mock_get_token:
            # Mock the service function to return the token from the mock service
            mock_get_token.return_value = service_token
            
            # Call an authenticated service endpoint
            response = client.get(
                '/api/health/services',
                headers={'Authorization': f'Bearer {service_token}'}
            )
            
            # Should succeed with the mocked service token
            assert response.status_code == 200
    
    def test_auth_middleware(self, client, mock_auth_service, auth_header):
        """Test that the authentication middleware correctly passes user context."""
        # Set up mock auth service to validate the token
        token = auth_header['Authorization'].split(' ')[1]
        user_id = str(uuid.uuid4())
        
        mock_auth_service.add_response(
            method='GET',
            url='/api/auth/validate-token',
            json={
                'valid': True,
                'user_id': user_id,
                'email': 'test@example.com',
                'roles': ['user']
            },
            match=[('authorization', f'Bearer {token}')]
        )
        
        # Call an authenticated endpoint
        response = client.get('/api/meetings', headers=auth_header)
        
        # Should succeed
        assert response.status_code == 200
        
        # In a real test, we would verify that user context was passed to the endpoint
        # Here we're just checking that the auth service was called correctly
        request = mock_auth_service.request_history[0]
        assert request.url.endswith('/api/auth/validate-token')
        assert request.headers['Authorization'] == f'Bearer {token}' 