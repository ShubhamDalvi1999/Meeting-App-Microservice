# 2. Authentication & Authorization

## Overview
This document covers authentication and authorization implementation in our Flask backend application. These security features are crucial for protecting user data and controlling access to resources.

## Authentication System

### 1. JWT Implementation
```python
# src/auth/jwt.py
from datetime import datetime, timedelta
from typing import Dict, Any
import jwt
from src.models import User
from src.config import get_config

class JWTManager:
    def __init__(self):
        self.config = get_config()
        self.secret_key = self.config['JWT_SECRET_KEY']
        self.access_expires = timedelta(hours=1)
        self.refresh_expires = timedelta(days=30)

    def create_access_token(self, user: User) -> str:
        """Create a new access token."""
        return self._create_token(
            user,
            'access',
            self.access_expires
        )

    def create_refresh_token(self, user: User) -> str:
        """Create a new refresh token."""
        return self._create_token(
            user,
            'refresh',
            self.refresh_expires
        )

    def _create_token(
        self,
        user: User,
        token_type: str,
        expires_delta: timedelta
    ) -> str:
        """Create a JWT token."""
        now = datetime.utcnow()
        payload = {
            'sub': user.id,
            'iat': now,
            'exp': now + expires_delta,
            'type': token_type,
            'roles': [role.name for role in user.roles]
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=['HS256']
            )
            if payload['exp'] < datetime.utcnow().timestamp():
                raise jwt.InvalidTokenError('Token has expired')
            return payload
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(str(e))

jwt_manager = JWTManager()
```

### 2. Authentication Middleware
```python
# src/auth/middleware.py
from functools import wraps
from flask import request, g
from src.models import User
from src.auth.jwt import jwt_manager

def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {'error': 'Missing or invalid authorization header'}, 401

        token = auth_header.split(' ')[1]
        try:
            payload = jwt_manager.decode_token(token)
            user = User.query.get(payload['sub'])
            if not user:
                return {'error': 'User not found'}, 401
            g.current_user = user
        except AuthenticationError as e:
            return {'error': str(e)}, 401

        return f(*args, **kwargs)
    return decorated_function

def refresh_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {'error': 'Missing or invalid authorization header'}, 401

        token = auth_header.split(' ')[1]
        try:
            payload = jwt_manager.decode_token(token)
            if payload['type'] != 'refresh':
                return {'error': 'Invalid token type'}, 401
            user = User.query.get(payload['sub'])
            if not user:
                return {'error': 'User not found'}, 401
            g.current_user = user
        except AuthenticationError as e:
            return {'error': str(e)}, 401

        return f(*args, **kwargs)
    return decorated_function
```

## Authorization System

### 1. Role-Based Access Control
```python
# src/models/role.py
from src import db

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.relationship('Permission', secondary='role_permissions')

class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

role_permissions = db.Table(
    'role_permissions',
    db.Column(
        'role_id',
        db.Integer,
        db.ForeignKey('roles.id'),
        primary_key=True
    ),
    db.Column(
        'permission_id',
        db.Integer,
        db.ForeignKey('permissions.id'),
        primary_key=True
    )
)

# src/models/user.py
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    roles = db.relationship('Role', secondary='user_roles')

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        return any(
            permission.name == permission_name
            for role in self.roles
            for permission in role.permissions
        )

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
```

### 2. Authorization Decorators
```python
# src/auth/decorators.py
from functools import wraps
from flask import g
from typing import List, Union

def require_permissions(permissions: Union[str, List[str]], require_all: bool = False):
    """Decorator to check if user has required permissions."""
    if isinstance(permissions, str):
        permissions = [permissions]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return {'error': 'Authentication required'}, 401

            user = g.current_user
            has_permissions = [
                user.has_permission(perm)
                for perm in permissions
            ]

            if require_all and not all(has_permissions):
                return {
                    'error': 'Insufficient permissions',
                    'required': permissions
                }, 403

            if not require_all and not any(has_permissions):
                return {
                    'error': 'Insufficient permissions',
                    'required_any': permissions
                }, 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_roles(roles: Union[str, List[str]], require_all: bool = False):
    """Decorator to check if user has required roles."""
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return {'error': 'Authentication required'}, 401

            user = g.current_user
            has_roles = [user.has_role(role) for role in roles]

            if require_all and not all(has_roles):
                return {
                    'error': 'Insufficient roles',
                    'required': roles
                }, 403

            if not require_all and not any(has_roles):
                return {
                    'error': 'Insufficient roles',
                    'required_any': roles
                }, 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

## Authentication Flow

### 1. Login Implementation
```python
# src/routes/auth.py
from flask import Blueprint, request, jsonify
from src.models import User
from src.auth.jwt import jwt_manager
from src.services import auth_service

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return {
            'error': 'Email and password are required'
        }, 400

    user = auth_service.authenticate_user(email, password)
    if not user:
        return {
            'error': 'Invalid email or password'
        }, 401

    access_token = jwt_manager.create_access_token(user)
    refresh_token = jwt_manager.create_refresh_token(user)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }

@auth_bp.route('/refresh', methods=['POST'])
@refresh_token_required
def refresh():
    """Refresh access token using refresh token."""
    user = g.current_user
    access_token = jwt_manager.create_access_token(user)

    return {
        'access_token': access_token,
        'user': user.to_dict()
    }

@auth_bp.route('/logout', methods=['POST'])
@authenticate
def logout():
    """Logout user by invalidating tokens."""
    # In a real implementation, you might want to blacklist the tokens
    return {'message': 'Successfully logged out'}
```

### 2. Password Management
```python
# src/auth/password.py
from passlib.hash import pbkdf2_sha256
from typing import Tuple
import secrets
import string

class PasswordManager:
    def __init__(self, rounds: int = 100000):
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2-SHA256."""
        return pbkdf2_sha256.hash(password, rounds=self.rounds)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return pbkdf2_sha256.verify(password, password_hash)

    def generate_password(self, length: int = 12) -> Tuple[str, str]:
        """Generate a random password and its hash."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        password_hash = self.hash_password(password)
        return password, password_hash

password_manager = PasswordManager()
```

## Security Best Practices

### 1. Token Security
- Use secure algorithms (HS256, RS256)
- Implement token expiration
- Rotate secrets regularly
- Use refresh token pattern
- Implement token blacklisting

### 2. Password Security
- Use strong hashing algorithms
- Implement password policies
- Enforce MFA when possible
- Rate limit authentication attempts
- Implement account lockout

### 3. General Security
- Use HTTPS only
- Implement CORS properly
- Sanitize user input
- Use secure headers
- Regular security audits

## Common Pitfalls

### 1. Token Handling
```python
# Bad: Storing sensitive data in token
def create_token(user):
    return jwt.encode({
        'email': user.email,
        'password_hash': user.password_hash  # Never do this!
    }, secret_key)

# Good: Store only necessary data
def create_token(user):
    return jwt.encode({
        'sub': user.id,
        'roles': [role.name for role in user.roles]
    }, secret_key)
```

### 2. Password Storage
```python
# Bad: Using weak hashing
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # Never use MD5!

# Good: Using strong hashing
def hash_password(password):
    return password_manager.hash_password(password)
```

## Next Steps
After mastering authentication and authorization, proceed to:
1. Database Operations (3_database.md)
2. Error Handling (4_error_handling.md)
3. Testing (5_testing.md) 