"""
File-based secret manager.
Retrieves secrets from files in a directory.
"""

import os
import json
import logging
from pathlib import Path
from .base import SecretManager

logger = logging.getLogger(__name__)

class FileSecretManager(SecretManager):
    """
    Secret manager that retrieves secrets from files.
    
    This is useful for Docker and Kubernetes environments that mount secrets as files.
    """
    
    def __init__(self, path='/app/secrets'):
        """
        Initialize the file-based secret manager.
        
        Args:
            path: Path to the secrets directory (default: '/app/secrets').
                 Can be a directory containing individual secret files,
                 or a JSON file containing multiple secrets.
        """
        self.path = Path(path)
        self._cache = {}
        self._is_json_file = self.path.is_file() and self.path.suffix.lower() == '.json'
        
        if self._is_json_file:
            logger.info(f"Initialized file-based secret manager with JSON file: {self.path}")
            self._load_json_file()
        else:
            logger.info(f"Initialized file-based secret manager with directory: {self.path}")
    
    def _load_json_file(self):
        """
        Load secrets from a JSON file.
        """
        try:
            if not self.path.exists():
                logger.warning(f"Secrets file does not exist: {self.path}")
                return
            
            with open(self.path, 'r') as f:
                self._cache = json.load(f)
            
            logger.debug(f"Loaded {len(self._cache)} secrets from JSON file")
        except Exception as e:
            logger.error(f"Error loading secrets from JSON file: {str(e)}")
    
    def _get_file_path(self, key):
        """
        Get the file path for a secret key.
        
        Args:
            key: The secret key.
            
        Returns:
            The file path.
        """
        # Replace dots with slashes
        key_path = key.replace('.', '/')
        
        # Ensure the key doesn't start with a slash
        if key_path.startswith('/'):
            key_path = key_path[1:]
        
        return self.path / key_path
    
    def get_secret(self, key, default=None):
        """
        Get a secret from a file.
        
        Args:
            key: The secret key.
            default: The default value to return if the secret is not found.
            
        Returns:
            The secret value, or default if not found.
        """
        if self._is_json_file:
            # For JSON files, use the cache
            value = self._cache.get(key)
            if value is None:
                logger.debug(f"Secret not found in JSON file: {key}")
                return default
            
            logger.debug(f"Retrieved secret from JSON file: {key}")
            return value
        else:
            # For directories, read the file
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                logger.debug(f"Secret file does not exist: {file_path}")
                return default
            
            try:
                with open(file_path, 'r') as f:
                    value = f.read().strip()
                
                logger.debug(f"Retrieved secret from file: {file_path}")
                return value
            except Exception as e:
                logger.error(f"Error reading secret file: {str(e)}")
                return default
    
    def get_secrets(self, keys):
        """
        Get multiple secrets.
        
        Args:
            keys: List of secret keys.
            
        Returns:
            Dictionary of key-value pairs.
        """
        return {key: self.get_secret(key) for key in keys}
    
    def has_secret(self, key):
        """
        Check if a secret exists.
        
        Args:
            key: The secret key.
            
        Returns:
            True if the secret exists, False otherwise.
        """
        if self._is_json_file:
            return key in self._cache
        else:
            return self._get_file_path(key).exists() 