# Secrets Management Module

This module provides a unified interface for managing secrets across various backends. It allows services to securely access sensitive information without hardcoding secrets in the codebase.

## Features

- **Multiple Backend Support**: Works with environment variables, file-based secrets, HashiCorp Vault, and AWS Secrets Manager.
- **Automatic Provider Detection**: Automatically detects the appropriate provider based on the environment.
- **Consistent Interface**: Provides a unified interface regardless of the underlying secrets backend.
- **Caching**: Implements caching to improve performance and reduce API calls.
- **Secure by Default**: Follows security best practices for handling sensitive information.

## Usage

### Basic Usage

```python
from backend.shared.secrets import get_secret

# Get a secret
db_password = get_secret('database/password')
api_key = get_secret('api/key')

# Use the secret
db_connection = connect_to_db(password=db_password)
```

### Getting Multiple Secrets

```python
from backend.shared.secrets import get_secrets

# Get multiple secrets at once
credentials = get_secrets(['database/username', 'database/password', 'api/key'])
print(f"Connecting as {credentials['database/username']}")
```

### Checking if a Secret Exists

```python
from backend.shared.secrets import has_secret

# Check if a secret exists
if has_secret('optional/feature/api_key'):
    # Use the optional feature
    api_key = get_secret('optional/feature/api_key')
    enable_feature(api_key)
```

### Explicitly Setting the Provider

```python
from backend.shared.secrets import set_secret_manager
from backend.shared.secrets.vault import VaultSecretManager

# Create a custom provider
manager = VaultSecretManager(url='https://vault.example.com:8200', token='my-token')

# Set it as the global provider
set_secret_manager(manager)
```

## Supported Providers

### Environment Variables (`EnvSecretManager`)

Uses environment variables to store secrets. This is the simplest provider and serves as a fallback.

Environment variables can be prefixed to organize secrets:
```
DB_PASSWORD=mysecretpassword
API_KEY=mysecretapikey
```

With the default prefix of `''` (empty string), you would access these as:
```python
db_password = get_secret('DB_PASSWORD')
api_key = get_secret('API_KEY')
```

With a prefix of `SECRET_`, you would set:
```
SECRET_DB_PASSWORD=mysecretpassword
SECRET_API_KEY=mysecretapikey
```

And access them as:
```python
db_password = get_secret('DB_PASSWORD')
api_key = get_secret('API_KEY')
```

### File-Based Secrets (`FileSecretManager`)

Uses files to store secrets. This is useful for Docker and Kubernetes environments that mount secrets as files.

Example directory structure:
```
/app/secrets/
  database/
    username
    password
  api/
    key
```

You would access these as:
```python
db_username = get_secret('database/username')
db_password = get_secret('database/password')
api_key = get_secret('api/key')
```

### HashiCorp Vault (`VaultSecretManager`)

Uses HashiCorp Vault for secret management. This is a production-ready solution with advanced features like secret rotation, access control, and audit logging.

Requires the `hvac` package to be installed.

Example Vault structure:
```
secret/
  database/
    username: myuser
    password: mypassword
  api/
    key: myapikey
```

You would access these as:
```python
db_username = get_secret('database/username')
db_password = get_secret('database/password')
api_key = get_secret('api/key')
```

### AWS Secrets Manager (`AWSSecretManager`)

Uses AWS Secrets Manager for secret management. This is a fully managed service that makes it easy to rotate, manage, and retrieve secrets.

Requires the `boto3` package to be installed.

Example AWS Secrets Manager structure:
```
myapp/database
myapp/api
```

You would access these as:
```python
db_secrets = get_secret('database')  # Returns the entire JSON object
api_secrets = get_secret('api')
```

Or with specific keys:
```python
db_password = get_secret('database#password')  # Uses '#' to separate the secret name from the key
api_key = get_secret('api#key')
```

## Configuration

The module can be configured using environment variables:

- `SECRET_MANAGER_TYPE`: The provider to use (`env`, `file`, `vault`, or `aws`).
- `SECRET_MANAGER_PREFIX`: The prefix for environment variables (for `EnvSecretManager`).
- `SECRET_MANAGER_PATH`: The path to the secrets directory (for `FileSecretManager`).
- `VAULT_ADDR`, `VAULT_TOKEN`: Configuration for the Vault provider.
- `AWS_REGION`, `AWS_SECRET_PREFIX`: Configuration for the AWS Secrets Manager provider.

## Security Considerations

- **Memory Management**: Secrets are stored as strings in memory, which means they could potentially be exposed in memory dumps or logs. Consider using secure string types if available in your environment.
- **Logging**: Be careful not to log secrets. The module avoids logging secret values, but you should ensure your application code doesn't log them either.
- **Transport Security**: Ensure that communication with secret backends (like Vault or AWS) is encrypted using TLS.
- **Access Control**: Use the principle of least privilege when setting up access to secret backends.

## Development

### Adding a New Provider

To add a new provider:

1. Create a new file in the `secrets` directory (e.g., `mybackend.py`).
2. Implement a class that inherits from `SecretManager` and implements all required methods.
3. Update the `__init__.py` file to import and register the new provider.

Example:

```python
from .base import SecretManager

class MyBackendSecretManager(SecretManager):
    def __init__(self, config_param=None):
        self.config_param = config_param
        self._cache = {}
        
    def get_secret(self, key, default=None):
        # Implementation
        
    def get_secrets(self, keys):
        # Implementation
        
    def has_secret(self, key):
        # Implementation
```

Then update `__init__.py`:

```python
try:
    from .mybackend import MyBackendSecretManager
    HAS_MYBACKEND = True
except ImportError:
    HAS_MYBACKEND = False

def get_secret_manager(manager_type=None):
    # ...
    elif manager_type == 'mybackend' and HAS_MYBACKEND:
        return MyBackendSecretManager()
    # ...
``` 