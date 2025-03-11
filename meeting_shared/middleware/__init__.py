"""
Shared middleware module for backend services.
Provides middleware for request ID tracking, logging, and more.
"""

from typing import List, Callable, Dict, Any, Optional, Type
import logging
import importlib

logger = logging.getLogger(__name__)

# Define middleware interface
class Middleware:
    """Base class for all middleware"""
    
    def __init__(self, app=None, **kwargs):
        """Initialize middleware with optional app"""
        self.app = app
        if app is not None:
            self.init_app(app, **kwargs)
    
    def init_app(self, app, **kwargs):
        """Initialize middleware with app"""
        raise NotImplementedError("Middleware must implement init_app")
        
    def process_request(self, request):
        """Process request before it reaches the view"""
        return None
        
    def process_response(self, request, response):
        """Process response after it leaves the view"""
        return response
        
    def __call__(self, environ, start_response):
        """WSGI middleware interface"""
        raise NotImplementedError("Middleware must implement __call__")


# Try to import specific middleware modules
# If not available, provide dummy implementations
try:
    from .request_id import RequestIdMiddleware
except ImportError:
    class RequestIdMiddleware(Middleware):
        """Dummy implementation of RequestIdMiddleware"""
        def init_app(self, app, **kwargs):
            logger.warning("Using dummy RequestIdMiddleware")
            
        def __call__(self, environ, start_response):
            return self.app(environ, start_response)


# Default middleware configuration
DEFAULT_MIDDLEWARE = {
    'request_id': {
        'class': RequestIdMiddleware,
        'kwargs': {
            'request_id_header': 'X-Request-ID',
            'correlation_id_header': 'X-Correlation-ID'
        }
    }
}


def register_middleware(app, middleware_list=None):
    """
    Register middleware with a Flask application.
    
    Args:
        app: Flask application
        middleware_list: List of middleware configurations or None for defaults
        
    Returns:
        Flask application with middleware registered
    """
    # Use default middleware if none specified
    if middleware_list is None:
        middleware_list = list(DEFAULT_MIDDLEWARE.values())
    
    # Add each middleware to the application
    for middleware_config in middleware_list:
        if isinstance(middleware_config, dict):
            middleware_class = middleware_config.get('class')
            kwargs = middleware_config.get('kwargs', {})
            
            if middleware_class:
                try:
                    middleware = middleware_class()
                    middleware.init_app(app, **kwargs)
                    logger.info(f"Registered middleware: {middleware_class.__name__}")
                except Exception as e:
                    logger.error(f"Failed to register middleware {middleware_class.__name__}: {str(e)}")
        elif isinstance(middleware_config, Middleware):
            # If middleware instance is provided directly
            try:
                middleware_config.init_app(app)
                logger.info(f"Registered middleware: {middleware_config.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to register middleware {middleware_config.__class__.__name__}: {str(e)}")
    
    return app


# Import specific middleware to make them available at package level
__all__ = [
    'Middleware',
    'RequestIdMiddleware', 
    'register_middleware'
] 