"""
Integration tests for user workflow.
"""

import pytest
import time

def test_complete_user_flow(client):
    """Test complete user registration, authentication, and management flow."""
    # Register a new user
    user_data = {
        'email': 'integration@test.com',
        'password': 'Test123!@#',
        'name': 'Integration Test User'
    }
    
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201
    
    # Verify login with new user
    login_data = {
        'email': user_data['email'],
        'password': user_data['password']
    }
    response = client.post('/api/auth/login', json=login_data)
    assert response.status_code == 200
    tokens = response.json
    assert 'access_token' in tokens
    assert 'refresh_token' in tokens
    
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']
    auth_header = {'Authorization': f'Bearer {access_token}'}
    
    # Get user profile
    response = client.get('/api/users/me', headers=auth_header)
    assert response.status_code == 200
    profile = response.json
    assert profile['email'] == user_data['email']
    assert profile['name'] == user_data['name']
    
    # Update user profile
    update_data = {
        'name': 'Updated Test User',
        'preferences': {
            'timezone': 'UTC',
            'notifications_enabled': True
        }
    }
    response = client.put('/api/users/me', 
                         json=update_data,
                         headers=auth_header)
    assert response.status_code == 200
    
    # Verify profile update
    response = client.get('/api/users/me', headers=auth_header)
    assert response.status_code == 200
    updated_profile = response.json
    assert updated_profile['name'] == update_data['name']
    assert updated_profile['preferences']['timezone'] == 'UTC'
    
    # Test token refresh
    time.sleep(1)  # Ensure some time has passed
    response = client.post('/api/auth/refresh', headers={
        'Authorization': f'Bearer {refresh_token}'
    })
    assert response.status_code == 200
    new_tokens = response.json
    assert 'access_token' in new_tokens
    
    # Verify new access token works
    new_auth_header = {'Authorization': f'Bearer {new_tokens["access_token"]}'}
    response = client.get('/api/users/me', headers=new_auth_header)
    assert response.status_code == 200
    
    # Logout
    response = client.post('/api/auth/logout', headers=auth_header)
    assert response.status_code == 200
    
    # Verify token is invalidated
    response = client.get('/api/users/me', headers=auth_header)
    assert response.status_code == 401 