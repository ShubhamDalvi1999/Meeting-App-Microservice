"""
Standardized error handling for backend services.
Provides common error classes and utilities for consistent error responses.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import request ID functionality
try:
    from meeting_shared.middleware.request_id import get_request_id
    HAS_REQUEST_ID = True
except ImportError:
    HAS_REQUEST_ID = False

class APIError(Exception):
    """Base exception class for API errors with status code and message"""
    
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Add request ID if available
        if HAS_REQUEST_ID:
            self.request_id = get_request_id()
        else:
            self.request_id = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary representation.
        
        Returns:
            Dictionary with error details
        """
        error_dict = {
            'error': True,
            'status_code': self.status_code,
            'message': self.message,
            'timestamp': self.timestamp
        }
        
        # Include request ID if available
        if hasattr(self, 'request_id') and self.request_id:
            error_dict['request_id'] = self.request_id
        
        # Include additional details if provided
        if self.details:
            error_dict['details'] = self.details
        
        return error_dict

# --- User and Authentication Errors ---

class ValidationError(APIError):
    """Exception for data validation errors"""
    
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)

class AuthenticationError(APIError):
    """Exception for authentication failures"""
    
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)

class AuthorizationError(APIError):
    """Exception for authorization failures"""
    
    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)

class UserExistsError(APIError):
    """Exception for duplicate user registration"""
    
    def __init__(self, message: str = "User already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)

class UserNotFoundError(APIError):
    """Exception for user not found"""
    
    def __init__(self, message: str = "User not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)

class TokenError(APIError):
    """Exception for token validation failures"""
    
    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)

# --- Resource Errors ---

class ResourceNotFoundError(APIError):
    """Exception for resource not found"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)

class ResourceExistsError(APIError):
    """Exception for duplicate resource"""
    
    def __init__(self, message: str = "Resource already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)

# --- Service Errors ---

class ServiceError(APIError):
    """Exception for service failures"""
    
    def __init__(self, message: str = "Service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

class ConfigurationError(APIError):
    """Exception for configuration errors"""
    
    def __init__(self, message: str = "Configuration error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

class DependencyError(APIError):
    """Exception for dependency failures"""
    
    def __init__(self, message: str = "Dependency error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, details=details)

class RateLimitError(APIError):
    """Exception for rate limiting"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, details=details)

class EmailError(APIError):
    """Exception for email sending failures"""
    
    def __init__(self, message: str = "Failed to send email", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

# Export all error classes
__all__ = [
    'APIError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'UserExistsError',
    'UserNotFoundError',
    'TokenError',
    'ResourceNotFoundError',
    'ResourceExistsError',
    'ServiceError',
    'ConfigurationError',
    'DependencyError',
    'RateLimitError',
    'EmailError',
] 