# Backend Architecture Documentation

## 1. Core Components

### Authentication System (`auth.py`)
```python
# Registration Flow
@auth_bp.route('/register', methods=['POST'])
- Validates email format and password strength
- Checks for duplicate email/username
- Creates new user with hashed password
- Returns 201 on success

# Login Flow
@auth_bp.route('/login', methods=['POST'])
- Validates credentials
- Generates JWT token with configurable expiry
- Returns token and user details

# Token Verification
@auth_bp.route('/verify-token', methods=['POST'])
- Validates JWT token format and signature
- Returns user details if token is valid
```

### Meeting Management (`meetings.py`)
```python
# Authentication Middleware
@token_required
- Validates JWT token in request header
- Handles different token error cases
- Injects current_user into route handlers

# Meeting Operations
- Create meetings with unique codes
- Join meetings using codes
- List user's meetings
- End/delete meetings
```

### Security Features
```python
# Token Structure
{
    'user_id': user.id,
    'email': user.email,
    'exp': expiration_time
}

# Error Handling
- ExpiredSignatureError: Token timeout
- InvalidTokenError: Malformed token
- InvalidKeyError: Wrong secret key
- InvalidAlgorithmError: Wrong algorithm
```

### Environment Configuration
```yaml
# Development Secrets (k8s/config/development/secrets.yaml)
JWT_SECRET_KEY: dev-jwt-secret-123
JWT_EXPIRY_DAYS: 1 (default)
```

## 2. Database Architecture

### Database: PostgreSQL
```yaml
# From docker-compose.yml
db:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=meetingapp
```

### SQLAlchemy Integration

#### 1. ORM (Object-Relational Mapping)
```python
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    # ... other fields
```

#### 2. Database Relationships
```python
class Meeting(db.Model):
    host = relationship('User', back_populates='hosted_meetings')
```

#### 3. Migration Support
```python
# From app.py
migrate = Migrate(app, db)
```

### Why SQLAlchemy?

#### a) Abstraction Layer
- Provides database-agnostic code
- Can switch databases without changing application code
- Handles SQL dialect differences

#### b) Security
- Automatic SQL injection prevention
- Parameter sanitization
- Secure connection management

#### c) Performance
- Connection pooling
- Query optimization
- Lazy loading of relationships

#### d) Developer Productivity
- Python-native syntax
- Automatic schema generation
- Built-in validation

### Database Configuration
```python
# From app.py
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

### Database Models Structure
```python
# Models defined:
- User: Authentication and user data
- Meeting: Meeting sessions
- MeetingParticipant: Many-to-many relationship for meetings
```

### Migration Support
```python
# migrations/env.py handles:
- Database schema versioning
- Automatic migration generation
- Up/down migration scripts
```

### Kubernetes Integration
```yaml
# Database credentials stored in k8s secrets
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: postgres
  password: postgres
  database-url: postgresql://postgres:postgres@postgres:5432/meetingapp
```

## 3. Best Practices Implemented
- Password hashing
- Email validation
- Token-based authentication
- Secure error handling
- Database transaction management
- Input validation
- Case-insensitive email handling
- Configurable token expiration

This architecture provides a secure, scalable, and maintainable foundation for the meeting application, with proper separation of concerns and robust error handling. The JWT-based authentication system allows for stateless authentication, which works well in a containerized environment. 