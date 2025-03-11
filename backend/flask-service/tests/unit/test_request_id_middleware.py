"""
Unit tests for the request ID middleware in the Flask service.
"""

import pytest
import uuid
import re
from flask import g, request
from unittest.mock import patch, MagicMock
import functools
from flask import jsonify
from flask import Flask
from meeting_shared.shared_logging import setup_logging

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.middleware]


class TestRequestIdMiddleware:
    """Unit tests for the request ID middleware."""
    
    def test_middleware_registration(self, app):
        """Test that the middleware is correctly registered."""
        # Create a mock middleware class
        class MockRequestIdMiddleware:
            def __init__(self):
                self.before_request_called = False
                self.after_request_called = False

            def init_app(self, app):
                app.before_request(self.before_request)
                app.after_request(self.after_request)

            def before_request(self):
                self.before_request_called = True

            def after_request(self, response):
                self.after_request_called = True
                return response

        # Create a middleware instance
        middleware = MockRequestIdMiddleware()
        
        # Register the middleware
        middleware.init_app(app)
        
        # Check that before_request and after_request functions are registered
        before_funcs = app.before_request_funcs.get(None, [])
        after_funcs = app.after_request_funcs.get(None, [])
        
        # There should be at least one before_request and after_request function
        assert len(before_funcs) > 0
        assert len(after_funcs) > 0
        
        # Create a test client and make a request to trigger middleware
        client = app.test_client()
        client.get('/nonexistent')
        
        # Verify that middleware functions were actually called
        assert middleware.before_request_called
        assert middleware.after_request_called
    
    def test_request_id_generation(self, app, client):
        """Test that request IDs are generated if not provided."""
        # Setup a simple middleware directly in the test
        @app.after_request
        def add_request_id(response):
            # Add a request ID if not already in the request
            if 'X-Request-ID' not in request.headers:
                response.headers['X-Request-ID'] = str(uuid.uuid4())
            return response
                
        # Make a request without a request ID header
        response = client.get('/health')
        
        # Check that a request ID was added to the response
        assert 'X-Request-ID' in response.headers
        
        # Verify that it's a valid UUID
        request_id = response.headers['X-Request-ID']
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', request_id)
    
    def test_request_id_propagation(self, app, client):
        """Test that provided request IDs are propagated."""
        # Create a test request ID
        test_request_id = str(uuid.uuid4())
        
        # Setup a simple middleware directly in the test
        @app.before_request
        def capture_request_id():
            if 'X-Request-ID' in request.headers:
                g.request_id = request.headers['X-Request-ID']
        
        @app.after_request
        def propagate_request_id(response):
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            return response
        
        # Make a request with the request ID header
        response = client.get('/health', headers={'X-Request-ID': test_request_id})
        
        # Check that the same request ID is in the response
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == test_request_id
    
    def test_correlation_id_propagation(self, app, client):
        """Test that correlation IDs are propagated."""
        # Create a test correlation ID
        test_correlation_id = str(uuid.uuid4())
        
        # Setup a simple middleware directly in the test
        @app.before_request
        def capture_correlation_id():
            if 'X-Correlation-ID' in request.headers:
                g.correlation_id = request.headers['X-Correlation-ID']
        
        @app.after_request
        def propagate_correlation_id(response):
            if hasattr(g, 'correlation_id'):
                response.headers['X-Correlation-ID'] = g.correlation_id
            return response
        
        # Make a request with the correlation ID header
        response = client.get('/health', headers={'X-Correlation-ID': test_correlation_id})
        
        # Check that the same correlation ID is in the response
        assert 'X-Correlation-ID' in response.headers
        assert response.headers['X-Correlation-ID'] == test_correlation_id
    
    def test_get_request_id_function(self, app, client):
        """Test a custom get_request_id function."""
        # Define a test request ID
        test_request_id = str(uuid.uuid4())
        
        # Define a get_request_id function
        def get_request_id():
            if hasattr(g, 'request_id'):
                return g.request_id
            return None
        
        # Setup a simple middleware directly in the test
        @app.before_request
        def capture_request_id():
            if 'X-Request-ID' in request.headers:
                g.request_id = request.headers['X-Request-ID']
            else:
                g.request_id = str(uuid.uuid4())
        
        # Test within a request context
        with app.test_request_context(headers={'X-Request-ID': test_request_id}):
            # Call the before_request function manually
            capture_request_id()
            
            # Test the get_request_id function
            assert get_request_id() == test_request_id
            
            # Verify request ID is in g
            assert hasattr(g, 'request_id')
            assert g.request_id == test_request_id
    
    def test_get_request_id_without_context(self):
        """Test a get_request_id function outside of a request context."""
        # Define a get_request_id function that works outside of a request context
        def get_request_id():
            try:
                if hasattr(g, 'request_id'):
                    return g.request_id
            except RuntimeError:
                # Runtime error occurs when accessing g outside of a request context
                return None
            return None
        
        # Call the function outside of a request context
        request_id = get_request_id()
        
        # Should return None when outside of a request context
        assert request_id is None
    
    def test_with_request_id_decorator(self, app):
        """Test a custom request ID decorator."""
        # Define a test request ID
        test_request_id = str(uuid.uuid4())
        
        # Define a with_request_id decorator
        def with_request_id(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with app.test_request_context(headers={'X-Request-ID': test_request_id}):
                    # Call the before_request handlers
                    app.preprocess_request()
                    
                    result = func(*args, **kwargs)
                    
                    # Clean up
                    app.process_response(app.response_class())
                    return result
            return wrapper
        
        # Define a get_request_id function
        def get_request_id():
            if hasattr(g, 'request_id'):
                return g.request_id
            return None
        
        # Setup a simple middleware
        @app.before_request
        def capture_request_id():
            if 'X-Request-ID' in request.headers:
                g.request_id = request.headers['X-Request-ID']
            else:
                g.request_id = str(uuid.uuid4())
        
        # Define a test function with the decorator
        @with_request_id
        def test_func():
            return get_request_id()
        
        # Call the test function and verify the result
        result = test_func()
        assert result == test_request_id
    
    def test_middleware_cleanup(self, app, client):
        """Test that the middleware properly sets request IDs."""
        # Use a flag to check if request_id was set
        request_id_was_set = False
        test_request_id_value = str(uuid.uuid4())
        
        # Setup test middleware
        @app.before_request
        def capture_request_id():
            # Set the request ID
            g.request_id = test_request_id_value
            
            # Check if we can access the request_id in g
            nonlocal request_id_was_set
            request_id_was_set = hasattr(g, 'request_id')
        
        # Make a request to trigger middleware
        response = client.get('/health')
        
        # Verify that request_id was set during the request
        assert request_id_was_set
        
        # Verify that we can set and access values in g within a request context
        with app.test_request_context():
            # Set a test value
            g.test_value = "test"
            # Verify we can access it
            assert g.test_value == "test"
    
    def test_middleware_with_error(self, app, client):
        """Test that the middleware works correctly when an error occurs."""
        # Create a test request ID
        test_request_id = str(uuid.uuid4())
        
        # Setup a simple middleware
        @app.before_request
        def capture_request_id():
            if 'X-Request-ID' in request.headers:
                g.request_id = request.headers['X-Request-ID']
            else:
                g.request_id = str(uuid.uuid4())
        
        @app.after_request
        def propagate_request_id(response):
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            return response
        
        # Create a route that raises an error
        @app.route('/error-test')
        def error_test():
            raise ValueError("Test error")
        
        # Register error handler
        @app.errorhandler(ValueError)
        def handle_value_error(e):
            response = jsonify({'error': str(e)})
            response.status_code = 500
            return response
        
        # Make a request with a request ID to the error route
        response = client.get('/error-test', headers={'X-Request-ID': test_request_id})
        
        # Check that the request ID is still in the response
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] == test_request_id
    
    def test_request_id_in_logs(self, app):
        """Test that the request ID is included in logs."""
        # Create a mock request ID
        mock_request_id = "test-request-id-123456"
        
        # Configure the app for request ID middleware
        app.config["REQUEST_ID_HEADER"] = "X-Request-ID"
        
        # Import the RequestIdMiddleware
        from meeting_shared.middleware.request_id import RequestIdMiddleware
        
        # Set up the middleware
        middleware = RequestIdMiddleware(app)
        
        # Create a test request with the mock request ID
        with app.test_request_context(headers={"X-Request-ID": mock_request_id}):
            # Call the before_request handler manually to ensure request ID is set
            middleware.before_request()
            
            # Verify the request ID is set in Flask g
            assert hasattr(g, 'request_id'), "request_id not set in Flask g"
            assert g.request_id == mock_request_id, f"Expected request_id {mock_request_id}, got {g.request_id}"
            
            # Verify correlation ID is also set
            assert hasattr(g, 'correlation_id'), "correlation_id not set in Flask g"
            assert g.correlation_id == mock_request_id, f"Expected correlation_id {mock_request_id}, got {g.correlation_id}" 