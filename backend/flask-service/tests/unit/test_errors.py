"""
Unit tests for the error handling functionality in the Flask service.
"""

import pytest
import json
import flask
from flask import Flask, jsonify, request, current_app
from unittest.mock import patch, MagicMock
import traceback
import sys

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.error]

# Try different import paths for the API error classes
try:
    from meeting_shared.errors import APIError
except ImportError:
    try:
        from src.core.errors import APIError
    except ImportError:
        pass


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
                                          AuthorizationError, ResourceNotFoundError,
                                          ResourceExistsError, ServiceError)
            except ImportError:
                from src.core.errors import (ValidationError, AuthenticationError, 
                                            AuthorizationError, ResourceNotFoundError,
                                            ResourceExistsError, ServiceError)
            
            # Test ValidationError
            error = ValidationError(message="Invalid data", details={"title": "Invalid format"})
            assert error.status_code == 422
            
            # Test AuthenticationError
            error = AuthenticationError(message="Authentication failed")
            assert error.status_code == 401
            
            # Test AuthorizationError
            error = AuthorizationError(message="Not authorized")
            assert error.status_code == 403
            
            # Test ResourceNotFoundError
            error = ResourceNotFoundError(message="Meeting not found")
            assert error.status_code == 404
            
            # Test ResourceExistsError
            error = ResourceExistsError(message="Meeting already exists")
            assert error.status_code == 409
            
            # Test ServiceError
            error = ServiceError(message="Unable to connect to auth service")
            assert error.status_code == 500
    
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
    
    def test_dependent_service_error(self, app, client, mock_request_id, mock_responses):
        """Test handling errors from dependent services."""
        with app.app_context():
            from src.core.errors import register_error_handlers, ServiceError
            
            # Register error handlers
            register_error_handlers(app)
            
            # Add a test route that simulates a service error
            @app.route('/service-error')
            def service_error():
                raise ServiceError(message="Auth service unavailable", 
                                details={"service": "auth"})
            
            # Make a request to the test route
            response = client.get('/service-error')
            
            # Check the response
            assert response.status_code == 500
            assert response.content_type == 'application/json'
            
            data = json.loads(response.data)
            assert data['message'] == "Auth service unavailable"
            assert data['status_code'] == 500
            assert data['details'] == {"service": "auth"}
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

    def test_api_error_inheritance(self, app):
        """Test that API error classes inherit correctly."""
        from meeting_shared.errors import (ValidationError, AuthenticationError,
                                        AuthorizationError, ResourceNotFoundError, 
                                        ConflictError, RateLimitError, ServerError)
        
        # Check that each error type inherits from APIError
        assert issubclass(ValidationError, APIError)
        assert issubclass(AuthenticationError, APIError)
        assert issubclass(AuthorizationError, APIError)
        assert issubclass(ResourceNotFoundError, APIError)
        assert issubclass(ConflictError, APIError)
        assert issubclass(RateLimitError, APIError)
        assert issubclass(ServerError, APIError)

    def test_validation_error_with_fields(self, app):
        """Test ValidationError with multiple field errors."""
        with app.app_context():
            try:
                from meeting_shared.errors import ValidationError
            except ImportError:
                pytest.skip("ValidationError not found")
            
            # Create a validation error with field errors
            field_errors = {
                'name': 'Name is required',
                'email': 'Email must be valid'
            }
            # ... existing code ... 