"""
Base class for integration tests.
Provides common functionality for setting up and tearing down test environments.
"""

import os
import json
import pytest
import requests
from unittest import TestCase
from flask import Flask
from flask.testing import FlaskClient
import responses
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTestBase(TestCase):
    """
    Base class for integration tests.
    
    This class provides common functionality for setting up and tearing down
    test environments for integration tests. It includes methods for:
    
    - Setting up mock responses for external services
    - Creating test clients for the application
    - Cleaning up resources after tests
    """
    
    # Default configuration for tests
    TEST_CONFIG = {
        'TESTING': True,
        'DEBUG': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test_secret_key',
        'JWT_SECRET_KEY': 'test_jwt_secret',
        'REDIS_URL': 'redis://localhost:6379/1',  # Use a different DB for testing
    }
    
    @classmethod
    def setUpClass(cls):
        """Set up resources before any tests in the class run."""
        super().setUpClass()
        logger.info("Setting up integration test environment")
        
        # Store original environment variables
        cls.original_env = dict(os.environ)
        
        # Set up environment variables for testing
        os.environ.update({
            'FLASK_ENV': 'testing',
            'TESTING': 'true',
            'AUTH_SERVICE_URL': 'http://localhost:5001',
            'BACKEND_SERVICE_URL': 'http://localhost:5000',
            'WEBSOCKET_SERVICE_URL': 'http://localhost:3001',
        })
        
        # Initialize responses for mocking HTTP requests
        responses.start()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests in the class have run."""
        super().tearDownClass()
        logger.info("Tearing down integration test environment")
        
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(cls.original_env)
        
        # Stop responses
        responses.stop()
    
    def setUp(self):
        """Set up resources before each test."""
        super().setUp()
        logger.info(f"Setting up test: {self._testMethodName}")
        
        # Create a test Flask app
        self.app = self.create_app()
        
        # Create a test client
        self.client = self.app.test_client()
        
        # Reset responses between tests
        responses.reset()
    
    def tearDown(self):
        """Clean up resources after each test."""
        super().tearDown()
        logger.info(f"Tearing down test: {self._testMethodName}")
    
    def create_app(self):
        """
        Create a Flask application for testing.
        
        Override this method in subclasses to create a specific application
        for testing.
        
        Returns:
            Flask: A Flask application instance.
        """
        app = Flask(__name__)
        app.config.update(self.TEST_CONFIG)
        return app
    
    def mock_service_response(self, service, endpoint, method='GET', 
                             status=200, json_data=None, body=None, 
                             content_type='application/json', headers=None):
        """
        Mock a response from a service.
        
        Args:
            service: The service name ('auth', 'backend', 'websocket')
            endpoint: The endpoint to mock (e.g., '/api/users')
            method: The HTTP method (default: 'GET')
            status: The HTTP status code (default: 200)
            json_data: JSON data to return (default: None)
            body: Response body if not using json_data (default: None)
            content_type: Content type header (default: 'application/json')
            headers: Additional headers (default: None)
            
        Returns:
            The mocked response.
        """
        # Get service URL from environment
        service_urls = {
            'auth': os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001'),
            'backend': os.environ.get('BACKEND_SERVICE_URL', 'http://localhost:5000'),
            'websocket': os.environ.get('WEBSOCKET_SERVICE_URL', 'http://localhost:3001'),
        }
        
        service_url = service_urls.get(service.lower())
        if not service_url:
            raise ValueError(f"Unknown service: {service}")
        
        # Ensure endpoint starts with a slash
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        url = service_url + endpoint
        
        # Set up headers
        response_headers = {'Content-Type': content_type}
        if headers:
            response_headers.update(headers)
        
        # Set up the mock response
        if json_data is not None:
            body = json.dumps(json_data)
        
        logger.info(f"Mocking {method} request to {url} with status {status}")
        return responses.add(
            method=method,
            url=url,
            body=body,
            status=status,
            headers=response_headers
        )
    
    def assert_response_status(self, response, expected_status):
        """
        Assert that a response has the expected status code.
        
        Args:
            response: The HTTP response
            expected_status: The expected HTTP status code
        """
        self.assertEqual(
            response.status_code, 
            expected_status, 
            f"Expected status {expected_status}, got {response.status_code}. Response: {response.data.decode('utf-8')}"
        )
    
    def assert_response_json(self, response, expected_json):
        """
        Assert that a response contains the expected JSON data.
        
        Args:
            response: The HTTP response
            expected_json: The expected JSON data (can be partial)
        """
        data = json.loads(response.data.decode('utf-8'))
        
        for key, value in expected_json.items():
            self.assertIn(key, data, f"Key '{key}' not found in response")
            self.assertEqual(data[key], value, f"Value for key '{key}' does not match")
    
    def mock_auth_token(self, user_id=1, email='test@example.com', name='Test User', is_admin=False):
        """
        Mock the authentication token validation.
        
        Args:
            user_id: User ID to include in the token (default: 1)
            email: User email (default: 'test@example.com')
            name: User name (default: 'Test User')
            is_admin: Whether the user is an admin (default: False)
            
        Returns:
            str: A mock token
        """
        # Mock the auth service validate endpoint
        self.mock_service_response(
            service='auth',
            endpoint='/auth/validate',
            method='POST',
            status=200,
            json_data={
                'valid': True,
                'user': {
                    'id': user_id,
                    'email': email,
                    'name': name,
                    'is_admin': is_admin
                }
            }
        )
        
        # Return a mock token
        return f"mock_token_{user_id}"
    
    def authenticated_request(self, method, endpoint, json_data=None, headers=None, user_id=1):
        """
        Make an authenticated request to the API.
        
        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint
            json_data: JSON data to send (default: None)
            headers: Additional headers (default: None)
            user_id: User ID to include in the mock token (default: 1)
            
        Returns:
            The HTTP response
        """
        # Mock the auth token
        token = self.mock_auth_token(user_id=user_id)
        
        # Set up headers
        request_headers = {'Authorization': f'Bearer {token}'}
        if headers:
            request_headers.update(headers)
        
        # Make the request
        method_func = getattr(self.client, method.lower())
        return method_func(
            endpoint,
            json=json_data,
            headers=request_headers
        ) 