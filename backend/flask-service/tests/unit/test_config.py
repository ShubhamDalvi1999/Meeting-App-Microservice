"""
Tests for shared configuration functionality.
"""

import os
import pytest
from meeting_shared.config import get_config, BaseConfig

def test_base_config():
    """Test base configuration settings."""
    config = BaseConfig()
    
    assert config.DEBUG is False
    assert config.TESTING is False
    assert config.ENV == 'production'
    assert config.API_PREFIX == "/api"
    assert isinstance(config.CORS_ORIGINS, list)
    assert isinstance(config.CORS_METHODS, list)

def test_development_config():
    """Test development configuration settings."""
    os.environ['FLASK_ENV'] = 'development'
    config = get_config('development')
    
    assert config.DEBUG is True
    assert config.ENV == 'development'
    assert config.LOG_LEVEL == "DEBUG"
    assert config.SQLALCHEMY_ECHO is True

def test_testing_config():
    """Test testing configuration settings."""
    config = get_config('testing')
    
    assert config.TESTING is True
    assert config.DEBUG is True
    assert config.ENV == 'testing'
    assert config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"
    assert config.WTF_CSRF_ENABLED is False

def test_production_config():
    """Test production configuration settings."""
    config = get_config('production')
    
    assert config.DEBUG is False
    assert config.ENV == 'production'
    assert config.LOG_LEVEL == "INFO"
    assert config.WTF_CSRF_SSL_STRICT is True
    assert config.PREFERRED_URL_SCHEME == 'https'

def test_service_specific_config():
    """Test service-specific configuration."""
    # Test Flask service config
    flask_config = get_config('development')
    assert flask_config.APP_NAME == "Meeting API Service"
    
    # Test Auth service config
    auth_config = get_config('development')
    assert auth_config.APP_NAME == "Auth Service"

def test_environment_override():
    """Test environment variable overrides."""
    os.environ['SECRET_KEY'] = 'test-secret'
    os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
    os.environ['SERVICE_KEY'] = 'test-service-key'
    
    config = get_config('development')
    
    assert config.SECRET_KEY == 'test-secret'
    assert config.JWT_SECRET_KEY == 'test-jwt-secret'
    assert config.SERVICE_KEY == 'test-service-key' 