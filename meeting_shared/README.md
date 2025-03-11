# Meeting Shared Package

A shared package for common functionality used across microservices in the Meeting App.

## Overview

This package contains shared utilities, middleware, models, and other components that are used by multiple microservices in the Meeting App. By centralizing these components, we ensure consistency across services and reduce code duplication.

## Installation

To install this package in development mode:

```bash
pip install -e /path/to/meeting_shared
```

Or add the following to your requirements.txt:

```
-e ../relative/path/to/meeting_shared
```

## Components

- **shared_logging**: Structured JSON logging with request ID tracking
- **middleware**: Flask middleware components (request ID, auth, etc.)
- **discovery**: Service discovery utilities
- **models**: Shared data models
- **schemas**: Shared API schemas
- **secrets**: Secret management utilities
- **utils**: General utility functions

## Usage

Import components from the package:

```python
from meeting_shared.shared_logging import setup_logging
from meeting_shared.middleware import register_middleware
```

## Features

### Service Discovery

The package includes a flexible service discovery system that supports multiple providers:

- **Static Discovery**: Uses environment variables or static configuration
- **Kubernetes Discovery**: Discovers services in a Kubernetes cluster

Service discovery includes health checks to detect unhealthy services:

```python
from meeting_shared.discovery import get_service_url

# Get URL for a service
auth_url = get_service_url('auth-service')

# Service details including health status
auth_service = get_service('auth-service')
if auth_service['status'] == 'healthy':
    # Service is healthy
```

### JWT Authentication

The package provides JWT authentication middleware with support for secret key rotation:

```python
from meeting_shared.middleware.auth import jwt_required

@app.route('/protected')
@jwt_required
def protected_route():
    return "This route is protected"
```

For Kubernetes deployments, use the included secret rotation script:

```bash
./k8s/scripts/manage-secrets.sh rotate -s jwt-secret
```

### Structured Logging

The package includes structured JSON logging with request ID tracking and correlation IDs:

```python
from meeting_shared.shared_logging import setup_logging

# Initialize logging
logger = setup_logging(app, service_name="my-service")

# Log with structured data
logger.info("User logged in", extra={"user_id": user.id})
```

### Log Sampling

For high-volume endpoints, the package includes log sampling to reduce log volume:

```python
from meeting_shared.shared_logging import setup_logging
from meeting_shared.shared_logging.sampling import SamplingConfig

# Configure sampling rates
sampling_config = SamplingConfig(
    default_rate=1.0,  # Log everything by default
    path_rates={
        r'^/api/health': 0.1,  # Log only 10% of health check requests
        r'^/api/metrics': 0.05  # Log only 5% of metrics requests
    },
    method_rates={
        'GET': 0.5  # Log 50% of GET requests
    },
    level_rates={
        'DEBUG': 0.1  # Log only 10% of DEBUG messages
    }
)

# Initialize logging with sampling
logger = setup_logging(
    app, 
    service_name="my-service",
    enable_sampling=True,
    sampling_config=sampling_config
)
```

## Development

When making changes to this shared package, remember to update all services that depend on it. 