# Flask Service API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
All endpoints except public routes require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt-token>
```

## Endpoints

### Health Check
```http
GET /health
```
Returns the health status of the service and its dependencies.

#### Response
```json
{
    "status": "healthy",
    "service": "flask",
    "database": "connected",
    "redis": "connected",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### User Management

#### Get Current User
```http
GET /users/me
```
Returns the currently authenticated user's profile.

##### Response
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_email_verified": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Update User Profile
```http
PATCH /users/me
```

##### Request Body
```json
{
    "first_name": "John",
    "last_name": "Doe"
}
```

##### Response
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_email_verified": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### Meetings

#### Create Meeting
```http
POST /meetings
```

##### Request Body
```json
{
    "title": "Team Sync",
    "description": "Weekly team sync meeting",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T11:00:00Z",
    "participants": ["user1@example.com", "user2@example.com"],
    "is_recurring": false
}
```

##### Response
```json
{
    "id": "uuid",
    "title": "Team Sync",
    "description": "Weekly team sync meeting",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T11:00:00Z",
    "creator": {
        "id": "uuid",
        "email": "user@example.com",
        "name": "John Doe"
    },
    "participants": [
        {
            "id": "uuid",
            "email": "user1@example.com",
            "name": "User One"
        },
        {
            "id": "uuid",
            "email": "user2@example.com",
            "name": "User Two"
        }
    ],
    "is_recurring": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Get Meetings
```http
GET /meetings
```

##### Query Parameters
- `start_date` (optional): Filter meetings after this date (ISO format)
- `end_date` (optional): Filter meetings before this date (ISO format)
- `page` (optional): Page number for pagination (default: 1)
- `per_page` (optional): Items per page (default: 10)

##### Response
```json
{
    "items": [
        {
            "id": "uuid",
            "title": "Team Sync",
            "description": "Weekly team sync meeting",
            "start_time": "2024-01-01T10:00:00Z",
            "end_time": "2024-01-01T11:00:00Z",
            "creator": {
                "id": "uuid",
                "email": "user@example.com",
                "name": "John Doe"
            },
            "participants": [],
            "is_recurring": false,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ],
    "total": 100,
    "page": 1,
    "per_page": 10,
    "pages": 10
}
```

#### Get Meeting
```http
GET /meetings/{meeting_id}
```

##### Response
```json
{
    "id": "uuid",
    "title": "Team Sync",
    "description": "Weekly team sync meeting",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T11:00:00Z",
    "creator": {
        "id": "uuid",
        "email": "user@example.com",
        "name": "John Doe"
    },
    "participants": [],
    "is_recurring": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Update Meeting
```http
PUT /meetings/{meeting_id}
```

##### Request Body
```json
{
    "title": "Updated Team Sync",
    "description": "Updated weekly team sync meeting",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T11:00:00Z",
    "participants": ["user1@example.com", "user2@example.com"],
    "is_recurring": false
}
```

##### Response
Same as Get Meeting response

#### Delete Meeting
```http
DELETE /meetings/{meeting_id}
```

##### Response
```json
{
    "message": "Meeting deleted successfully"
}
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "validation_error",
    "message": "Invalid request parameters",
    "details": {
        "field": ["error message"]
    }
}
```

### 401 Unauthorized
```json
{
    "error": "unauthorized",
    "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
    "error": "forbidden",
    "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
    "error": "not_found",
    "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
    "error": "rate_limit_exceeded",
    "message": "Too many requests",
    "details": {
        "retry_after": 60
    }
}
```

### 500 Internal Server Error
```json
{
    "error": "internal_server_error",
    "message": "An unexpected error occurred"
}
``` 