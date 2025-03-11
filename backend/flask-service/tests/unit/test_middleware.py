"""
Tests for middleware components.
"""

import pytest
from flask import g
from meeting_shared.middleware.request_id import get_request_id

def test_request_id_middleware(client):
    """Test that request ID middleware adds request ID to context."""
    response = client.get('/health')
    assert response.status_code == 200
    assert 'X-Request-ID' in response.headers

def test_request_id_propagation(client):
    """Test that request ID is propagated when provided."""
    request_id = "test-123"
    response = client.get('/health', headers={'X-Request-ID': request_id})
    assert response.status_code == 200
    assert response.headers['X-Request-ID'] == request_id

def test_auth_middleware_missing_token(client):
    """Test that auth middleware blocks requests without token."""
    response = client.get('/api/meetings')
    assert response.status_code == 401
    assert response.json['error'] == "Authentication Error"

def test_auth_middleware_invalid_token(client):
    """Test that auth middleware blocks requests with invalid token."""
    response = client.get('/api/meetings', headers={'Authorization': 'Bearer invalid'})
    assert response.status_code == 401
    assert response.json['error'] == "Authentication Error" 