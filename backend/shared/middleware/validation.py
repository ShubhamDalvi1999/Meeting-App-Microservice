from functools import wraps
from flask import request, jsonify
from pydantic import BaseModel, ValidationError
from typing import Type, List, Union, Dict, Any
from ..schemas.base import ErrorResponse
import logging
from ..database import transaction

logger = logging.getLogger(__name__)

def validate_schema(schema_class: Type[BaseModel], allow_bulk: bool = False):
    """
    Enhanced decorator to validate request data against a Pydantic schema
    
    Args:
        schema_class: Pydantic model class to validate against
        allow_bulk: Whether to allow bulk validation of a list of items
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get request data based on content type
                if request.is_json:
                    data = request.get_json()
                elif request.form:
                    data = request.form.to_dict()
                else:
                    data = request.args.to_dict()
                
                # Handle bulk validation if allowed and data is a list
                if allow_bulk and isinstance(data, list):
                    validated_data = [schema_class(**item) for item in data]
                else:
                    validated_data = schema_class(**data)
                
                # Add validated data to kwargs
                kwargs['data'] = validated_data
                
                # Wrap the function call in a transaction
                with transaction():
                    return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.error(f"Validation error: {str(e)}")
                response = ErrorResponse(
                    error="Validation Error",
                    message="Invalid request data",
                    details={"errors": e.errors()}
                )
                return jsonify(response.model_dump()), 400
                
            except Exception as e:
                logger.error(f"Error validating request data: {str(e)}")
                response = ErrorResponse(
                    error="Validation Error",
                    message="Error processing request data"
                )
                return jsonify(response.model_dump()), 400
                
        return decorated_function
    return decorator

def validate_nested_schema(schema_class: Type[BaseModel], field_path: str):
    """
    Decorator to validate nested data in request against a Pydantic schema
    
    Args:
        schema_class: Pydantic model class to validate against
        field_path: Dot-notation path to the nested data (e.g. "user.profile")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                
                # Navigate to nested data using field path
                nested_data = data
                for field in field_path.split('.'):
                    nested_data = nested_data.get(field, {})
                
                # Validate nested data
                validated_data = schema_class(**nested_data)
                
                # Add validated data to kwargs using field path
                kwargs[field_path.replace('.', '_')] = validated_data
                
                # Wrap the function call in a transaction
                with transaction():
                    return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.error(f"Validation error in nested schema: {str(e)}")
                response = ErrorResponse(
                    error="Validation Error",
                    message=f"Invalid data in {field_path}",
                    details={"errors": e.errors()}
                )
                return jsonify(response.model_dump()), 400
                
            except Exception as e:
                logger.error(f"Error validating nested data: {str(e)}")
                response = ErrorResponse(
                    error="Validation Error",
                    message="Error processing request data"
                )
                return jsonify(response.model_dump()), 400
                
        return decorated_function
    return decorator

def validate_query_params(*required_params):
    """
    Decorator to validate required query parameters
    
    Args:
        *required_params: Names of required query parameters
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_params = [
                param for param in required_params 
                if param not in request.args
            ]
            
            if missing_params:
                response = ErrorResponse(
                    error="Validation Error",
                    message="Missing required query parameters",
                    details={"missing_params": missing_params}
                )
                return jsonify(response.model_dump()), 400
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator 