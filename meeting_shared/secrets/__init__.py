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
    
    if manager_type == 'env' and HAS_ENV:
        return EnvSecretManager()
    elif manager_type == 'file' and HAS_FILE:
        return FileSecretManager()
    elif manager_type == 'vault' and HAS_VAULT:
        return VaultSecretManager()
    elif manager_type == 'aws' and HAS_AWS:
        return AWSSecretManager()
    else:
        logger.warning(f"Unsupported or unavailable secret manager: {manager_type}")
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

# Export public interface
__all__ = [
    'get_secret',
    'get_secrets',
    'has_secret',
    'set_secret_manager',
    'get_secret_manager'
] 