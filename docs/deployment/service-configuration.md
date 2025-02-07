# Service Configuration

This document details the configuration of each service in the Meeting App.

## Service Overview

| Service    | Internal Port | External Port | Protocol |
|------------|--------------|---------------|----------|
| Frontend   | 3000         | 30000         | HTTP     |
| API        | 5000         | 30963         | HTTP     |
| WebSocket  | 3001         | 30283         | WS       |
| PostgreSQL | 5432         | N/A           | TCP      |
| Redis      | 6379         | N/A           | TCP      |

## Environment Variables

### Frontend Configuration
```yaml
NEXT_PUBLIC_API_URL: "http://localhost:30963"
NEXT_PUBLIC_WS_URL: "ws://localhost:30283"
NEXT_PUBLIC_BASE_URL: "http://localhost:30000"
```

### Backend Configuration
```yaml
# API Configuration
FLASK_ENV: "development"
FLASK_APP: "app.py"
API_HOST: "0.0.0.0"
API_PORT: "5000"
WS_HOST: "0.0.0.0"
WS_PORT: "3001"

# CORS Configuration
CORS_ORIGINS: "http://localhost:30000,http://meeting-app.local,http://localhost:3000"

# Database Configuration
POSTGRES_DB: "meetingapp"
POSTGRES_USER: "dev_user"
POSTGRES_HOST: "postgres"
POSTGRES_PORT: "5432"
DATABASE_URL: "postgresql://dev_user:dev-password-123@postgres:5432/meetingapp"

# Redis Configuration
REDIS_URL: "redis://:dev-redis-123@redis:6379/0"
REDIS_HOST: "redis"
REDIS_PORT: "6379"
```

## Health Checks

### Frontend Health Check
- Endpoint: `/api/health`
- Method: GET
- Response:
  ```json
  {
    "status": "healthy",
    "timestamp": "ISO-8601 timestamp"
  }
  ```

### Backend Health Checks
- Main: `/health`
- Database: `/health/db`
- Redis: `/health/redis`

## Resource Limits

### Frontend
```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

### Backend
```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

## Container Images

- Frontend: `meeting-app-frontend:dev`
- Backend API: `meeting-app-backend:dev`
- WebSocket: `meeting-app-websocket:dev`
- PostgreSQL: `postgres:15-alpine`
- Redis: `redis:7-alpine`

## Persistent Storage

### PostgreSQL
- Type: StatefulSet
- Storage: 10Gi
- StorageClass: standard

### Redis
- Type: Deployment
- Storage: EmptyDir (non-persistent for development) 