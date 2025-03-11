"""
Unit tests for the error handling functionality in the auth service.
"""

import pytest
import json
import flask
from flask import Flask, jsonify, request, current_app

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.error]


class TestErrorHandling:
    """Unit tests for the error handling functionality."""
    
    def test_api_error_base_class(self, app):
        """Test the base APIError class functionality."""
        with app.app_context():
            # Try to import from shared module first
            try:
                from meeting_shared.errors import APIError
            except ImportError:
                from src.core.errors import APIError
            
            # Create an instance of APIError
            error = APIError(message="Test error", status_code=400, details={"field": "value"})
            
            # Check the properties
            assert error.message == "Test error"
            assert error.status_code == 400
            assert error.details == {"field": "value"}
            assert isinstance(error.timestamp, str)
            
            # Check the to_dict method
            error_dict = error.to_dict()
            assert error_dict["message"] == "Test error"
            assert error_dict["status_code"] == 400
            assert error_dict["details"] == {"field": "value"}
            assert "timestamp" in error_dict
            assert "request_id" in error_dict
    
    def test_specific_error_classes(self, app):
        """Test specific error classes derived from APIError."""
        with app.app_context():
            # Try to import from shared module first
            try:
                from meeting_shared.errors import (ValidationError, AuthenticationError, 
                                                  AuthorizationError, UserExistsError,
                                                  UserNotFoundError, TokenError)
            except ImportError:
                from src.core.errors import (ValidationError, AuthenticationError, 
                                            AuthorizationError, UserExistsError,
                                            UserNotFoundError, TokenError)
            
            # Test ValidationError
            error = ValidationError(message="Invalid data", details={"email": "Invalid format"})
            assert error.status_code == 422
            
            # Test AuthenticationError
            error = AuthenticationError(message="Authentication failed")
            assert error.status_code == 401
            
            # Test AuthorizationError
            error = AuthorizationError(message="Not authorized")
            assert error.status_code == 403
            
            # Test UserExistsError
            error = UserExistsError(message="User already exists")
            assert error.status_code == 409
            
            # Test UserNotFoundError
            error = UserNotFoundError(message="User not found")
            assert error.status_code == 404
            
            # Test TokenError
            error = TokenError(message="Invalid token")
            assert error.status_code == 401
    
    def test_error_handler_registration(self, app):
        """Test that error handlers are correctly registered."""
        with app.app_context():
            from src.core.errors import register_error_handlers
            
            # Register error handlers
            register_error_handlers(app)
            
            # Check that handlers are registered
            assert app.error_handler_spec[None][400] is not None
            assert app.error_handler_spec[None][401] is not None
            assert app.error_handler_spec[None][403] is not None
            assert app.error_handler_spec[None][404] is not None
            assert app.error_handler_spec[None][405] is not None
            assert app.error_handler_spec[None][422] is not None
            assert app.error_handler_spec[None][429] is not None
            assert app.error_handler_spec[None][500] is not None
    
    def test_api_error_response(self, app, client, mock_request_id):
        """Test that API errors return proper JSON responses."""
        with app.app_context():
            # Try to import from shared module first
            try:
                from meeting_shared.errors import ValidationError
            except ImportError:
                from src.core.errors import ValidationError
            
            from src.core.errors import register_error_handlers
            
            # Register error handlers
            register_error_handlers(app)
            
            # Add a test route that raises an error
            @app.route('/test-error')
            def test_error():
                raise ValidationError(message="Test validation error", 
                                    details={"field": "Invalid value"})
            
            # Make a request to the test route
            response = client.get('/test-error')
            
            # Check the response
            assert response.status_code == 422
            assert response.content_type == 'application/json'
            
            data = json.loads(response.data)
            assert data['message'] == "Test validation error"
            assert data['status_code'] == 422
            assert data['details'] == {"field": "Invalid value"}
            assert "timestamp" in data
            assert data['request_id'] == mock_request_id
    
    def test_http_error_response(self, app, client, mock_request_id):
        """Test that HTTP errors return proper JSON responses."""
        with app.app_context():
            from src.core.errors import register_error_handlers
            
            # Register error handlers
            register_error_handlers(app)
            
            # Add a test route that returns a 404
            @app.route('/nonexistent-route')
            def nonexistent_route():
                flask.abort(404)
            
            # Make a request to a nonexistent route
            response = client.get('/route-that-does-not-exist')
            
            # Check the response
            assert response.status_code == 404
            assert response.content_type == 'application/json'
            
            data = json.loads(response.data)
            assert "Not Found" in data['message']
            assert data['status_code'] == 404
            assert "timestamp" in data
            assert data['request_id'] == mock_request_id
    
    def test_unhandled_exception_response(self, app, client, mock_request_id):
        """Test that unhandled exceptions return proper JSON responses."""
        with app.app_context():
            from src.core.errors import register_error_handlers
            
            # Register error handlers
            register_error_handlers(app)
            
            # Add a test route that raises an unhandled exception
            @app.route('/unhandled-exception')
            def unhandled_exception():
                # This will raise a ZeroDivisionError
                return 1 / 0
            
            # Make a request to the test route
            response = client.get('/unhandled-exception')
            
            # Check the response
            assert response.status_code == 500
            assert response.content_type == 'application/json'
            
            data = json.loads(response.data)
            assert "Internal Server Error" in data['message']
            assert data['status_code'] == 500
            assert "timestamp" in data
            assert data['request_id'] == mock_request_id
            
            # In production, we shouldn't expose the error details
            if app.config['ENV'] == 'production':
                assert 'ZeroDivisionError' not in str(data)
            else:
                # In development, we might include error details
                # This depends on your error handler implementation
                pass 