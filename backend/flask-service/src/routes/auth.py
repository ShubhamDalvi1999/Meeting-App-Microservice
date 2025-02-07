from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
import jwt
import datetime
from datetime import UTC
import os
import re
from sqlalchemy.exc import IntegrityError

from ..models import db, User

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    if not email or len(email) > 120:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if not password or len(password) > 72:  # bcrypt max length is 72 bytes
        return False
    # At least 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def validate_name(name):
    if not name or len(name) > 100:
        return False
    # Allow letters, numbers, spaces, dots, and hyphens
    return bool(re.match(r'^[a-zA-Z0-9\s.-]{3,100}$', name))

def get_failed_login_attempts(email):
    # You should implement rate limiting using Redis or similar
    # This is a placeholder
    return 0

def is_ip_blocked(ip):
    # You should implement IP blocking using Redis or similar
    # This is a placeholder
    return False

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # Check IP blocking first
        if is_ip_blocked(request.remote_addr):
            return jsonify({'error': 'Too many requests', 'code': 'ip_blocked'}), 429

        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if not all(k in data for k in ['email', 'name', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Sanitize inputs
        email = data['email'].strip().lower()
        name = data['name'].strip()
        password = data['password']
            
        # Enhanced validations
        if not validate_email(email):
            return jsonify({
                'error': 'Invalid email format or length',
                'requirements': 'Valid email format and maximum 120 characters'
            }), 400
            
        if not validate_password(password):
            return jsonify({
                'error': 'Password does not meet requirements',
                'requirements': 'At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character'
            }), 400
            
        if not validate_name(name):
            return jsonify({
                'error': 'Invalid name format or length',
                'requirements': 'Between 3-100 characters, letters, numbers, spaces, dots, and hyphens only'
            }), 400
            
        # Check for existing user with case-insensitive email
        if User.query.filter(User.email.ilike(email)).first():
            return jsonify({'error': 'Email already registered'}), 400
            
        # Check for existing user with case-insensitive name
        if User.query.filter(User.name.ilike(name)).first():
            return jsonify({'error': 'Name already taken'}), 400
        
        user = User(
            email=email,
            name=name,
            password=password
        )
        
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'Database constraint violation'}), 400
        
        # Generate JWT token with limited expiry
        token_expiry = int(os.getenv('JWT_EXPIRY_DAYS', '1'))
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.datetime.now(UTC) + datetime.timedelta(days=token_expiry),
            'iat': datetime.datetime.now(UTC),
            'type': 'access'
        }, os.getenv('JWT_SECRET_KEY'), algorithm='HS256')
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error occurred during registration'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        # Check IP blocking first
        if is_ip_blocked(request.remote_addr):
            return jsonify({'error': 'Too many requests', 'code': 'ip_blocked'}), 429

        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not all(k in data for k in ['email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        email = data['email'].strip().lower()
        
        # Check failed login attempts
        attempts = get_failed_login_attempts(email)
        if attempts >= 5:  # Lock after 5 failed attempts
            return jsonify({
                'error': 'Account temporarily locked',
                'code': 'account_locked',
                'retry_after': '15 minutes'
            }), 429
        
        user = User.query.filter(User.email.ilike(email)).first()
        
        if not user or not user.check_password(data['password']):
            # Increment failed attempts counter (implement in Redis)
            return jsonify({
                'error': 'Invalid credentials',
                'remaining_attempts': 5 - (attempts + 1)
            }), 401
        
        # Reset failed attempts counter on successful login
        
        # Generate JWT token with all necessary claims
        token_expiry = int(os.getenv('JWT_EXPIRY_DAYS', '1'))
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.datetime.now(UTC) + datetime.timedelta(days=token_expiry),
            'iat': datetime.datetime.now(UTC),
            'type': 'access'
        }, os.getenv('JWT_SECRET_KEY'), algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Server error occurred during login'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        token = request.headers.get('Authorization')
        
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Invalid token format', 'code': 'invalid_token_format'}), 401
            
        token = token.split('Bearer ')[1]
        
        try:
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
            user = User.query.get(data['user_id'])
            
            if not user:
                return jsonify({'error': 'User not found', 'code': 'user_not_found'}), 401
                
            return jsonify({
                'valid': True,
                'user': user.to_dict()
            })
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired', 'code': 'token_expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token', 'code': 'token_invalid'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Server error occurred during token verification', 'code': 'verification_error'}), 500 