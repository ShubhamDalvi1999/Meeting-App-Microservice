"""
Environment variable secret manager.
Retrieves secrets from environment variables.
"""

import os
import logging
from .base import SecretManager

logger = logging.getLogger(__name__)

class EnvSecretManager(SecretManager):
    """
    Secret manager that retrieves secrets from environment variables.
    
    This is the simplest secret manager and serves as a fallback.
    """
    
    def __init__(self, prefix=''):
        """
        Initialize the environment variable secret manager.
        
        Args:
            prefix: Prefix for environment variables (default: '').
                   For example, if prefix is 'SECRET_', then the secret
                   'database/password' would be retrieved from the
                   environment variable 'SECRET_DATABASE_PASSWORD'.
        """
        self.prefix = prefix
        logger.info(f"Initialized environment variable secret manager with prefix '{prefix}'")
    
    def _format_key(self, key):
        """
        Format a key for use with environment variables.
        
        Args:
            key: The secret key.
            
        Returns:
            The formatted key.
        """
        # Replace slashes and dots with underscores
        formatted_key = key.replace('/', '_').replace('.', '_').replace('-', '_')
        
        # Convert to uppercase
        formatted_key = formatted_key.upper()
        
        # Add prefix
        if self.prefix:
            formatted_key = f"{self.prefix}{formatted_key}"
        
        return formatted_key
    
    def get_secret(self, key, default=None):
        """
        Get a secret from an environment variable.
        
        Args:
            key: The secret key.
            default: The default value to return if the secret is not found.
            
        Returns:
            The secret value, or default if not found.
        """
        env_key = self._format_key(key)
        value = os.environ.get(env_key)
        
        if value is None:
            logger.debug(f"Secret not found in environment variables: {env_key}")
            return default
        
        logger.debug(f"Retrieved secret from environment variables: {env_key}")
        return value
    
    def get_secrets(self, keys):
        """
        Get multiple secrets from environment variables.
        
        Args:
            keys: A list of secret keys.
            
        Returns:
            A dictionary of secret keys to values.
        """
        result = {}
        
        for key in keys:
            value = self.get_secret(key)
            if value is not None:
                result[key] = value
        
        return result
    
    def has_secret(self, key):
        """
        Check if a secret exists in environment variables.
        
        Args:
            key: The secret key.
            
        Returns:
            True if the secret exists, False otherwise.
        """
        env_key = self._format_key(key)
        return env_key in os.environ 