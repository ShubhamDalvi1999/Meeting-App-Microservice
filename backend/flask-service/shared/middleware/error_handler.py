from functools import wraps
from flask import jsonify, current_app
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from jwt.exceptions import PyJWTError
from ..schemas.base import ErrorResponse
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)

def handle_api_errors(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = ErrorResponse(
            error="API Error",
            message=error.message,
            details=error.details
        )
        return jsonify(response.model_dump()), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = ErrorResponse(
            error="Validation Error",
            message="Invalid request data",
            details={"errors": error.errors()}
        )
        return jsonify(response.model_dump()), 400

    @app.errorhandler(PyJWTError)
    def handle_jwt_error(error):
        response = ErrorResponse(
            error="Authentication Error",
            message=str(error)
        )
        return jsonify(response.model_dump()), 401

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        response = ErrorResponse(
            error="Database Error",
            message="Data integrity violation",
            details={"error": str(error.orig)}
        )
        return jsonify(response.model_dump()), 409

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        logger.error(f"Database error: {str(error)}")
        response = ErrorResponse(
            error="Database Error",
            message="An error occurred while processing your request"
        )
        return jsonify(response.model_dump()), 500

    @app.errorhandler(404)
    def handle_404(error):
        response = ErrorResponse(
            error="Not Found",
            message="The requested resource was not found"
        )
        return jsonify(response.model_dump()), 404

    @app.errorhandler(405)
    def handle_405(error):
        response = ErrorResponse(
            error="Method Not Allowed",
            message=f"The {request.method} method is not allowed for this endpoint"
        )
        return jsonify(response.model_dump()), 405

    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f"Internal server error: {str(error)}")
        response = ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred"
        )
        return jsonify(response.model_dump()), 500

def error_handler(f):
    """Decorator to handle errors in routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            if not isinstance(e, APIError):
                e = APIError(str(e), 500)
            response = ErrorResponse(
                error=e.__class__.__name__,
                message=str(e),
                details=getattr(e, 'details', None)
            )
            return jsonify(response.model_dump()), e.status_code
    return decorated 