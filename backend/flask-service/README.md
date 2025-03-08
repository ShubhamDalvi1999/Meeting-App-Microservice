# Meeting API Service

## Overview

The Meeting API Service is a Flask-based backend for managing meetings in the Meeting App platform. It provides REST API endpoints for creating, updating, and managing meetings, integrates with the authentication service, and handles real-time updates via Redis and WebSockets.

## Architecture

The service follows a modular architecture with well-defined responsibilities:

```
backend/
├── flask-service/         # Meeting API Service
│   ├── src/               # Application code
│   │   ├── core/          # Core functionality
│   │   │   ├── __init__.py    # Logging and initialization
│   │   │   ├── config.py      # Environment-specific configuration
│   │   │   ├── errors.py      # Error handling
│   │   │   └── health.py      # Health checks
│   │   ├── routes/        # API routes and endpoints
│   │   ├── utils/         # Utility functions
│   │   └── app.py         # Flask application factory
│   ├── shared/            # Shared modules with auth service
│   ├── migrations/        # Database migrations
│   └── tests/             # Unit and integration tests
```

## Enhanced Debugging

This service includes comprehensive logging and debugging capabilities:

1. **Centralized Logging**: All logging is handled through the `src.core` module, with appropriate log levels for each environment.

2. **Detailed Health Checks**: The `/health` endpoint provides detailed diagnostics for all dependencies and service components.

3. **Error Handling**: A robust error handling system provides consistent error responses and detailed logging of exceptions.

4. **Environment Diagnostics**: System information, environment variables, and configuration is logged at startup to aid in debugging deployment issues.

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (see `.env.example`)

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Run the development server:
   ```bash
   flask run
   ```

### Docker

The service can be run with Docker using the provided Dockerfile:

```bash
# Build the image
docker build -t meeting-api-service .

# Run the container
docker run -p 5000:5000 --env-file .env meeting-api-service
```

Or with docker-compose:

```bash
docker-compose up -d backend
```

## API Endpoints

### Health Check

- **GET** `/health`
  - Returns detailed health information about the service and its dependencies
  - Response: 200 OK (healthy) or 503 Service Unavailable (unhealthy)

### Meeting Endpoints

- **GET** `/api/meetings`
  - Lists all meetings for the authenticated user
  - Response: 200 OK

- **POST** `/api/meetings`
  - Creates a new meeting
  - Response: 201 Created

- **GET** `/api/meetings/{id}`
  - Gets details of a specific meeting
  - Response: 200 OK

- **PUT** `/api/meetings/{id}`
  - Updates a meeting
  - Response: 200 OK

- **DELETE** `/api/meetings/{id}`
  - Deletes a meeting
  - Response: 204 No Content

## Debugging Guidance

### Common Issues

1. **Database Connection Errors**
   - Check PostgreSQL connection string in `.env`
   - Verify PostgreSQL service is running
   - Check database logs for connection rejections

2. **Redis Connection Issues**
   - Verify Redis is running and accessible
   - Check Redis connection string in `.env`
   - Check for authentication failures in Redis logs

3. **Auth Service Integration**
   - Ensure AUTH_SERVICE_URL is correct
   - Verify SERVICE_KEY matches between services
   - Check auth service logs for connection attempts

### Enhanced Logging

To enable detailed logging, set `LOG_LEVEL=DEBUG` in your environment. This will provide:

- Detailed request and response information
- SQL queries and execution times
- Redis operations
- Authentication flow details

Log files are stored in the `/app/logs` directory:
- `app.log` - All application logs
- `error.log` - Error logs only
- `error_TIMESTAMP.json` - Detailed error reports (in development)

## Testing

Run the test suite with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=src
```

## Error Handling

The service uses standardized error responses:

```json
{
  "error": true,
  "message": "Error message",
  "status_code": 400,
  "timestamp": "2023-01-01T12:00:00.000Z",
  "details": {
    "field": "Error details"
  }
}
```

Error types include:
- ValidationError (422)
- AuthenticationError (401)
- AuthorizationError (403)
- NotFoundError (404)
- ServiceError (500)
- ConfigurationError (500)

## Performance Monitoring

The service includes basic performance metrics:
- Response times for key endpoints
- Database query times
- Redis operation latency
- External service call durations

For production monitoring, consider integrating Prometheus or similar. 