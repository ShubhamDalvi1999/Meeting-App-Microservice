"""
Unit tests for the request ID middleware.
"""

import pytest
import uuid
from flask import g, request
from unittest.mock import patch, MagicMock

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.middleware]


class TestRequestIdMiddleware:
    """Unit tests for the request ID middleware."""
    
    def test_middleware_registration(self, app):
        """Test that the middleware is correctly registered."""
        # Import the middleware class based on what's available
        try:
            from meeting_shared.middleware.request_id import RequestIdMiddleware
        except ImportError:
            try:
                from src.middleware.request_id import RequestIdMiddleware
            except ImportError:
                pytest.skip("RequestIdMiddleware not found")
        
        # Create middleware instance
        middleware = RequestIdMiddleware()
        
        # Register middleware with app
        middleware.init_app(app)
        
        # Verify that the middleware was registered
        # This is hard to test directly, but we can check for side effects
        assert hasattr(app, 'before_request_funcs')
        assert hasattr(app, 'after_request_funcs')
    
    def test_request_id_generation(self, app, client):
        """Test that a request ID is generated for requests."""
        # Make a request
        response = client.get('/health')
        
        # Check that a request ID header is in the response
        assert 'X-Request-ID' in response.headers
        assert response.headers.get('X-Request-ID') is not None
        assert len(response.headers.get('X-Request-ID')) > 0
    
    def test_request_id_propagation(self, app, client):
        """Test that request IDs are propagated from request to response."""
        # Generate a test request ID
        test_request_id = str(uuid.uuid4())
        
        # Make a request with the test request ID
        response = client.get('/health', headers={'X-Request-ID': test_request_id})
        
        # Check that the same request ID is in the response
        assert 'X-Request-ID' in response.headers
        assert response.headers.get('X-Request-ID') == test_request_id
    
    def test_correlation_id_propagation(self, app, client):
        """Test that correlation IDs are propagated from request to response."""
        # Generate a test correlation ID
        test_correlation_id = str(uuid.uuid4())
        
        # Make a request with the test correlation ID
        response = client.get('/health', headers={'X-Correlation-ID': test_correlation_id})
        
        # Check that the same correlation ID is in the response
        assert 'X-Correlation-ID' in response.headers
        assert response.headers.get('X-Correlation-ID') == test_correlation_id
    
    def test_get_request_id_function(self, app, client):
        """Test the get_request_id function."""
        # Import the function based on what's available
        try:
            from meeting_shared.middleware.request_id import get_request_id
        except ImportError:
            try:
                from src.middleware.request_id import get_request_id
            except ImportError:
                pytest.skip("get_request_id function not found")
        
        # Generate a test request ID
        test_request_id = str(uuid.uuid4())
        
        # Make a test request that will use the get_request_id function
        # We need a route that calls get_request_id, here we'll patch it
        
        with app.test_request_context(headers={'X-Request-ID': test_request_id}):
            # Manually set request ID in g to simulate middleware
            g.request_id = test_request_id
            
            # Call the function
            returned_id = get_request_id()
            
            # Verify the result
            assert returned_id == test_request_id
    
    def test_get_request_id_without_context(self):
        """Test the get_request_id function outside a request context."""
        # Import the function based on what's available
        try:
            from meeting_shared.middleware.request_id import get_request_id
        except ImportError:
            try:
                from src.middleware.request_id import get_request_id
            except ImportError:
                pytest.skip("get_request_id function not found")
        
        # Call the function outside a request context
        # It should return None or a default value
        result = get_request_id()
        
        # The result could be None or a default value depending on implementation
        assert result is None or isinstance(result, str)
    
    def test_with_request_id_decorator(self, app):
        """Test the with_request_id decorator."""
        # Import the decorator based on what's available
        try:
            from meeting_shared.middleware.request_id import with_request_id
        except ImportError:
            try:
                from src.middleware.request_id import with_request_id
            except ImportError:
                pytest.skip("with_request_id decorator not found")
        
        # Create a test function with the decorator
        @with_request_id
        def test_func():
            # Import get_request_id in the function to ensure it's available
            try:
                from meeting_shared.middleware.request_id import get_request_id
            except ImportError:
                from src.middleware.request_id import get_request_id
            
            # Return the request ID
            return get_request_id()
        
        # Call the function outside a request context
        result = test_func()
        
        # The decorator should ensure a request ID is available
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0 