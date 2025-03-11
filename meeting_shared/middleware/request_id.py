"""
Request ID middleware module for tracking requests across services.
Generates and propagates request and correlation IDs.
"""

import logging
import uuid
import threading
from functools import wraps
from flask import Flask, request, g, has_request_context, current_app
from werkzeug.wsgi import ClosingIterator
from werkzeug.exceptions import HTTPException
from typing import Optional, Dict, Any, Callable, Union, List, Tuple

try:
    from . import Middleware
except (ImportError, ValueError):
    # Fallback if parent module not available
    class Middleware:
        """Base middleware class fallback"""
        def __init__(self, app=None, **kwargs):
            self.app = app
            if app is not None:
                self.init_app(app, **kwargs)
                
        def init_app(self, app, **kwargs):
            pass

# Thread-local storage for request ID when Flask context is not available
_request_id_local = threading.local()

logger = logging.getLogger(__name__)

class RequestIdMiddleware(Middleware):
    """
    WSGI middleware that assigns a unique request ID to each incoming request.
    Optionally preserves request ID from request header if present.
    """
    
    def __init__(self, app=None, **kwargs):
        """Initialize middleware with optional app"""
        self.app = app
        self.request_id_header = 'X-Request-ID'
        self.correlation_id_header = 'X-Correlation-ID'
        self.include_in_response = True
        
        if app is not None:
            self.init_app(app, **kwargs)
            
    def init_app(self, app: Flask, **kwargs):
        """
        Initialize middleware with Flask application.
        
        Args:
            app: Flask application
            request_id_header: Name of header containing request ID
            correlation_id_header: Name of header containing correlation ID
            include_in_response: Whether to include request/correlation IDs in response
        """
        # Store configuration
        self.request_id_header = kwargs.get('request_id_header', self.request_id_header)
        self.correlation_id_header = kwargs.get('correlation_id_header', self.correlation_id_header)
        self.include_in_response = kwargs.get('include_in_response', self.include_in_response)
        
        # Register middleware with Flask
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        
        # Add endpoint to get current request ID (useful for testing/debugging)
        app.add_url_rule('/_request_id', '_request_id', self.request_id_endpoint)
        
        # Wrap application with WSGI middleware
        if not hasattr(app, 'wsgi_app_wrapped_by_request_id') or not app.wsgi_app_wrapped_by_request_id:
            original_wsgi_app = app.wsgi_app
            app.wsgi_app = self
            app.wsgi_app_wrapped_by_request_id = True
            self.app = original_wsgi_app
            
        logger.info(f"RequestIdMiddleware initialized with headers: {self.request_id_header}, {self.correlation_id_header}")
        
    def __call__(self, environ, start_response):
        """
        WSGI middleware implementation.
        
        Args:
            environ: WSGI environment
            start_response: WSGI start_response function
            
        Returns:
            WSGI response
        """
        # Extract request ID from environment or generate new one
        request_id = environ.get('HTTP_' + self.request_id_header.replace('-', '_').upper())
        correlation_id = environ.get('HTTP_' + self.correlation_id_header.replace('-', '_').upper())
        
        # Generate IDs if not present
        if not request_id:
            request_id = str(uuid.uuid4())
        
        if not correlation_id:
            correlation_id = request_id
            
        # Store in environment for downstream WSGI applications
        environ['request_id'] = request_id
        environ['correlation_id'] = correlation_id
        
        # Store in thread-local for access outside request context
        _request_id_local.request_id = request_id
        _request_id_local.correlation_id = correlation_id
        
        # Function to intercept the status and headers
        def custom_start_response(status, headers, exc_info=None):
            # Add request ID header to response if configured
            if self.include_in_response:
                headers_list = list(headers)
                headers_list.append((self.request_id_header, request_id))
                headers_list.append((self.correlation_id_header, correlation_id))
                headers = headers_list
            
            return start_response(status, headers, exc_info)
        
        # Process request
        try:
            return ClosingIterator(
                self.app(environ, custom_start_response),
                self.cleanup_request
            )
        except Exception as e:
            # Clean up if an exception occurs
            self.cleanup_request()
            raise
    
    def before_request(self):
        """Before request handler for Flask."""
        # Get request ID from headers or generate new one
        request_id = request.headers.get(self.request_id_header)
        correlation_id = request.headers.get(self.correlation_id_header)
        
        # Generate IDs if not present
        if not request_id:
            request_id = str(uuid.uuid4())
        
        if not correlation_id:
            correlation_id = request_id
        
        # Store in Flask g for access within request
        g.request_id = request_id
        g.correlation_id = correlation_id
        
        # Store in thread-local for access outside request context
        _request_id_local.request_id = request_id
        _request_id_local.correlation_id = correlation_id
        
        logger.debug(f"Request {request_id} started: {request.method} {request.path}")
    
    def after_request(self, response):
        """
        After request handler for Flask.
        
        Args:
            response: Flask response
            
        Returns:
            Modified response with request ID headers
        """
        # Add request ID headers to response if configured
        if self.include_in_response:
            response.headers.setdefault(
                self.request_id_header, 
                getattr(g, 'request_id', 'unknown')
            )
            response.headers.setdefault(
                self.correlation_id_header, 
                getattr(g, 'correlation_id', 'unknown')
            )
        
        logger.debug(f"Request {getattr(g, 'request_id', 'unknown')} completed with status {response.status_code}")
        return response
    
    def teardown_request(self, exception=None):
        """
        Teardown request handler for Flask.
        
        Args:
            exception: Exception if an error occurred during request processing
        """
        if exception:
            logger.error(f"Request {getattr(g, 'request_id', 'unknown')} failed: {str(exception)}")
    
    def cleanup_request(self):
        """Clean up request resources."""
        # Clear thread-local storage
        if hasattr(_request_id_local, 'request_id'):
            del _request_id_local.request_id
        if hasattr(_request_id_local, 'correlation_id'):
            del _request_id_local.correlation_id
    
    def request_id_endpoint(self):
        """Endpoint that returns the current request ID."""
        return {
            'request_id': get_request_id(),
            'correlation_id': get_correlation_id()
        }


# Helper functions to access request IDs outside middleware
def get_request_id() -> str:
    """
    Get the current request ID.
    
    Returns:
        str: Request ID from Flask g, or thread-local, or None
    """
    if has_request_context():
        return getattr(g, 'request_id', None)
    
    return getattr(_request_id_local, 'request_id', None)


def get_correlation_id() -> str:
    """
    Get the current correlation ID.
    
    Returns:
        str: Correlation ID from Flask g, or thread-local, or None
    """
    if has_request_context():
        return getattr(g, 'correlation_id', None)
    
    return getattr(_request_id_local, 'correlation_id', None)


def with_request_id(func):
    """
    Decorator that ensures a request ID exists for the decorated function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Generate request ID if none exists
        if not get_request_id():
            request_id = str(uuid.uuid4())
            _request_id_local.request_id = request_id
            _request_id_local.correlation_id = request_id
        
        return func(*args, **kwargs)
    
    return wrapper 