"""
Tests for authentication functionality.
"""

import pytest
from flask import url_for

def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post('/api/auth/login', json={
        'email': test_user['email'],
        'password': test_user['password']
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert 'refresh_token' in response.json

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    response = client.post('/api/auth/login', json={
        'email': test_user['email'],
        'password': 'wrong_password'
    })
    assert response.status_code == 401
    assert response.json['error'] == 'Authentication Error'

def test_refresh_token(client, refresh_token):
    """Test token refresh."""
    response = client.post('/api/auth/refresh', headers={
        'Authorization': f'Bearer {refresh_token}'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_logout(client, access_token):
    """Test logout functionality."""
    response = client.post('/api/auth/logout', headers={
        'Authorization': f'Bearer {access_token}'
    })
    assert response.status_code == 200
    
    # Try to use the token after logout
    response = client.get('/api/users/me', headers={
        'Authorization': f'Bearer {access_token}'
    })
    assert response.status_code == 401 