from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from ..schemas.base import ErrorResponse
import logging

logger = logging.getLogger(__name__)

def jwt_required(f):
    """Decorator to require JWT token for route access"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            response = ErrorResponse(
                error="Authentication Error",
                message="Token is missing"
            )
            return jsonify(response.model_dump()), 401
        
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256']
            )
            g.current_user_id = payload['user_id']
            g.current_token = token
            
        except jwt.ExpiredSignatureError:
            response = ErrorResponse(
                error="Authentication Error",
                message="Token has expired"
            )
            return jsonify(response.model_dump()), 401
            
        except jwt.InvalidTokenError:
            response = ErrorResponse(
                error="Authentication Error",
                message="Invalid token"
            )
            return jsonify(response.model_dump()), 401
        
        return f(*args, **kwargs)
    
    return decorated

def service_auth_required(f):
    """Decorator to require service authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        service_key = request.headers.get('X-Service-Key')
        expected_key = current_app.config.get('SERVICE_KEY')
        
        if not service_key or service_key != expected_key:
            response = ErrorResponse(
                error="Authentication Error",
                message="Invalid service key"
            )
            return jsonify(response.model_dump()), 403
            
        return f(*args, **kwargs)
    
    return decorated

def roles_required(*roles):
    """Decorator to require specific roles for route access"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user_id'):
                response = ErrorResponse(
                    error="Authentication Error",
                    message="No authenticated user"
                )
                return jsonify(response.model_dump()), 401
            
            # This should be implemented based on your role management system
            user_roles = get_user_roles(g.current_user_id)
            
            if not any(role in user_roles for role in roles):
                response = ErrorResponse(
                    error="Authorization Error",
                    message="Insufficient permissions"
                )
                return jsonify(response.model_dump()), 403
                
            return f(*args, **kwargs)
        return decorated
    return decorator

def get_user_roles(user_id: int) -> list:
    """Get user roles - implement based on your role management system"""
    # This is a placeholder - implement based on your system
    return [] 