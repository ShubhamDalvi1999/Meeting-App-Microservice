"""
Integration tests for the authentication flow.
Tests the complete authentication flow including registration, login, and token refresh.
"""

import json
import os
import requests
from .base import IntegrationTestBase
import responses

class TestAuthFlow(IntegrationTestBase):
    """Test the complete authentication flow."""
    
    def create_app(self):
        """Create the Flask application for testing."""
        # Import here to avoid circular imports
        import sys
        import os
        
        # Add the src directory to the path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
        
        # Import the create_app function
        from src.app import create_app
        
        # Create the app with test configuration
        app = create_app('testing')
        
        # Override any config settings
        app.config.update(self.TEST_CONFIG)
        
        return app
    
    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        
        # Set up the database
        from src.models import db
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up the test environment."""
        # Clean up the database
        from src.models import db
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        super().tearDown()
    
    def test_registration_login_refresh_flow(self):
        """Test the complete authentication flow."""
        # 1. Register a new user
        registration_data = {
            'email': 'test@example.com',
            'password': 'Password123!',
            'name': 'Test User'
        }
        
        register_response = self.client.post(
            '/auth/register',
            json=registration_data
        )
        
        self.assert_response_status(register_response, 201)
        register_data = json.loads(register_response.data.decode('utf-8'))
        self.assertIn('message', register_data)
        self.assertIn('user', register_data)
        self.assertEqual(register_data['user']['email'], registration_data['email'])
        
        # 2. Login with the new user
        login_data = {
            'email': registration_data['email'],
            'password': registration_data['password']
        }
        
        login_response = self.client.post(
            '/auth/login',
            json=login_data
        )
        
        self.assert_response_status(login_response, 200)
        login_data = json.loads(login_response.data.decode('utf-8'))
        self.assertIn('access_token', login_data)
        self.assertIn('refresh_token', login_data)
        
        access_token = login_data['access_token']
        refresh_token = login_data['refresh_token']
        
        # 3. Access a protected endpoint
        me_response = self.client.get(
            '/auth/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        self.assert_response_status(me_response, 200)
        me_data = json.loads(me_response.data.decode('utf-8'))
        self.assertIn('user', me_data)
        self.assertEqual(me_data['user']['email'], registration_data['email'])
        
        # 4. Refresh the token
        refresh_response = self.client.post(
            '/auth/refresh',
            headers={'Authorization': f'Bearer {refresh_token}'}
        )
        
        self.assert_response_status(refresh_response, 200)
        refresh_data = json.loads(refresh_response.data.decode('utf-8'))
        self.assertIn('access_token', refresh_data)
        
        new_access_token = refresh_data['access_token']
        
        # 5. Access a protected endpoint with the new token
        me_response_2 = self.client.get(
            '/auth/me',
            headers={'Authorization': f'Bearer {new_access_token}'}
        )
        
        self.assert_response_status(me_response_2, 200)
        me_data_2 = json.loads(me_response_2.data.decode('utf-8'))
        self.assertIn('user', me_data_2)
        self.assertEqual(me_data_2['user']['email'], registration_data['email'])
    
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        # 1. Register a new user
        registration_data = {
            'email': 'test2@example.com',
            'password': 'Password123!',
            'name': 'Test User 2'
        }
        
        register_response = self.client.post(
            '/auth/register',
            json=registration_data
        )
        
        self.assert_response_status(register_response, 201)
        
        # 2. Try to login with incorrect password
        login_data = {
            'email': registration_data['email'],
            'password': 'WrongPassword123!'
        }
        
        login_response = self.client.post(
            '/auth/login',
            json=login_data
        )
        
        self.assert_response_status(login_response, 401)
        login_data = json.loads(login_response.data.decode('utf-8'))
        self.assertIn('message', login_data)
        self.assertIn('error', login_data)
    
    def test_token_validation(self):
        """Test token validation."""
        # 1. Register and login a user
        registration_data = {
            'email': 'test3@example.com',
            'password': 'Password123!',
            'name': 'Test User 3'
        }
        
        self.client.post('/auth/register', json=registration_data)
        
        login_response = self.client.post(
            '/auth/login',
            json={
                'email': registration_data['email'],
                'password': registration_data['password']
            }
        )
        
        login_data = json.loads(login_response.data.decode('utf-8'))
        access_token = login_data['access_token']
        
        # 2. Validate the token
        validate_response = self.client.post(
            '/auth/validate',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        self.assert_response_status(validate_response, 200)
        validate_data = json.loads(validate_response.data.decode('utf-8'))
        self.assertIn('valid', validate_data)
        self.assertTrue(validate_data['valid'])
        
        # 3. Validate an invalid token
        invalid_token = "invalid.token.here"
        invalid_validate_response = self.client.post(
            '/auth/validate',
            headers={'Authorization': f'Bearer {invalid_token}'}
        )
        
        self.assert_response_status(invalid_validate_response, 401)
    
    def test_service_to_service_auth(self):
        """Test service-to-service authentication."""
        # Mock the service authentication endpoint
        self.mock_service_response(
            service='backend',
            endpoint='/api/internal/auth',
            method='POST',
            status=200,
            json_data={'authenticated': True, 'service': 'backend'}
        )
        
        # Create a service token
        with self.app.app_context():
            from src.utils.token_service import create_service_token
            service_token = create_service_token('auth-service', 'backend')
        
        # Call the backend service with the service token
        response = requests.post(
            f"{os.environ.get('BACKEND_SERVICE_URL')}/api/internal/auth",
            headers={'Authorization': f'Bearer {service_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['service'], 'backend') 