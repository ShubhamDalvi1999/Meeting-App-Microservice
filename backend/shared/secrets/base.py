"""
Base class for secret managers.
Defines the interface that all secret managers must implement.
"""

from abc import ABC, abstractmethod


class SecretManager(ABC):
    """
    Abstract base class for secret managers.
    
    All secret managers must implement the methods defined in this class.
    """
    
    @abstractmethod
    def get_secret(self, key, default=None):
        """
        Get a secret by key.
        
        Args:
            key: The secret key.
            default: The default value to return if the secret is not found.
            
        Returns:
            The secret value, or default if not found.
        """
        pass
    
    @abstractmethod
    def get_secrets(self, keys):
        """
        Get multiple secrets by keys.
        
        Args:
            keys: A list of secret keys.
            
        Returns:
            A dictionary of secret keys to values.
        """
        pass
    
    @abstractmethod
    def has_secret(self, key):
        """
        Check if a secret exists.
        
        Args:
            key: The secret key.
            
        Returns:
            True if the secret exists, False otherwise.
        """
        pass
    
    def _sanitize_key(self, key):
        """
        Sanitize a secret key to match the backend's requirements.
        
        Args:
            key: The secret key to sanitize
            
        Returns:
            Sanitized key
        """
        # Default implementation just converts to uppercase
        # Subclasses can override this if needed
        return key.upper()
    
    def _format_key(self, key):
        """
        Format a secret key for display (e.g., for logging).
        Masks the actual key if it's sensitive.
        
        Args:
            key: The secret key to format
            
        Returns:
            Formatted key safe for display
        """
        key = str(key).lower()
        
        # List of partial key names that should be masked when displayed
        sensitive_keys = [
            'password', 'secret', 'key', 'token', 'credential', 
            'auth', 'access', 'private', 'cert', 'signature'
        ]
        
        if any(sensitive in key for sensitive in sensitive_keys):
            parts = key.split('_')
            
            # Keep the first part visible if it's not sensitive
            if not any(sensitive in parts[0].lower() for sensitive in sensitive_keys):
                return f"{parts[0]}_***"
            else:
                return "***"
        
        return key 