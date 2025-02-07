# Flask Service Integration Documentation

## Overview
This document describes the integration points between the Flask service and other components of the system.

## Dependencies
- Auth Service: User authentication and session management
- Redis: Rate limiting and caching
- PostgreSQL: Primary database
- Prometheus: Metrics collection

## Shared Components
The service uses several shared components from the `backend/shared` directory:

### 1. Configuration
```python
from shared.config import config
app.config.from_object(config[config_name])
```

### 2. Database
```python
from shared.database import db, init_db, transaction_context
```

### 3. Middleware
- Error Handling: `shared.middleware.error_handler`
- Validation: `shared.middleware.validation`
- Rate Limiting: `shared.middleware.rate_limiter`
- Authentication: `shared.middleware.auth`

### 4. Schemas
Base schemas for request/response validation are in `shared.schemas.base`

## Service Integration Points

### 1. Auth Service Integration
The service communicates with the Auth service through several endpoints:

#### Token Validation
```http
POST /api/auth/validate-token
Authorization: Bearer <service-key>
{
    "token": "<jwt-token>"
}
```

#### Session Synchronization
```http
POST /api/auth/sync-session
Authorization: Bearer <service-key>
{
    "user_id": "<user-id>",
    "session_data": {
        "expires_at": "<timestamp>",
        "is_active": true
    }
}
```

#### User Data Synchronization
```http
POST /api/auth/sync-user
Authorization: Bearer <service-key>
{
    "id": "<user-id>",
    "email": "<email>",
    "first_name": "<first-name>",
    "last_name": "<last-name>",
    "is_active": true,
    "is_email_verified": true
}
```

## Metrics
Prometheus metrics are exposed on port 9090 (configurable) and include:
- HTTP request counts and durations
- Database connection counts
- Redis connection counts

## Environment Variables
See `.env.example` for required environment variables.

## Health Check
The service exposes a health check endpoint:
```http
GET /health
```

Response:
```json
{
    "status": "healthy",
    "service": "flask",
    "database": "connected",
    "redis": "connected",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Handling
All errors follow a standard format:
```json
{
    "error": "<error-type>",
    "message": "<error-message>",
    "details": {
        // Optional additional error details
    }
}
```

## Logging
Logs are written to both console and file (if configured) with the following format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Security
- All service-to-service communication requires service key authentication
- CSRF protection is enabled for browser endpoints
- Rate limiting is applied to all endpoints
- All sensitive data is validated and sanitized 