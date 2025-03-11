# Meeting Application

A comprehensive meeting management application with authentication, real-time communication, and calendar integration.

## System Architecture

The application is built using a microservices architecture consisting of:

- **Frontend**: Next.js application for the user interface
- **Backend API**: Flask-based API for meeting management
- **Auth Service**: Flask-based microservice for authentication and user management
- **WebSocket Service**: Node.js-based WebSocket server for real-time communication
- **Databases**: PostgreSQL for persistent data storage
- **Redis**: For caching, pub/sub messaging, and session storage
- **Monitoring**: Prometheus and Grafana for metrics and monitoring
- **Shared Package**: Common utilities and middleware shared across services

### Shared Package

The `meeting_shared` package contains common functionality used across all microservices in the Meeting App. This ensures consistency and reduces code duplication.

#### Installation

For development, install the package in editable mode:

```bash
# From the project root
pip install -e meeting_shared
```

Or add to your service's requirements.txt:
```
-e ../meeting_shared
```

#### Components

- **shared_logging**: Structured JSON logging with request ID tracking
  ```python
  from meeting_shared.shared_logging import setup_logging
  
  # Initialize logging
  logger = setup_logging(app, service_name="my-service")
  ```

- **middleware**: Flask middleware components
  ```python
  from meeting_shared.middleware import register_middleware
  from meeting_shared.middleware.auth import jwt_required
  
  # Register all middleware
  register_middleware(app)
  
  # Use auth decorator
  @app.route("/protected")
  @jwt_required
  def protected_route():
      return {"message": "Protected resource"}
  ```

- **discovery**: Service discovery utilities
  ```python
  from meeting_shared.discovery import get_service_url
  
  # Get URL for a service
  auth_url = get_service_url("auth-service")
  ```

- **secrets**: Secret management
  ```python
  from meeting_shared.secrets import get_secret
  
  # Get a secret
  api_key = get_secret("api.key")
  ```

#### Development Guidelines

1. **Adding New Features**
   - Place shared code in the appropriate module
   - Update tests in the `tests/` directory
   - Document new functionality in docstrings

2. **Dependencies**
   - Add new dependencies to `setup.py`
   - Keep dependencies minimal and version-pinned

3. **Testing**
   ```bash
   # Run tests
   cd meeting_shared
   pytest
   ```

4. **Code Style**
   - Follow PEP 8
   - Use type hints
   - Document public interfaces

5. **Version Control**
   - Create feature branches from `main`
   - Write descriptive commit messages
   - Update CHANGELOG.md for significant changes

#### Docker Integration

The shared package is automatically mounted in development:
```yaml
volumes:
  - ./meeting_shared:/app/meeting_shared
```

For production, it's installed during the build process:
```dockerfile
COPY meeting_shared /app/meeting_shared/
RUN pip install -e /app/meeting_shared
```

### Advanced Features

The application includes several advanced features for enterprise-grade deployments:

- **Service Discovery**: Dynamic service location and communication between microservices
- **Secret Management**: Secure handling of sensitive information across various backends
- **Integration Testing**: Comprehensive testing of service interactions
- **Centralized Logging**: Structured logging with correlation IDs across services
- **Circuit Breaking**: Resilient service communication with automatic failure handling
- **Performance Monitoring**: Real-time metrics and monitoring

## Prerequisites

- Docker and Docker Compose
- Git
- Make (optional, for using Makefile)

### Windows-Specific Requirements

- Docker Desktop
- PowerShell 5.0 or higher for running scripts
- Git Bash for bash scripts (optional)

## Quick Start

### Setting Up Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/meeting-app.git
   cd meeting-app
   ```

2. Create a `.env` file by copying the example:
   ```bash
   # For Linux/macOS
   cp .env.example .env
   
   # For Windows
   copy .env.example .env
   ```

3. Modify the `.env` file with your desired configuration values.

### Starting the Application

#### Using Scripts (Recommended)

For Windows:
```powershell
# Ensure PowerShell execution policy allows running scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the start script
.\start.ps1
```

For Linux/macOS:
```bash
# Make the script executable
chmod +x start.sh

# Run the start script
./start.sh
```

#### Manual Startup

Start the services in the following order:

```bash
# 1. Start database services
docker-compose up -d postgres auth-db redis

# 2. Wait for databases to initialize
sleep 15

# 3. Start the auth service
docker-compose up -d auth-service

# 4. Wait for auth service
sleep 10

# 5. Start the backend service
docker-compose up -d backend

# 6. Start remaining services
docker-compose up -d websocket frontend prometheus grafana
```

### Database Migrations

Run migrations to initialize the database schema:

For Windows:
```powershell
.\migrate.ps1 -ForceInit -Upgrade
```

For Linux/macOS:
```bash
chmod +x migrate.sh
./migrate.sh --force-init --upgrade
```

## Accessing the Application

Once all services are started, you can access the application at:

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:5000](http://localhost:5000)
- **Auth Service**: [http://localhost:5001](http://localhost:5001)
- **WebSocket Service**: [http://localhost:3001](http://localhost:3001)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3002](http://localhost:3002)

## Development

### Rebuilding Services

If you need to rebuild a specific service after code changes:

```bash
docker-compose build <service-name>
docker-compose up -d <service-name>
```

### Viewing Logs

To view logs for a specific service:

```bash
docker-compose logs <service-name>
```

To follow logs in real-time:

```bash
docker-compose logs -f <service-name>
```

### Running Tests

#### Unit Tests

```bash
docker-compose -f docker-compose.test.yml up
```

#### Integration Tests

Run integration tests to verify service interactions:

```bash
# For Windows
.\run-integration-tests.ps1

# For Linux/macOS
chmod +x run-integration-tests.sh
./run-integration-tests.sh
```

## Advanced Features

### Service Discovery

The application includes a flexible service discovery system that supports multiple backends:

- **Environment Variables**: Simple configuration for development
- **Static Configuration**: JSON/YAML-based configuration for Docker Compose
- **Consul**: For production deployments with health checks
- **Kubernetes**: Native service discovery in Kubernetes environments

For more information, see the [Service Discovery Documentation](backend/shared/discovery/README.md).

### Secret Management

Secure handling of sensitive information with support for multiple backends:

- **Environment Variables**: Simple configuration for development
- **File-Based**: For Docker and Kubernetes secrets
- **HashiCorp Vault**: Advanced secret management with rotation
- **AWS Secrets Manager**: Cloud-native secret management

For more information, see the [Secret Management Documentation](backend/shared/secrets/README.md).

### Integration Testing

The application includes a comprehensive integration testing framework:

- **Service Mocking**: Mock responses from dependent services
- **Authentication Testing**: Verify authentication flows
- **End-to-End Testing**: Test complete user journeys

To run integration tests:

```bash
# For auth service
cd backend/auth-service
python -m pytest tests/integration

# For backend service
cd backend/flask-service
python -m pytest tests/integration
```

## Troubleshooting

For common issues and solutions, please refer to the [Troubleshooting Guide](TROUBLESHOOTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Backend Architecture Standardization

This document summarizes the standardization changes implemented to improve consistency, reliability, and maintainability across backend services.

## Key Improvements

1. **Standardized Configuration System**
   - Unified configuration classes across services
   - Environment-specific configs (development, testing, production)
   - Service-specific configs (auth, flask, websocket)
   - Consistent environment variable handling

2. **Unified Logging Framework**
   - Structured JSON logging with consistent formatting
   - Request ID and correlation ID tracking in logs
   - Configurable log levels and outputs
   - Third-party library log level management

3. **Consistent Middleware Architecture**
   - Standard middleware interface
   - Centralized middleware registration
   - Request ID middleware for request tracking
   - Fallback mechanisms for backward compatibility

4. **Standardized Error Handling**
   - Common error classes with consistent responses
   - Structured error responses with request IDs
   - Detailed logging of exceptions
   - Consistent HTTP status codes

5. **HTTP Utilities Standardization**
   - Request ID propagation in HTTP requests
   - Retry mechanisms for transient failures
   - Consistent logging of HTTP requests
   - Simplified API for common HTTP methods

6. **Import System Improvements**
   - Fallback mechanisms for backward compatibility
   - Clear import paths for shared modules
   - Graceful handling of missing dependencies

7. **Application Factory Standardization**
   - Consistent initialization across services
   - Standard health check endpoints
   - Unified extension registration
   - Proper error handling during startup

## Project Structure

```
backend/
├── shared/                      # Shared modules used across services
│   ├── __init__.py              # Shared module import helpers
│   ├── config.py                # Standardized configuration
│   ├── errors.py                # Common error classes
│   ├── logging/                 # Logging framework
│   │   ├── __init__.py          # Logging module exports
│   │   └── config.py            # Logging configuration
│   ├── middleware/              # Shared middleware
│   │   ├── __init__.py          # Middleware registration
│   │   └── request_id.py        # Request ID middleware
│   └── utils/                   # Utility functions
│       ├── __init__.py          # Utils module exports
│       └── http.py              # HTTP request utilities
├── auth-service/                # Authentication service
│   └── src/
│       ├── app.py               # Main application factory
│       └── core/                # Core functionality
└── flask-service/               # Main backend API service
    └── src/
        ├── app.py               # Main application factory
        └── core/                # Core functionality
```

## Benefits of Standardization

1. **Improved Maintainability**
   - Consistent patterns make code easier to understand
   - Reduced duplication across services
   - Centralized configuration and error handling

2. **Enhanced Reliability**
   - Robust error handling and logging
   - Request tracking across services
   - Proper fallback mechanisms

3. **Better Observability**
   - Structured logs with request context
   - Consistent health check endpoints
   - Detailed error information

4. **Simplified Development**
   - Standard interfaces for common functionality
   - Reduced cognitive load for developers
   - Easier onboarding for new team members

## Next Steps

1. Add comprehensive test coverage for shared modules
2. Implement distributed tracing with OpenTelemetry
3. Add centralized metrics collection
4. Create deployment automation for shared modules
5. Add comprehensive documentation 