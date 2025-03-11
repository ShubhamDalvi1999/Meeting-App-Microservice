"""
Test configuration and fixtures for the Auth service.
"""

import os
import sys
import pytest
import logging
from flask import Flask
import json
import tempfile
import responses
from typing import Dict, Any, Generator, Callable
from flask.testing import FlaskClient

# Add source directories to Python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(BASE_DIR, "src")
SHARED_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "meeting_shared"))

for path in [SRC_DIR, SHARED_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import after path setup
from src.app import create_app
from meeting_shared.config import get_config
from meeting_shared.database import db as _db

# Setup logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def app() -> Flask:
    """Create a Flask application for testing."""
    # Use testing configuration
    app = create_app("testing")
    
    # Create tables
    with app.app_context():
        _db.create_all()
    
    yield app
    
    # Clean up
    with app.app_context():
        _db.drop_all()

@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Create a test client."""
    return app.test_client()

@pytest.fixture(scope="function")
def db(app: Flask):
    """Create a clean database for each test."""
    with app.app_context():
        _db.create_all()
        
    yield _db
    
    with app.app_context():
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope="function")
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    yield db.session
    
    transaction.rollback()
    connection.close()
    db.session.remove()

@pytest.fixture(scope="function")
def test_user(db, app: Flask):
    """Create a test user."""
    from src.models.user import User
    
    user_data = {
        'email': 'test@example.com',
        'password': 'test_password',
        'name': 'Test User',
        'is_active': True
    }
    
    with app.app_context():
        user = User(**user_data)
        user.set_password(user_data['password'])
        db.session.add(user)
        db.session.commit()
        
        user_data['id'] = user.id
        return user_data

@pytest.fixture(scope="function")
def admin_user(db, app: Flask) -> Dict[str, Any]:
    """
    Create an admin test user in the database.
    
    Args:
        db: Database fixture
        app: Flask application fixture
        
    Returns:
        dict: Admin user data
    """
    from src.models.user import User
    from src.services.auth_service import hash_password
    
    user_data = {
        'email': 'admin@example.com',
        'password': 'AdminPass123!',
        'name': 'Admin User',
        'is_admin': True
    }
    
    with app.app_context():
        # Create user
        user = User(
            email=user_data['email'],
            name=user_data['name'],
            password_hash=hash_password(user_data['password']),
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Return user data with ID
        user_data['id'] = user.id
        return user_data

@pytest.fixture(scope="function")
def access_token(app: Flask, test_user: Dict[str, Any]) -> str:
    """
    Generate an access token for the test user.
    
    Args:
        app: Flask application fixture
        test_user: Test user fixture
        
    Returns:
        str: JWT access token
    """
    from src.services.token_service import create_access_token
    
    with app.app_context():
        return create_access_token(identity=test_user['id'])

@pytest.fixture(scope="function")
def refresh_token(app: Flask, test_user: Dict[str, Any]) -> str:
    """
    Generate a refresh token for the test user.
    
    Args:
        app: Flask application fixture
        test_user: Test user fixture
        
    Returns:
        str: JWT refresh token
    """
    from src.services.token_service import create_refresh_token
    
    with app.app_context():
        return create_refresh_token(identity=test_user['id'])

@pytest.fixture(scope="function")
def service_token(app: Flask) -> str:
    """
    Generate a service token for service-to-service communication.
    
    Args:
        app: Flask application fixture
        
    Returns:
        str: JWT service token
    """
    from src.services.token_service import create_service_token
    
    with app.app_context():
        return create_service_token(issuer='auth-service', audience='test-service')

@pytest.fixture(scope="function")
def auth_header(access_token: str) -> Dict[str, str]:
    """
    Create an authorization header with the access token.
    
    Args:
        access_token: JWT access token fixture
        
    Returns:
        dict: Authorization header
    """
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture(scope="function")
def service_auth_header(service_token: str) -> Dict[str, str]:
    """
    Create an authorization header with the service token.
    
    Args:
        service_token: JWT service token fixture
        
    Returns:
        dict: Authorization header
    """
    return {'Authorization': f'Bearer {service_token}'}

@pytest.fixture(scope="function")
def mock_responses():
    """
    Set up and tear down mocked responses.
    
    Returns:
        responses.RequestsMock: Mocked responses
    """
    with responses.RequestsMock() as rsps:
        yield rsps

@pytest.fixture(scope="function")
def capture_logs(caplog) -> Generator[None, None, None]:
    """
    Capture logs during test execution.
    
    Args:
        caplog: Pytest's built-in caplog fixture
        
    Returns:
        Generator: Yields control to the test and then performs assertions
    """
    # Set up
    caplog.set_level(logging.INFO)
    
    # Run test
    yield
    
    # Tear down - do any log analysis here if needed
    logger.debug(f"Captured {len(caplog.records)} log records")

@pytest.fixture(scope="function")
def mock_request_id() -> Generator[str, None, None]:
    """
    Mock a request ID for testing.
    
    Returns:
        str: Mocked request ID
    """
    request_id = "test-request-id-123456"
    
    # Patch the request_id module to return our test ID
    try:
        import src.core.logging as logging_module
        original_get_request_id = getattr(logging_module, 'get_request_id', None)
        setattr(logging_module, 'get_request_id', lambda: request_id)
    except (ImportError, AttributeError):
        pass
    
    # Also try middleware module if it exists
    try:
        import src.middleware.request_id as request_id_module
        original_get_request_id_middleware = getattr(request_id_module, 'get_request_id', None)
        setattr(request_id_module, 'get_request_id', lambda: request_id)
    except (ImportError, AttributeError):
        pass
    
    yield request_id
    
    # Restore original function if needed
    if original_get_request_id:
        setattr(logging_module, 'get_request_id', original_get_request_id)
    
    if original_get_request_id_middleware:
        setattr(request_id_module, 'get_request_id', original_get_request_id_middleware) 