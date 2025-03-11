"""
Tests for the health check endpoint.
"""

def test_health_check(client):
    """Test that the health check endpoint returns 200 OK."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
    assert response.json['service'] == 'auth-service' 