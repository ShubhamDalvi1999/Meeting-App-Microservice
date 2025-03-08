"""
Base utilities for integration testing between services
"""

import os
import json
import pytest
import requests
import time
from datetime import datetime, timedelta
import jwt

# Test configuration
DEFAULT_CONFIG = {
    'AUTH_SERVICE_URL': os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001'),
    'BACKEND_URL': os.environ.get('BACKEND_URL', 'http://localhost:5000'),
    'WEBSOCKET_URL': os.environ.get('WEBSOCKET_URL', 'ws://localhost:3001'),
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'test-secret-key'),
    'SERVICE_KEY': os.environ.get('SERVICE_KEY', 'test-service-key'),
    'TEST_USER_EMAIL': 'test@example.com',
    'TEST_USER_PASSWORD': 'Test123!',
    'TEST_ADMIN_EMAIL': 'admin@example.com',
    'TEST_ADMIN_PASSWORD': 'Admin123!',
    'TIMEOUT': 10  # seconds
}

class IntegrationTestBase:
    """
    Base class for all integration tests providing common functionality
    """
    
    @classmethod
    def setup_class(cls):
        """Set up test environment once for the whole class"""
        cls.config = DEFAULT_CONFIG.copy()
        cls.auth_url = cls.config['AUTH_SERVICE_URL']
        cls.api_url = cls.config['BACKEND_URL']
        cls.ws_url = cls.config['WEBSOCKET_URL']
        cls.service_key = cls.config['SERVICE_KEY']
        cls.timeout = cls.config['TIMEOUT']
        
        # Ensure services are available
        cls._wait_for_services()
        
        # Create test users if they don't exist
        cls._ensure_test_users()
    
    @classmethod
    def _wait_for_services(cls):
        """Wait for all services to be available"""
        services = [
            ('auth', f"{cls.auth_url}/health"),
            ('backend', f"{cls.api_url}/health"),
        ]
        
        for name, url in services:
            start_time = time.time()
            while time.time() - start_time < cls.timeout:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"Service {name} is available")
                        break
                except requests.RequestException:
                    pass
                
                print(f"Waiting for {name} service to be available...")
                time.sleep(1)
            else:
                pytest.fail(f"Service {name} not available after {cls.timeout} seconds")
    
    @classmethod
    def _ensure_test_users(cls):
        """Create test users if they don't exist"""
        # Test regular user
        cls._create_or_get_user(
            cls.config['TEST_USER_EMAIL'],
            cls.config['TEST_USER_PASSWORD'],
            ['user']
        )
        
        # Test admin user
        cls._create_or_get_user(
            cls.config['TEST_ADMIN_EMAIL'],
            cls.config['TEST_ADMIN_PASSWORD'],
            ['user', 'admin']
        )
    
    @classmethod
    def _create_or_get_user(cls, email, password, roles=None):
        """Create a user or get existing user"""
        # Check if user exists
        login_response = cls.login(email, password)
        if login_response.status_code == 200:
            return login_response.json()
        
        # User doesn't exist, create it
        url = f"{cls.auth_url}/api/auth/register"
        data = {
            'email': email,
            'password': password,
            'name': email.split('@')[0].title()
        }
        
        # Create user
        response = requests.post(url, json=data, timeout=cls.timeout)
        if response.status_code != 201:
            pytest.fail(f"Failed to create test user: {response.text}")
        
        # If roles specified and not the default 'user', update roles using service key
        if roles and set(roles) != {'user'}:
            cls._update_user_roles(email, roles)
        
        # Login to get tokens
        return cls.login(email, password).json()
    
    @classmethod
    def _update_user_roles(cls, email, roles):
        """Update user roles using service key"""
        url = f"{cls.auth_url}/api/internal/users/roles"
        headers = {'X-Service-Key': cls.service_key}
        data = {'email': email, 'roles': roles}
        
        response = requests.put(url, headers=headers, json=data, timeout=cls.timeout)
        if response.status_code != 200:
            pytest.fail(f"Failed to update user roles: {response.text}")
    
    @staticmethod
    def login(email, password):
        """Login and get access token"""
        url = f"{DEFAULT_CONFIG['AUTH_SERVICE_URL']}/api/auth/login"
        data = {'email': email, 'password': password}
        
        return requests.post(url, json=data, timeout=DEFAULT_CONFIG['TIMEOUT'])
    
    @staticmethod
    def get_headers(access_token):
        """Get standard authorization headers"""
        return {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def get_service_headers():
        """Get service-to-service authorization headers"""
        return {
            'X-Service-Key': DEFAULT_CONFIG['SERVICE_KEY'],
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def generate_test_token(user_id, email, roles=None):
        """Generate a test JWT token for a user"""
        roles = roles or ['user']
        payload = {
            'sub': str(user_id),
            'email': email,
            'roles': roles,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(
            payload, 
            DEFAULT_CONFIG['JWT_SECRET_KEY'], 
            algorithm='HS256'
        ) 