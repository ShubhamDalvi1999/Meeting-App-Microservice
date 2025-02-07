# Service Architecture Documentation

## Overview
The application follows a microservices architecture with two main backend services:
- **Auth Service** (Port 5001): Handles authentication, authorization, and user management
- **Flask Service** (Port 5000): Handles business logic and meeting management

## Service Components

### 1. Auth Service
- **Primary Responsibilities**:
  - User authentication and authorization
  - Session management
  - OAuth integration (Google)
  - Email verification
  - Password reset functionality
  - Token management

- **Key Features**:
  - JWT-based authentication
  - Secure password handling
  - Multi-device session support
  - Rate limiting
  - Email verification
  - OAuth 2.0 integration

### 2. Flask Service
- **Primary Responsibilities**:
  - Meeting management
  - User data synchronization
  - Business logic
  - API endpoints for frontend

- **Key Features**:
  - Meeting CRUD operations
  - User management
  - Real-time updates
  - Data validation

## Service Integration

### Authentication Flow
1. User authenticates through Auth Service
2. Auth Service generates JWT token
3. Token is validated by both services
4. Flask Service maintains synchronized user state

### Data Synchronization
- **User Data**:
  ```json
  {
    "id": "user_id",
    "email": "user@example.com",
    "is_active": true,
    "is_email_verified": true,
    "first_name": "John",
    "last_name": "Doe"
  }
  ```

- **Session Data**:
  ```json
  {
    "session_id": "session_id",
    "user_id": "user_id",
    "expires_at": "timestamp",
    "device_info": {}
  }
  ```

### Security Measures
1. Service-to-Service Authentication:
   - Service key authentication
   - Protected integration endpoints
   - Secure communication channels

2. Token Management:
   - Shared JWT secret
   - Synchronized token validation
   - Coordinated token revocation

3. Session Management:
   - Synchronized session states
   - Coordinated cleanup
   - Secure session storage

## Infrastructure

### Databases
1. **Auth Database** (PostgreSQL):
   - User accounts
   - Sessions
   - OAuth tokens
   - Email verification
   - Password reset tokens

2. **Main Database** (PostgreSQL):
   - User profiles
   - Meetings
   - Participants
   - Application data

### Caching & Message Queue
- **Redis**:
  - Session caching
  - Rate limiting
  - Temporary data storage

## Error Handling & Reliability

### Retry Mechanism
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
```

### Circuit Breaker
```python
@circuit(
    failure_threshold=5,
    recovery_timeout=60
)
```

### Health Checks
- Regular service health monitoring
- Database connection verification
- Redis connection verification

## Configuration

### Environment Variables
```env
# Auth Service
AUTH_DATABASE_URL=postgresql://postgres:postgres@auth-db:5432/auth_db
JWT_SECRET_KEY=shared-secret-key
SERVICE_KEY=service-authentication-key

# Flask Service
DATABASE_URL=postgresql://user:pass@db:5432/app
AUTH_SERVICE_URL=http://auth-service:5001
```

## Deployment

### Docker Services
```yaml
services:
  auth-service:
    ports: 
      - "5001:5001"
    depends_on:
      - auth-db
      - redis

  backend:
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
      - auth-service
```

## Monitoring & Logging

### Logging Strategy
- Structured logging
- Service-specific logs
- Integration event logging
- Error tracking

### Metrics
- Service health
- Authentication success/failure rates
- Session statistics
- API response times

## Development Guidelines

### Service Communication
1. Always use service integration classes
2. Implement proper error handling
3. Maintain data consistency
4. Log important events

### Security Guidelines
1. Never expose service keys
2. Validate all incoming data
3. Implement rate limiting
4. Use secure communication

### Testing
1. Unit tests for each service
2. Integration tests for service communication
3. End-to-end testing
4. Security testing 