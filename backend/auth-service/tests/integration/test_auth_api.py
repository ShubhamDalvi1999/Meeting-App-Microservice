"""
Integration tests for the auth service API endpoints.
"""

import pytest
import json
import jwt
from datetime import datetime, timedelta

# Add pytest mark for test categories
pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.api]


class TestAuthAPI:
    """Integration tests for the authentication API endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'version' in data
        assert 'timestamp' in data
        assert 'request_id' in data
    
    def test_register_user(self, client, db):
        """Test user registration."""
        user_data = {
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User created successfully'
        assert 'id' in data['user']
        assert data['user']['email'] == user_data['email']
        assert data['user']['first_name'] == user_data['first_name']
        assert data['user']['last_name'] == user_data['last_name']
        assert 'password' not in data['user']
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_register_user_existing_email(self, client, test_user):
        """Test registering a user with an existing email."""
        user_data = {
            'email': test_user['email'],
            'password': 'Password123!',
            'first_name': 'Another',
            'last_name': 'User'
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'already exists' in data['message'].lower()
    
    def test_register_user_invalid_data(self, client):
        """Test registering a user with invalid data."""
        # Missing required fields
        user_data = {
            'email': 'invalid@example.com',
            'first_name': 'Invalid'
            # Missing password and last_name
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'validation error' in data['message'].lower()
        
        # Invalid email format
        user_data = {
            'email': 'not-an-email',
            'password': 'Password123!',
            'first_name': 'Invalid',
            'last_name': 'User'
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'validation error' in data['message'].lower()
        assert 'email' in str(data['details']).lower()
        
        # Invalid password (too short)
        user_data = {
            'email': 'valid@example.com',
            'password': 'short',
            'first_name': 'Invalid',
            'last_name': 'User'
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'validation error' in data['message'].lower()
        assert 'password' in str(data['details']).lower()
    
    def test_login(self, client, test_user):
        """Test user login."""
        login_data = {
            'email': test_user['email'],
            'password': 'Password123!'  # This is the password from the test_user fixture
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Login successful'
        assert 'user' in data
        assert data['user']['email'] == test_user['email']
        assert 'access_token' in data
        assert 'refresh_token' in data
        
        # Verify token contains correct user id
        from src.utils.token_service import decode_token
        token_data = decode_token(data['access_token'])
        assert token_data['sub'] == str(test_user['id'])
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        # Wrong password
        login_data = {
            'email': test_user['email'],
            'password': 'WrongPassword123!'
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'invalid' in data['message'].lower()
        
        # Non-existent user
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'Password123!'
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'invalid' in data['message'].lower()
    
    def test_refresh_token(self, client, test_user, refresh_token):
        """Test refreshing access token."""
        refresh_data = {
            'refresh_token': refresh_token
        }
        
        response = client.post(
            '/api/auth/refresh',
            data=json.dumps(refresh_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data  # Should also get a new refresh token
        
        # Verify token contains correct user id
        from src.utils.token_service import decode_token
        token_data = decode_token(data['access_token'])
        assert token_data['sub'] == str(test_user['id'])
    
    def test_refresh_token_invalid(self, client):
        """Test refreshing with an invalid refresh token."""
        refresh_data = {
            'refresh_token': 'invalid-token'
        }
        
        response = client.post(
            '/api/auth/refresh',
            data=json.dumps(refresh_data),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'invalid' in data['message'].lower()
    
    def test_logout(self, client, access_token):
        """Test user logout."""
        logout_data = {
            'access_token': access_token
        }
        
        response = client.post(
            '/api/auth/logout',
            data=json.dumps(logout_data),
            content_type='application/json',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'logged out' in data['message'].lower()
        
        # Try to use the same token after logout
        response = client.get(
            '/api/users/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        assert response.status_code == 401
    
    def test_get_user_profile(self, client, test_user, auth_header):
        """Test getting the current user's profile."""
        response = client.get(
            '/api/users/me',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == test_user['id']
        assert data['email'] == test_user['email']
        assert data['first_name'] == test_user['first_name']
        assert data['last_name'] == test_user['last_name']
        assert 'password' not in data
    
    def test_update_user_profile(self, client, test_user, auth_header):
        """Test updating the current user's profile."""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = client.put(
            '/api/users/me',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['first_name'] == update_data['first_name']
        assert data['last_name'] == update_data['last_name']
        assert data['email'] == test_user['email']  # Email should not change
        
        # Verify changes were persisted
        response = client.get(
            '/api/users/me',
            headers=auth_header
        )
        
        data = json.loads(response.data)
        assert data['first_name'] == update_data['first_name']
        assert data['last_name'] == update_data['last_name']
    
    def test_change_password(self, client, test_user, auth_header):
        """Test changing the user's password."""
        password_data = {
            'current_password': 'Password123!',
            'new_password': 'NewPassword456!'
        }
        
        response = client.put(
            '/api/users/me/password',
            data=json.dumps(password_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'password updated' in data['message'].lower()
        
        # Try logging in with the new password
        login_data = {
            'email': test_user['email'],
            'password': 'NewPassword456!'
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_change_password_invalid_current(self, client, auth_header):
        """Test changing password with invalid current password."""
        password_data = {
            'current_password': 'WrongPassword!',
            'new_password': 'NewPassword456!'
        }
        
        response = client.put(
            '/api/users/me/password',
            data=json.dumps(password_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'invalid' in data['message'].lower()
    
    def test_unauthorized_access(self, client):
        """Test accessing protected endpoints without authentication."""
        # Try accessing user profile without token
        response = client.get('/api/users/me')
        assert response.status_code == 401
        
        # Try with invalid token
        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        assert response.status_code == 401 