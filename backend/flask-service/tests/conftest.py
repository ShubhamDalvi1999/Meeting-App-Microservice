"""
Test configuration and fixtures for the Flask service.
"""

import os
import sys
import pytest
from flask import Flask
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