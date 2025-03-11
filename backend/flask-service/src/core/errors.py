"""
Centralized error handling for the Flask service.
Provides standardized error responses and detailed logging of exceptions.
"""

import traceback
import logging
import json
import os
from datetime import datetime
from flask import jsonify, request, current_app

logger = logging.getLogger(__name__)

# Try to import standardized errors from shared module
try:
    # Try to import from backend.meeting_shared first
    from backend.meeting_shared.errors import (
        APIError, ValidationError, AuthenticationError, AuthorizationError,
        UserExistsError, UserNotFoundError, TokenError, ResourceNotFoundError,
        ResourceExistsError, ServiceError, ConfigurationError, DependencyError,
        RateLimitError, EmailError, HAS_REQUEST_ID
    )
    SHARED_ERRORS_AVAILABLE = True
    logger.info("Successfully imported shared error classes")
except ImportError:
    try:
        # Try to import from meeting_shared as fallback
        from meeting_shared.errors import (
            APIError, ValidationError, AuthenticationError, AuthorizationError,
            UserExistsError, UserNotFoundError, TokenError, ResourceNotFoundError,
            ResourceExistsError, ServiceError, ConfigurationError, DependencyError,
            RateLimitError, EmailError, HAS_REQUEST_ID
        )
        SHARED_ERRORS_AVAILABLE = True
        logger.info("Successfully imported shared error classes using fallback path")
    except ImportError:
        SHARED_ERRORS_AVAILABLE = False
        logger.warning("Could not import shared error classes, using local definitions")
        
        # Try to import request ID functionality
        try:
            from backend.meeting_shared.middleware.request_id import get_request_id
            HAS_REQUEST_ID = True
        except ImportError:
            try:
                from meeting_shared.middleware.request_id import get_request_id
                HAS_REQUEST_ID = True
            except ImportError:
                HAS_REQUEST_ID = False

        # Define error classes locally if shared module is not available
        class APIError(Exception):
            """Base exception class for API errors with status code and message"""
            
            def __init__(self, message, status_code=400, details=None):
                self.message = message
                self.status_code = status_code
                self.details = details or {}
                self.timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Add request ID if available
                if HAS_REQUEST_ID:
                    self.request_id = get_request_id()
                else:
                    self.request_id = None
            
            def to_dict(self):
                """Convert exception to dictionary representation"""
                error_dict = {
                    'error': True,
                    'status_code': self.status_code,
                    'message': self.message,
                    'timestamp': self.timestamp
                }
                
                # Include request ID if available
                if hasattr(self, 'request_id') and self.request_id:
                    error_dict['request_id'] = self.request_id
                
                # Include request URL and method if in a request context
                try:
                    error_dict['path'] = request.path
                    error_dict['method'] = request.method
                except RuntimeError:
                    # Not in a request context
                    pass
                
                # Include additional details if provided
                if self.details:
                    error_dict['details'] = self.details
                
                return error_dict

        class ValidationError(APIError):
            """Exception for data validation errors"""
            
            def __init__(self, message="Validation error", details=None):
                super().__init__(message, status_code=422, details=details)

        class AuthenticationError(APIError):
            """Exception for authentication failures"""
            
            def __init__(self, message="Authentication required", details=None):
                super().__init__(message, status_code=401, details=details)

        class AuthorizationError(APIError):
            """Exception for authorization failures"""
            
            def __init__(self, message="Not authorized", details=None):
                super().__init__(message, status_code=403, details=details)

        class ResourceNotFoundError(APIError):
            """Exception for resource not found"""
            
            def __init__(self, message="Resource not found", details=None):
                super().__init__(message, status_code=404, details=details)

        class ResourceExistsError(APIError):
            """Exception for duplicate resource"""
            
            def __init__(self, message="Resource already exists", details=None):
                super().__init__(message, status_code=409, details=details)

        class RateLimitError(APIError):
            """Exception for rate limiting"""
            
            def __init__(self, message="Rate limit exceeded", details=None):
                super().__init__(message, status_code=429, details=details)

        class ServiceError(APIError):
            """Exception for service failures"""
            
            def __init__(self, message="Service error", details=None):
                super().__init__(message, status_code=500, details=details)

        class ConfigurationError(APIError):
            """Exception for configuration errors"""
            
            def __init__(self, message="Configuration error", details=None):
                super().__init__(message, status_code=500, details=details)

        class DependencyError(APIError):
            """Exception for dependency failures"""
            
            def __init__(self, message="Dependency error", details=None):
                super().__init__(message, status_code=503, details=details)
                
        class UserExistsError(APIError):
            """Exception for duplicate user registration"""
            
            def __init__(self, message="User already exists", details=None):
                super().__init__(message, status_code=409, details=details)
                
        class UserNotFoundError(APIError):
            """Exception for user not found"""
            
            def __init__(self, message="User not found", details=None):
                super().__init__(message, status_code=404, details=details)
                
        class TokenError(APIError):
            """Exception for token validation failures"""
            
            def __init__(self, message="Invalid or expired token", details=None):
                super().__init__(message, status_code=401, details=details)
                
        class EmailError(APIError):
            """Exception for email sending failures"""
            
            def __init__(self, message="Failed to send email", details=None):
                super().__init__(message, status_code=500, details=details)

def register_error_handlers(app):
    """
    Register all error handlers with the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Custom exceptions
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(ValidationError, handle_api_error)
    app.register_error_handler(AuthenticationError, handle_api_error)
    app.register_error_handler(AuthorizationError, handle_api_error)
    app.register_error_handler(ResourceNotFoundError, handle_api_error)
    app.register_error_handler(ResourceExistsError, handle_api_error)
    app.register_error_handler(RateLimitError, handle_api_error)
    app.register_error_handler(ServiceError, handle_api_error)
    app.register_error_handler(ConfigurationError, handle_api_error)
    app.register_error_handler(DependencyError, handle_api_error)
    app.register_error_handler(UserExistsError, handle_api_error)
    app.register_error_handler(UserNotFoundError, handle_api_error)
    app.register_error_handler(TokenError, handle_api_error)
    app.register_error_handler(EmailError, handle_api_error)
    
    # Standard HTTP errors
    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(401, handle_unauthorized)
    app.register_error_handler(403, handle_forbidden)
    app.register_error_handler(404, handle_not_found)
    app.register_error_handler(405, handle_method_not_allowed)
    app.register_error_handler(422, handle_unprocessable_entity)
    app.register_error_handler(429, handle_rate_limit_exceeded)
    app.register_error_handler(500, handle_server_error)
    
    # Catch-all for any other exceptions
    app.register_error_handler(Exception, handle_exception)
    
    logger.info("Registered error handlers")

def handle_api_error(error):
    """
    Handler for API errors.
    
    Args:
        error: APIError instance
        
    Returns:
        JSON response with error details
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    
    # Add request ID header if available
    if hasattr(error, 'request_id') and error.request_id:
        response.headers['X-Request-ID'] = error.request_id
    
    # Log the error
    if error.status_code >= 500:
        logger.error(f"API Error: {error.message}", extra={'status_code': error.status_code})
    else:
        logger.info(f"API Error: {error.message}", extra={'status_code': error.status_code})
    
    return response

def handle_bad_request(error):
    """
    Handler for 400 Bad Request errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    api_error = APIError("Bad request", status_code=400)
    return handle_api_error(api_error)

def handle_unauthorized(error):
    """
    Handler for 401 Unauthorized errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    api_error = AuthenticationError("Authentication required")
    return handle_api_error(api_error)

def handle_forbidden(error):
    """
    Handler for 403 Forbidden errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    api_error = AuthorizationError("Access forbidden")
    return handle_api_error(api_error)

def handle_not_found(error):
    """
    Handler for 404 Not Found errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    api_error = ResourceNotFoundError("Resource not found")
    return handle_api_error(api_error)

def handle_method_not_allowed(error):
    """
    Handler for 405 Method Not Allowed errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    api_error = APIError("Method not allowed", status_code=405)
    return handle_api_error(api_error)

def handle_unprocessable_entity(error):
    """
    Handler for 422 Unprocessable Entity errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    # Extract validation errors from WTForms if available
    details = {}
    if hasattr(error, 'data') and 'errors' in error.data:
        details = {'fields': error.data['errors']}
    
    api_error = ValidationError("Validation error", details=details)
    return handle_api_error(api_error)

def handle_rate_limit_exceeded(error):
    """
    Handler for 429 Too Many Requests errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    api_error = RateLimitError("Rate limit exceeded")
    return handle_api_error(api_error)

def handle_server_error(error):
    """
    Handler for 500 Internal Server Error errors.
    
    Args:
        error: Error instance
        
    Returns:
        JSON response with error details
    """
    # Log the full stack trace
    logger.error(f"Server error: {str(error)}", exc_info=True)
    
    # Create a more detailed error in development
    is_development = current_app.config.get('ENV') == 'development'
    
    details = None
    if is_development:
        details = {
            'traceback': traceback.format_exc(),
            'error_type': error.__class__.__name__
        }
    
    api_error = ServiceError("Internal server error", details=details)
    return handle_api_error(api_error)

def handle_exception(error):
    """
    Catch-all handler for uncaught exceptions.
    
    Args:
        error: Exception instance
        
    Returns:
        JSON response with error details
    """
    # Log the full stack trace
    logger.error(f"Uncaught exception: {str(error)}", exc_info=True)
    
    # Create a more detailed error in development
    is_development = current_app.config.get('ENV') == 'development'
    
    details = None
    if is_development:
        details = {
            'traceback': traceback.format_exc(),
            'error_type': error.__class__.__name__
        }
    
    message = str(error) if is_development else "An unexpected error occurred"
    
    api_error = ServiceError(message, details=details)
    return handle_api_error(api_error) 