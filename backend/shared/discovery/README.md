# Service Discovery Module

This module provides a unified interface for service discovery across various backends. It allows services to locate and communicate with each other dynamically, without hardcoding service locations.

## Features

- **Multiple Backend Support**: Works with environment variables, static configuration, Consul, and Kubernetes.
- **Automatic Provider Detection**: Automatically detects the appropriate provider based on the environment.
- **Consistent Interface**: Provides a unified interface regardless of the underlying discovery mechanism.
- **Service Registration**: Supports registering and deregistering services (where applicable).
- **Caching**: Implements caching to improve performance.

## Usage

### Basic Usage

```python
from backend.shared.discovery import get_service_url

# Get the URL for a service
auth_url = get_service_url('auth')
backend_url = get_service_url('backend')

# Make a request to the service
import requests
response = requests.get(f"{auth_url}/health")
```

### Getting Detailed Service Information

```python
from backend.shared.discovery import get_service

# Get detailed information about a service
auth_service = get_service('auth')
print(f"Auth service is at {auth_service['url']} on port {auth_service['port']}")
```

### Getting All Services

```python
from backend.shared.discovery import get_services

# Get all available services
services = get_services()
for name, service in services.items():
    print(f"Service {name} is at {service.get('url')}")
```

### Registering a Service

```python
from backend.shared.discovery import register_service

# Register a service
register_service('my-service', {
    'address': 'localhost',
    'port': 8080,
    'tags': ['http', 'api'],
    'check': {
        'http': 'http://localhost:8080/health',
        'interval': '10s'
    }
})
```

### Deregistering a Service

```python
from backend.shared.discovery import deregister_service

# Deregister a service
deregister_service('my-service')
```

### Explicitly Setting the Provider

```python
from backend.shared.discovery import set_discovery_provider
from backend.shared.discovery.consul import ConsulServiceDiscovery

# Create a custom provider
provider = ConsulServiceDiscovery(host='consul.example.com', port=8500)

# Set it as the global provider
set_discovery_provider(provider)
```

## Supported Providers

### Environment Variables (`EnvServiceDiscovery`)

Uses environment variables to discover services. This is the simplest provider and serves as a fallback.

Environment variables should be in the format:
- `SERVICE_<NAME>_URL`: The full URL to the service
- `SERVICE_<NAME>_HOST`: The hostname of the service
- `SERVICE_<NAME>_PORT`: The port of the service

Example:
```
SERVICE_AUTH_URL=http://auth-service:5001
SERVICE_BACKEND_HOST=backend-service
SERVICE_BACKEND_PORT=5000
```

### Static Configuration (`StaticServiceDiscovery`)

Uses a static JSON or YAML configuration file to discover services. This is useful for development and testing environments, or when using Docker Compose.

Example configuration file:
```json
{
  "auth": {
    "url": "http://auth-service:5001",
    "address": "auth-service",
    "port": 5001
  },
  "backend": {
    "url": "http://backend-service:5000",
    "address": "backend-service",
    "port": 5000
  }
}
```

### Consul (`ConsulServiceDiscovery`)

Uses HashiCorp Consul for service discovery. This is a production-ready solution that supports health checks and dynamic service registration.

Requires the `python-consul` package to be installed.

### Kubernetes (`KubernetesServiceDiscovery`)

Uses the Kubernetes API for service discovery. This is ideal for applications running in a Kubernetes cluster.

Requires the `kubernetes` package to be installed.

## Configuration

The module can be configured using environment variables:

- `SERVICE_DISCOVERY_PROVIDER`: The provider to use (`env`, `static`, `consul`, or `kubernetes`).
- `SERVICE_DISCOVERY_CONFIG_FILE`: The path to the configuration file for the static provider.
- `CONSUL_HOST`, `CONSUL_PORT`, `CONSUL_TOKEN`: Configuration for the Consul provider.
- `KUBERNETES_NAMESPACE`: The namespace to use for Kubernetes service discovery.

## Development

### Adding a New Provider

To add a new provider:

1. Create a new file in the `discovery` directory (e.g., `myservice.py`).
2. Implement a class that inherits from `ServiceDiscovery` and implements all required methods.
3. Update the `__init__.py` file to import and register the new provider.

Example:

```python
from .base import ServiceDiscovery

class MyServiceDiscovery(ServiceDiscovery):
    def __init__(self, config_param=None):
        self.config_param = config_param
        
    def get_service_url(self, service_name, default=None):
        # Implementation
        
    def get_service(self, service_name, default=None):
        # Implementation
        
    def get_services(self):
        # Implementation
        
    def register_service(self, service_name, service_data):
        # Implementation
        
    def deregister_service(self, service_name):
        # Implementation
```

Then update `__init__.py`:

```python
try:
    from .myservice import MyServiceDiscovery
    HAS_MYSERVICE = True
except ImportError:
    HAS_MYSERVICE = False

def get_discovery_provider(provider_type=None):
    # ...
    elif provider_type == 'myservice' and HAS_MYSERVICE:
        return MyServiceDiscovery()
    # ...
``` 