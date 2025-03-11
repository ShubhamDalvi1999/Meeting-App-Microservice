"""
Integration tests for the health check endpoints in the Flask service.
"""

import pytest
import json
import re
from unittest.mock import patch

# Add pytest mark for test categories
pytestmark = [pytest.mark.integration, pytest.mark.api]


class TestHealthCheck:
    """Integration tests for the health check endpoints."""
    
    def test_basic_health_check(self, client, mock_request_id):
        """Test the basic health check endpoint."""
        response = client.get('/health', headers={'X-Request-ID': mock_request_id})
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'version' in data
        assert 'timestamp' in data
        assert data['request_id'] == mock_request_id
    
    def test_database_health_check(self, client, db):
        """Test the database health check endpoint."""
        # Call the database health check endpoint
        response = client.get('/health/database')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'database' in data
        assert data['database']['status'] == 'ok'
        assert 'response_time_ms' in data['database']
        
        # Verify that the response time is a reasonable value
        response_time = data['database']['response_time_ms']
        assert isinstance(response_time, (int, float))
        assert response_time >= 0
    
    def test_database_health_check_failure(self, client, db):
        """Test the database health check when the database is down."""
        # Mock the database connection to simulate failure
        with patch('src.core.health.check_database_connection') as mock_check_db:
            mock_check_db.return_value = {
                'status': 'error',
                'error': 'Database connection failed',
                'response_time_ms': 0
            }
            
            # Call the database health check endpoint
            response = client.get('/health/database')
            
            # Even though the database is down, the endpoint should still return a 200
            # but with status indicating error
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            
            data = json.loads(response.data)
            assert data['status'] == 'error'  # Overall status is error
            assert 'database' in data
            assert data['database']['status'] == 'error'
            assert 'error' in data['database']
            assert data['database']['error'] == 'Database connection failed'
    
    def test_auth_service_health_check(self, client, mock_auth_service):
        """Test the auth service health check endpoint."""
        # Mock the auth service health endpoint
        mock_auth_service.add_response(
            method='GET',
            url='/health',
            json={
                'status': 'ok',
                'version': '1.0.0',
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Call the service health check endpoint
        response = client.get('/health/services')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'services' in data
        assert 'auth' in data['services']
        assert data['services']['auth']['status'] == 'ok'
        assert 'response_time_ms' in data['services']['auth']
        
        # Verify that the response time is a reasonable value
        response_time = data['services']['auth']['response_time_ms']
        assert isinstance(response_time, (int, float))
        assert response_time >= 0
    
    def test_auth_service_health_check_failure(self, client, mock_auth_service):
        """Test the auth service health check when the service is down."""
        # Mock the auth service to return a 503 Service Unavailable
        mock_auth_service.add_response(
            method='GET',
            url='/health',
            status=503,
            json={
                'status': 'error',
                'message': 'Service Unavailable',
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Call the service health check endpoint
        response = client.get('/health/services')
        
        # Even though the auth service is down, the endpoint should still return a 200
        # but with status indicating error
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert data['status'] == 'error'  # Overall status is error
        assert 'services' in data
        assert 'auth' in data['services']
        assert data['services']['auth']['status'] == 'error'
        assert 'error' in data['services']['auth']
    
    def test_complete_health_check(self, client, db, mock_auth_service):
        """Test the complete health check endpoint."""
        # Mock the auth service health endpoint
        mock_auth_service.add_response(
            method='GET',
            url='/health',
            json={
                'status': 'ok',
                'version': '1.0.0',
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Call the complete health check endpoint
        response = client.get('/health/complete')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'version' in data
        assert 'timestamp' in data
        assert 'database' in data
        assert data['database']['status'] == 'ok'
        assert 'services' in data
        assert 'auth' in data['services']
        assert data['services']['auth']['status'] == 'ok'
        
        # Verify that there's a dependency graph in the response
        assert 'dependencies' in data
        assert isinstance(data['dependencies'], list)
    
    def test_health_request_id(self, client, mock_request_id):
        """Test that health check endpoints include request IDs."""
        response = client.get('/health', headers={'X-Request-ID': mock_request_id})
        
        assert response.status_code == 200
        
        # Check response headers
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == mock_request_id
        
        # Check request ID in the response body
        data = json.loads(response.data)
        assert 'request_id' in data
        assert data['request_id'] == mock_request_id
    
    def test_health_metrics(self, client):
        """Test that health check endpoints include performance metrics."""
        response = client.get('/health/metrics')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'metrics' in data
        
        # Should include system metrics
        metrics = data['metrics']
        assert 'cpu' in metrics
        assert 'memory' in metrics
        assert 'uptime' in metrics
        
        # Check uptime format
        assert re.match(r'^\d+d \d+h \d+m \d+s$', metrics['uptime'])
    
    def test_health_status_degraded(self, client, mock_auth_service):
        """Test health check with degraded status."""
        # Mock the auth service to be degraded
        mock_auth_service.add_response(
            method='GET',
            url='/health',
            json={
                'status': 'degraded',
                'message': 'High latency',
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Call the service health check endpoint
        response = client.get('/health/services')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'degraded'
        assert 'services' in data
        assert 'auth' in data['services']
        assert data['services']['auth']['status'] == 'degraded'
        assert 'message' in data['services']['auth']
        assert 'High latency' in data['services']['auth']['message'] 