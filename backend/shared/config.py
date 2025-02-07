import os
from datetime import timedelta

class BaseConfig:
    """Base configuration for all environments"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # CORS
    CORS_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization", "X-Service-Key", "X-CSRF-Token"]
    
    # Service Integration
    SERVICE_KEY = os.getenv('SERVICE_KEY', 'your-service-key')
    AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:5001')
    FLASK_SERVICE_URL = os.getenv('FLASK_SERVICE_URL', 'http://backend:5000')
    
    # JWT Settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT = 100  # requests per minute
    RATE_LIMIT_AUTH = 5  # auth requests per minute
    
    # Session
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    
    # Disable secure cookies in development
    SESSION_COOKIE_SECURE = False

class TestingConfig(BaseConfig):
    """Testing configuration"""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///test.db')
    
    # Disable secure cookies in testing
    SESSION_COOKIE_SECURE = False
    
    # Increase rate limits for testing
    RATE_LIMIT_DEFAULT = 1000
    RATE_LIMIT_AUTH = 100

class ProductionConfig(BaseConfig):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Stricter security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Lower rate limits for production
    RATE_LIMIT_DEFAULT = 60
    RATE_LIMIT_AUTH = 3

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 