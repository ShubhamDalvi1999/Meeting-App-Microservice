"""
Centralized configuration management for the application.
Handles environment variables and provides environment-specific settings.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseConfig:
    """Base configuration settings shared across all environments"""
    # Application settings
    APP_NAME = "Meeting API Service"
    API_PREFIX = "/api"
    
    # Environment settings
    DEBUG = False
    TESTING = False
    
    # Security settings
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SERVICE_KEY = os.environ.get("SERVICE_KEY")
    
    # Database settings 
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis settings
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization", "X-Service-Key"]
    
    # Auth Service integration
    AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:5001")
    
    # File paths
    ROOT_DIR = Path("/app")
    LOG_DIR = ROOT_DIR / "logs"
    BACKUP_DIR = ROOT_DIR / "backups"
    
    # Ensure directories exist
    LOG_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)

    # Healthcheck settings
    HEALTH_DATABASE_TIMEOUT = 3  # seconds
    HEALTH_REDIS_TIMEOUT = 2     # seconds

class DevelopmentConfig(BaseConfig):
    """Development environment specific configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    
    # Enable detailed error messages and SQL query logging
    SQLALCHEMY_ECHO = True
    
    # Development-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
    # Extended CORS settings for development
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", 
                                 "http://localhost:3000,http://localhost:3001,http://localhost:5000").split(",")

class TestingConfig(BaseConfig):
    """Testing environment specific configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    
    # Mock external services
    AUTH_SERVICE_URL = os.environ.get("TEST_AUTH_SERVICE_URL", "http://localhost:5001")
    REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/1")

class ProductionConfig(BaseConfig):
    """Production environment specific configuration"""
    LOG_LEVEL = "INFO"
    
    # Production security settings
    WTF_CSRF_SSL_STRICT = True
    
    # Set stricter CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "https://yourdomain.com").split(",")

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
    logger.info(f"Using '{config_name}' configuration")
    
    # Validate critical settings
    if not selected_config.SECRET_KEY and config_name == "production":
        logger.critical("SECRET_KEY not set in production environment!")
    
    if not selected_config.SQLALCHEMY_DATABASE_URI:
        logger.critical("DATABASE_URL not set! Application may fail to start")
    
    return selected_config 