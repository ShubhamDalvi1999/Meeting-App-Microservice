# Service Integration API Documentation

## Overview
This document describes the internal API endpoints used for service integration between the Auth Service and Flask Service.

## Authentication
All integration endpoints require service authentication using the `X-Service-Key` header.

```http
X-Service-Key: your-service-key
```

## Endpoints

### 1. Validate Token
Validates a JWT token across services.

```http
POST /api/auth/validate-token
```

**Request:**
```json
{
    "token": "jwt-token-string"
}
```

**Response Success (200):**
```json
{
    "user_id": 123,
    "exp": 1234567890,
    "iat": 1234567890,
    "type": "access"
}
```

**Response Error (401):**
```json
{
    "error": "Invalid token"
}
```

### 2. Sync User Session
Synchronizes user session data between services.

```http
POST /api/auth/sync-session
```

**Request:**
```json
{
    "user_id": 123,
    "token": "jwt-token-string",
    "session_data": {
        "session_id": "session-uuid",
        "device_info": {
            "device_type": "mobile",
            "browser": "chrome"
        },
        "expires_at": "2024-01-01T00:00:00Z"
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response Success (200):**
```json
{
    "status": "success"
}
```

**Response Error (400):**
```json
{
    "error": "Failed to sync session"
}
```

### 3. Sync User Data
Synchronizes user data between services.

```http
POST /api/auth/sync-user
```

**Request:**
```json
{
    "id": 123,
    "email": "user@example.com",
    "is_active": true,
    "is_email_verified": true,
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "url-to-picture",
    "last_sync": "2024-01-01T00:00:00Z"
}
```

**Response Success (200):**
```json
{
    "status": "success"
}
```

**Response Error (400):**
```json
{
    "error": "Failed to sync user data"
}
```

### 4. Revoke User Sessions
Revokes all sessions for a user across services.

```http
POST /api/auth/revoke-user-sessions
```

**Request:**
```json
{
    "user_id": 123,
    "reason": "user_requested",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response Success (200):**
```json
{
    "status": "success"
}
```

**Response Error (400):**
```json
{
    "error": "Failed to revoke sessions"
}
```

## Error Handling

### Common Error Responses

#### Invalid Service Key (403)
```json
{
    "error": "Invalid service key"
}
```

#### Internal Server Error (500)
```json
{
    "error": "Internal server error"
}
```

### Error Codes
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting
- Maximum 100 requests per minute per service
- Rate limit headers included in response:
  ```http
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1234567890
  ```

## Best Practices

### 1. Error Handling
- Always check response status codes
- Implement retry logic for failed requests
- Log all errors with appropriate context

### 2. Data Validation
- Validate all data before sending
- Check response data integrity
- Handle missing or invalid fields gracefully

### 3. Security
- Keep service keys secure
- Use HTTPS for all communications
- Validate all tokens and credentials

### 4. Performance
- Implement caching where appropriate
- Use bulk operations when possible
- Monitor response times

## Example Implementation

### Python Example
```python
def sync_user_data(user_data):
    headers = {
        'X-Service-Key': config.SERVICE_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{config.SERVICE_URL}/api/auth/sync-user",
            json=user_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to sync user data: {str(e)}")
        raise
``` 