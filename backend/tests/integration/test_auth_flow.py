"""
Integration tests for authentication flow between services
"""

import pytest
import requests
import time
import jwt
from .base import IntegrationTestBase

class TestAuthFlow(IntegrationTestBase):
    """Test the entire authentication flow across services"""
    
    def test_register_login_access_api(self):
        """Test full user lifecycle: registration, login, and API access"""
        # Generate unique test user
        timestamp = int(time.time())
        email = f"test_user_{timestamp}@example.com"
        password = "Test123!"
        name = f"Test User {timestamp}"
        
        # 1. Register a new user
        register_url = f"{self.auth_url}/api/auth/register"
        register_data = {
            'email': email,
            'password': password,
            'name': name
        }
        
        register_response = requests.post(
            register_url, 
            json=register_data,
            timeout=self.timeout
        )
        
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data['email'] == email
        assert 'id' in user_data
        
        # 2. Login with the new user
        login_url = f"{self.auth_url}/api/auth/login"
        login_data = {
            'email': email,
            'password': password
        }
        
        login_response = requests.post(
            login_url,
            json=login_data,
            timeout=self.timeout
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        
        access_token = tokens['access_token']
        
        # Verify token is valid JWT with expected claims
        decoded = jwt.decode(
            access_token, 
            options={"verify_signature": False}
        )
        assert decoded['email'] == email
        assert 'sub' in decoded
        assert 'roles' in decoded
        assert 'user' in decoded['roles']
        
        # 3. Access an API endpoint that requires authentication
        meetings_url = f"{self.api_url}/api/meetings"
        headers = self.get_headers(access_token)
        
        # Attempt to access meetings endpoint (which requires auth)
        meetings_response = requests.get(
            meetings_url,
            headers=headers,
            timeout=self.timeout
        )
        
        # Should return 200 OK with empty meetings list for new user
        assert meetings_response.status_code == 200
        assert isinstance(meetings_response.json(), list)
        
        # 4. Test accessing API with invalid token
        invalid_headers = self.get_headers("invalid.token.here")
        invalid_response = requests.get(
            meetings_url,
            headers=invalid_headers,
            timeout=self.timeout
        )
        
        # Should return 401 Unauthorized
        assert invalid_response.status_code == 401
    
    def test_service_to_service_communication(self):
        """Test service-to-service communication using service keys"""
        # 1. Generate unique test user through normal registration
        timestamp = int(time.time())
        email = f"test_service_{timestamp}@example.com"
        password = "Test123!"
        name = f"Service Test {timestamp}"
        
        # Register user
        register_url = f"{self.auth_url}/api/auth/register"
        register_data = {
            'email': email,
            'password': password,
            'name': name
        }
        
        register_response = requests.post(
            register_url, 
            json=register_data,
            timeout=self.timeout
        )
        
        assert register_response.status_code == 201
        user_id = register_response.json()['id']
        
        # 2. Use service-to-service endpoint to modify user (requires service key)
        roles_url = f"{self.auth_url}/api/internal/users/roles"
        roles_data = {
            'email': email,
            'roles': ['user', 'admin']  # Add admin role
        }
        
        # First try without service key (should fail)
        no_key_response = requests.put(
            roles_url,
            json=roles_data,
            timeout=self.timeout
        )
        
        assert no_key_response.status_code in [401, 403]  # Either unauthorized or forbidden
        
        # Now try with service key (should succeed)
        service_headers = self.get_service_headers()
        service_response = requests.put(
            roles_url,
            headers=service_headers,
            json=roles_data,
            timeout=self.timeout
        )
        
        assert service_response.status_code == 200
        
        # 3. Verify user now has admin role by logging in
        login_response = self.login(email, password)
        access_token = login_response.json()['access_token']
        
        decoded = jwt.decode(
            access_token, 
            options={"verify_signature": False}
        )
        
        assert 'admin' in decoded['roles']
        
        # 4. Test accessing admin-only endpoint with the new admin user
        # This assumes there's an admin-only endpoint in your API
        # Replace with an actual admin endpoint in your system
        admin_url = f"{self.api_url}/api/meetings/admin/stats"
        admin_headers = self.get_headers(access_token)
        
        admin_response = requests.get(
            admin_url,
            headers=admin_headers,
            timeout=self.timeout
        )
        
        # If your API has proper role-based access control, this should succeed
        # Note: If this endpoint doesn't exist, you may need to adjust this test
        assert admin_response.status_code in [200, 404]  # Either success or not found
        
        # It should not return 401/403 which would indicate auth failure
        assert admin_response.status_code not in [401, 403]
    
    def test_token_refresh_flow(self):
        """Test the token refresh flow"""
        # 1. Login with test user
        login_response = self.login(
            self.config['TEST_USER_EMAIL'],
            self.config['TEST_USER_PASSWORD']
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert 'refresh_token' in tokens
        
        refresh_token = tokens['refresh_token']
        
        # 2. Use refresh token to get new access token
        refresh_url = f"{self.auth_url}/api/auth/refresh"
        refresh_data = {
            'refresh_token': refresh_token
        }
        
        refresh_response = requests.post(
            refresh_url,
            json=refresh_data,
            timeout=self.timeout
        )
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert 'access_token' in new_tokens
        
        # 3. Verify new access token works
        new_access_token = new_tokens['access_token']
        meetings_url = f"{self.api_url}/api/meetings"
        headers = self.get_headers(new_access_token)
        
        meetings_response = requests.get(
            meetings_url,
            headers=headers,
            timeout=self.timeout
        )
        
        assert meetings_response.status_code == 200 