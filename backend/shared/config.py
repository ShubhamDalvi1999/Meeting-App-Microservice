"""
Standardized configuration module for backend services.
Provides consistent configuration across different services.
"""

import os
from pathlib import Path

class BaseConfig:
    """Base configuration settings shared across all environments"""
    # Environment settings
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Application settings
    API_PREFIX = "/api"
    
    # Security settings
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SERVICE_KEY = os.environ.get("SERVICE_KEY")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 60 * 60  # 30 days
    BCRYPT_LOG_ROUNDS = 13
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis settings
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    REDIS_TOKEN_BLACKLIST_DB = 1
    
    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization", "X-Service-Key", "X-Request-ID", "X-Correlation-ID"]
    
    # Logging settings
    LOG_LEVEL = "INFO"
    JSON_LOGS = os.environ.get("JSON_LOGS", "true").lower() == "true"
    LOG_TO_FILE = os.environ.get("LOG_TO_FILE", "false").lower() == "true"
    LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")
    
    # Service discovery settings
    SERVICE_DISCOVERY_PROVIDER = os.environ.get("SERVICE_DISCOVERY_PROVIDER", "env")
    
    # Secret management settings
    SECRET_MANAGER_TYPE = os.environ.get("SECRET_MANAGER_TYPE", "env")
    
    # File paths
    ROOT_DIR = Path("/app")
    LOG_DIR = ROOT_DIR / "logs"
    
    # Ensure directories exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Service URLs
    AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:5001")
    BACKEND_SERVICE_URL = os.environ.get("BACKEND_SERVICE_URL", "http://backend:5000")
    WEBSOCKET_SERVICE_URL = os.environ.get("WEBSOCKET_SERVICE_URL", "http://websocket:3001")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


class DevelopmentConfig(BaseConfig):
    """Development environment specific configuration"""
    DEBUG = True
    ENV = 'development'
    LOG_LEVEL = "DEBUG"
    
    # More lenient security settings for development
    BCRYPT_LOG_ROUNDS = 4
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours in development
    
    # Enable detailed error messages and SQL query logging
    SQLALCHEMY_ECHO = True
    
    # Development-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
    # Extended CORS settings for development
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", 
                                "http://localhost:3000,http://127.0.0.1:3000").split(",")


class TestingConfig(BaseConfig):
    """Testing environment specific configuration"""
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    
    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Shorter token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = 300  # 5 minutes
    JWT_REFRESH_TOKEN_EXPIRES = 600  # 10 minutes
    
    # Mock external services
    REDIS_URL = "redis://localhost:6379/2"
    
    # Disable email sending in tests
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(BaseConfig):
    """Production environment specific configuration"""
    LOG_LEVEL = "INFO"
    
    # Production security settings
    WTF_CSRF_SSL_STRICT = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Set stricter CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "https://yourdomain.com").split(",")
    
    # Production database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 15
    }
    
    # Enhanced logging for production
    LOG_TO_FILE = True


class AuthServiceConfig(BaseConfig):
    """Auth service specific configuration"""
    APP_NAME = "Auth Service"
    SQLALCHEMY_DATABASE_URI = os.environ.get("AUTH_DATABASE_URL")
    OAUTH_PROVIDERS = {
        'google': {
            'client_id': os.environ.get("GOOGLE_CLIENT_ID"),
            'client_secret': os.environ.get("GOOGLE_CLIENT_SECRET")
        }
    }


class FlaskServiceConfig(BaseConfig):
    """Flask service specific configuration"""
    APP_NAME = "Meeting API Service"
    SQLALCHEMY_DATABASE_URI = os.environ.get("BACKEND_DATABASE_URL")


class WebsocketServiceConfig(BaseConfig):
    """Websocket service specific configuration"""
    APP_NAME = "Websocket Service"
    WEBSOCKET_PORT = int(os.environ.get("WEBSOCKET_PORT", 3001))


# Config dictionary mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'auth': AuthServiceConfig,
    'flask': FlaskServiceConfig,
    'websocket': WebsocketServiceConfig,
}


def get_config(env_name=None):
    """
    Get configuration based on environment name.
    
    Args:
        env_name: Environment name ('development', 'testing', 'production')
        
    Returns:
        Configuration class
    """
    if not env_name:
        env_name = os.environ.get('FLASK_ENV', 'development')
    
    # Combine service-specific config with env-specific config
    service_type = os.environ.get('SERVICE_TYPE', 'default')
    base_config = config.get(env_name, config['default'])
    service_config = config.get(service_type, config['default'])
    
    # Create a new config class that inherits from both
    class CombinedConfig(service_config, base_config):
        pass
    
    return CombinedConfig 