from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from ..models.auth import AuthUser, UserSession
from ..database import db

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = AuthUser.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
            # Store user in flask g object
            g.current_user = current_user
            
            # Get current session
            current_session = UserSession.query.filter_by(
                token=token,
                revoked=False
            ).first()
            if not current_session:
                return jsonify({'error': 'Invalid session'}), 401
            
            g.current_session = current_session
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def get_current_user():
    """Get the current authenticated user"""
    return getattr(g, 'current_user', None)

def get_current_session():
    """Get the current user session"""
    return getattr(g, 'current_session', None) 