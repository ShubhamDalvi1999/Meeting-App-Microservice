"""
Centralized configuration management for the auth service.
Handles environment variables and provides environment-specific settings.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseConfig:
    """Base configuration settings shared across all environments"""
    # Application settings
    APP_NAME = "Auth Service"
    API_PREFIX = "/api"
    
    # Environment settings
    DEBUG = False
    TESTING = False
    
    # Security settings
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SERVICE_KEY = os.environ.get("SERVICE_KEY")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 60 * 60  # 30 days
    BCRYPT_LOG_ROUNDS = 13
    
    # Database settings 
    SQLALCHEMY_DATABASE_URI = os.environ.get("AUTH_DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis settings
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    REDIS_TOKEN_BLACKLIST_DB = 1
    
    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization", "X-Service-Key"]
    
    # Email settings
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = True
    EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "noreply@example.com")
    
    # Frontend settings
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    
    # Authentication settings
    PASSWORD_RESET_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours
    EMAIL_VERIFICATION_TOKEN_EXPIRES = 48 * 60 * 60  # 48 hours
    FAILED_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_TIME = 15 * 60  # 15 minutes
    
    # File paths
    ROOT_DIR = Path("/app")
    LOG_DIR = ROOT_DIR / "logs"
    
    # Ensure directories exist
    LOG_DIR.mkdir(exist_ok=True)

    # OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

class DevelopmentConfig(BaseConfig):
    """Development environment specific configuration"""
    DEBUG = True
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
                                 "http://localhost:3000,http://localhost:3001,http://localhost:5000,http://localhost:5001").split(",")

class TestingConfig(BaseConfig):
    """Testing environment specific configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_AUTH_DATABASE_URL", "sqlite:///:memory:")
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    
    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Shorter token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = 300  # 5 minutes
    JWT_REFRESH_TOKEN_EXPIRES = 600  # 10 minutes
    
    # Mock external services
    REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/2")
    
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
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

# Dictionary of available configurations
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    # Default to development
    "default": DevelopmentConfig
}

def get_config(config_name=None):
    """
    Get the configuration for the current environment.
    
    Args:
        config_name: Optional configuration name override
        
    Returns:
        Configuration class
    """
    if not config_name:
        config_name = os.environ.get("FLASK_ENV", "development").lower()
    
    selected_config = config.get(config_name, config["default"])
    logger.info(f"Using '{config_name}' configuration for auth service")
    
    # Validate critical settings
    if not selected_config.SECRET_KEY and config_name == "production":
        logger.critical("JWT_SECRET_KEY not set in production environment!")
    
    if not selected_config.SQLALCHEMY_DATABASE_URI:
        logger.critical("AUTH_DATABASE_URL not set! Application may fail to start")
    
    return selected_config 