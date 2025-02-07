# Backend Services Documentation

## Overview
The backend of the application is built using a microservices architecture with two main services:
1. Flask Backend Service (REST API)
2. Node.js WebSocket Service (Real-time Communication)

## Application Structure

### 1. Project Layout
```
backend/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── meeting.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── meetings.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── meeting_service.py
│   └── utils/
│       ├── __init__.py
│       └── validators.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_meetings.py
└── requirements.txt
```

### 2. Application Factory
```python
# src/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_object=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object('src.config.DevelopmentConfig')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register blueprints
    from src.routes import auth_bp, meetings_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(meetings_bp, url_prefix='/api/meetings')

    # Register error handlers
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404

    @app.errorhandler(500)
    def server_error(error):
        return {'error': 'Internal server error'}, 500
```

## Flask Backend Service

### Purpose
The Flask service handles all HTTP-based API requests, including:
- User authentication and authorization
- Meeting management
- User profile management
- Database operations

### Key Components
1. **Authentication Service**
   - Handles user registration and login
   - JWT token generation and validation
   - Session management

2. **Meeting Service**
   - Meeting creation and management
   - Participant management
   - Meeting scheduling and notifications

3. **Database Service**
   - PostgreSQL database interactions
   - Data model management
   - Query optimization

### Flow
1. Client makes HTTP request to API endpoint
2. Request is authenticated via JWT middleware
3. Request is processed by appropriate service
4. Database operations are performed if needed
5. Response is sent back to client

### Technologies Used
- Python 3.9+
- Flask Framework
- SQLAlchemy ORM
- PostgreSQL
- JWT Authentication
- RESTful API Design

## Configuration Management

### 1. Configuration Classes
```python
# src/config.py
import os
from datetime import timedelta

class BaseConfig:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
```

### 2. Environment Variables
```python
# src/utils/config.py
from functools import lru_cache
from typing import Dict, Any
import os
import json

@lru_cache()
def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    config = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
        'MAIL_SERVER': os.getenv('MAIL_SERVER'),
        'MAIL_PORT': int(os.getenv('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', 'true').lower() == 'true',
        'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
    }
    
    # Load additional config from file if exists
    config_file = os.getenv('CONFIG_FILE')
    if config_file and os.path.exists(config_file):
        with open(config_file) as f:
            config.update(json.load(f))
    
    return config
```

## Node.js WebSocket Service

### Purpose
The Node.js service handles all real-time communications, including:
- Video/Audio streaming
- Chat functionality
- Whiteboard collaboration
- Real-time meeting state synchronization

### Key Components
1. **WebSocket Manager**
   - Connection handling
   - Event broadcasting
   - Room management

2. **Signaling Service**
   - WebRTC signaling
   - Peer connection management
   - ICE candidate exchange

3. **Meeting State Manager**
   - Real-time state synchronization
   - Participant status management
   - Meeting controls

### Flow
1. Client establishes WebSocket connection
2. Connection is authenticated
3. Client joins specific meeting room
4. Real-time events are broadcasted to room participants
5. WebRTC connections are established for media streaming

### Technologies Used
- Node.js
- Socket.IO
- WebRTC
- Redis (for state management)
- JWT Authentication

## Request Handling

### 1. Route Decorators
```python
# src/routes/meetings.py
from functools import wraps
from flask import Blueprint, request, jsonify
from src.models import Meeting
from src.services import meeting_service

meetings_bp = Blueprint('meetings', __name__)

def validate_meeting_input(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        required_fields = ['title', 'start_time', 'end_time']
        
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
            
        return f(*args, **kwargs)
    return decorated_function

@meetings_bp.route('/', methods=['POST'])
@validate_meeting_input
def create_meeting():
    data = request.get_json()
    meeting = meeting_service.create_meeting(data)
    return jsonify(meeting.to_dict()), 201
```

### 2. Request Validation
```python
# src/utils/validators.py
from datetime import datetime
from typing import Dict, Any, List, Tuple

class ValidationError(Exception):
    def __init__(self, errors: Dict[str, str]):
        self.errors = errors
        super().__init__('Validation error')

def validate_meeting_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    errors = {}
    
    # Validate title
    title = data.get('title', '').strip()
    if not title:
        errors['title'] = 'Title is required'
    elif len(title) > 100:
        errors['title'] = 'Title must be less than 100 characters'
    
    # Validate times
    try:
        start_time = datetime.fromisoformat(data.get('start_time', ''))
        end_time = datetime.fromisoformat(data.get('end_time', ''))
        
        if start_time < datetime.now():
            errors['start_time'] = 'Start time must be in the future'
        
        if end_time <= start_time:
            errors['end_time'] = 'End time must be after start time'
            
    except ValueError:
        errors['time_format'] = 'Invalid time format'
    
    if errors:
        raise ValidationError(errors)
        
    return data, list(errors.keys())
```

## Integration Points

### Database Integration
- Both services share the same PostgreSQL database
- Consistent data model across services
- Transaction management for data integrity

### Authentication Integration
- Shared JWT secret for token validation
- Consistent session management
- Single sign-on across services

### Event Communication
- Inter-service communication via Redis
- Event-driven architecture
- Message queue for asynchronous operations

## Security Measures
1. **Authentication**
   - JWT-based token authentication
   - Password hashing with bcrypt
   - Rate limiting on auth endpoints

2. **Data Protection**
   - Input validation and sanitization
   - SQL injection prevention
   - XSS protection

3. **Network Security**
   - HTTPS enforcement
   - WebSocket secure (WSS)
   - Network policy enforcement

## Scalability Considerations
1. **Horizontal Scaling**
   - Stateless service design
   - Load balancer ready
   - Session management via Redis

2. **Performance Optimization**
   - Database query optimization
   - Connection pooling
   - Caching strategies

3. **Resource Management**
   - Kubernetes resource limits
   - Auto-scaling configurations
   - Load monitoring and alerts 