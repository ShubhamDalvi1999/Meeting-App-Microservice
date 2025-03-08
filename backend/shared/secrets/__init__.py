"""
Secrets management module.
Provides a unified interface for accessing secrets from various backends.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Import secret managers
try:
    from .env import EnvSecretManager
    HAS_ENV = True
except ImportError:
    HAS_ENV = False

try:
    from .file import FileSecretManager
    HAS_FILE = True
except ImportError:
    HAS_FILE = False

try:
    from .vault import VaultSecretManager
    HAS_VAULT = True
except ImportError:
    HAS_VAULT = False

try:
    from .aws import AWSSecretManager
    HAS_AWS = True
except ImportError:
    HAS_AWS = False

# Global secret manager instance
_secret_manager = None

def get_secret_manager(manager_type=None):
    """
    Get a secret manager instance.
    
    Args:
        manager_type: The type of secret manager to use.
            Options: 'env', 'file', 'vault', 'aws'
            If None, will try to determine from environment variables.
            
    Returns:
        A secret manager instance.
    """
    # Try to determine the manager type from environment variables
    if manager_type is None:
        manager_type = os.environ.get('SECRET_MANAGER_TYPE', 'env').lower()
    
    # Create the appropriate manager
    if manager_type == 'env' and HAS_ENV:
        prefix = os.environ.get('SECRET_MANAGER_PREFIX', '')
        return EnvSecretManager(prefix=prefix)
    elif manager_type == 'file' and HAS_FILE:
        path = os.environ.get('SECRET_MANAGER_PATH', '/app/secrets')
        return FileSecretManager(path=path)
    elif manager_type == 'vault' and HAS_VAULT:
        url = os.environ.get('VAULT_ADDR', 'http://localhost:8200')
        token = os.environ.get('VAULT_TOKEN')
        role_id = os.environ.get('VAULT_ROLE_ID')
        secret_id = os.environ.get('VAULT_SECRET_ID')
        
        if token:
            return VaultSecretManager(url=url, token=token)
        elif role_id and secret_id:
            return VaultSecretManager(url=url, role_id=role_id, secret_id=secret_id)
        else:
            logger.warning("Vault secret manager requested but no token or AppRole credentials provided")
            return None
    elif manager_type == 'aws' and HAS_AWS:
        region = os.environ.get('AWS_REGION')
        prefix = os.environ.get('AWS_SECRET_PREFIX', '')
        return AWSSecretManager(region_name=region, prefix=prefix)
    else:
        logger.warning(f"Unknown or unavailable secret manager type: {manager_type}, falling back to env")
        if HAS_ENV:
            return EnvSecretManager()
        else:
            logger.error("No secret manager available")
            return None

def _get_manager():
    """
    Get the global secret manager instance, creating it if necessary.
    
    Returns:
        The global secret manager instance.
    """
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = get_secret_manager()
    return _secret_manager

def set_secret_manager(manager):
    """
    Set the global secret manager instance.
    
    Args:
        manager: A secret manager instance.
    """
    global _secret_manager
    _secret_manager = manager

def get_secret(key, default=None):
    """
    Get a secret by key.
    
    Args:
        key: The secret key.
        default: The default value to return if the secret is not found.
        
    Returns:
        The secret value, or default if not found.
    """
    manager = _get_manager()
    if manager is None:
        logger.error(f"No secret manager available, cannot get secret: {key}")
        return default
    return manager.get_secret(key, default)

def get_secrets(keys):
    """
    Get multiple secrets by keys.
    
    Args:
        keys: A list of secret keys.
        
    Returns:
        A dictionary of secret keys to values.
    """
    manager = _get_manager()
    if manager is None:
        logger.error(f"No secret manager available, cannot get secrets: {keys}")
        return {}
    return manager.get_secrets(keys)

def has_secret(key):
    """
    Check if a secret exists.
    
    Args:
        key: The secret key.
        
    Returns:
        True if the secret exists, False otherwise.
    """
    manager = _get_manager()
    if manager is None:
        logger.error(f"No secret manager available, cannot check secret: {key}")
        return False
    return manager.has_secret(key) 