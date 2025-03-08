"""
HashiCorp Vault secret manager.
Retrieves secrets from HashiCorp Vault.
"""

import os
import logging
from .base import SecretManager

try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False

logger = logging.getLogger(__name__)

class VaultSecretManager(SecretManager):
    """
    Secret manager that retrieves secrets from HashiCorp Vault.
    Requires the hvac package to be installed.
    """
    
    def __init__(self, 
                 url=None, 
                 token=None, 
                 path_prefix='secret/',
                 auth_method='token',
                 role_id=None,
                 secret_id=None):
        """
        Initialize HashiCorp Vault secret manager.
        
        Args:
            url: Vault server URL (defaults to VAULT_ADDR env var)
            token: Vault token (defaults to VAULT_TOKEN env var)
            path_prefix: Path prefix for secrets (defaults to 'secret/')
            auth_method: Authentication method ('token', 'approle', etc.)
            role_id: AppRole role ID (for 'approle' auth method)
            secret_id: AppRole secret ID (for 'approle' auth method)
        """
        if not HAS_HVAC:
            raise ImportError("hvac package is required for VaultSecretManager")
        
        self.url = url or os.environ.get('VAULT_ADDR')
        if not self.url:
            raise ValueError("Vault URL not provided and VAULT_ADDR environment variable not set")
        
        self.token = token or os.environ.get('VAULT_TOKEN')
        self.path_prefix = path_prefix.rstrip('/') + '/'
        self.auth_method = auth_method
        self.role_id = role_id or os.environ.get('VAULT_ROLE_ID')
        self.secret_id = secret_id or os.environ.get('VAULT_SECRET_ID')
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Vault client and authenticate."""
        try:
            self.client = hvac.Client(url=self.url)
            
            if self.auth_method == 'token' and self.token:
                self.client.token = self.token
            elif self.auth_method == 'approle' and self.role_id and self.secret_id:
                self.client.auth.approle.login(
                    role_id=self.role_id,
                    secret_id=self.secret_id
                )
            else:
                raise ValueError(f"Unsupported auth method or missing credentials: {self.auth_method}")
            
            if not self.client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")
            
            logger.info(f"Successfully authenticated to Vault at {self.url}")
        except Exception as e:
            logger.error(f"Error initializing Vault client: {str(e)}")
            raise
    
    def get_secret(self, key, default=None):
        """
        Get a secret from Vault.
        
        Args:
            key: The secret key to retrieve
            default: Default value if secret not found
            
        Returns:
            The secret value, or default if not found
        """
        if not self.client or not self.client.is_authenticated():
            logger.error("Vault client not initialized or not authenticated")
            return default
        
        try:
            # Split key into path and key parts (e.g., 'database/password' -> 'database', 'password')
            parts = key.split('/')
            if len(parts) > 1:
                # Key includes a path
                path = '/'.join(parts[:-1])
                key_name = parts[-1]
                full_path = f"{self.path_prefix}{path}"
            else:
                # Key is just a name
                full_path = self.path_prefix.rstrip('/')
                key_name = key
            
            # Read from Vault
            response = self.client.secrets.kv.v2.read_secret_version(
                path=full_path,
                mount_point='secret'
            )
            
            # Extract the value
            if response and 'data' in response and 'data' in response['data']:
                data = response['data']['data']
                if key_name in data:
                    logger.debug(f"Retrieved secret {self._format_key(key)} from Vault")
                    return data[key_name]
            
            logger.debug(f"Secret {self._format_key(key)} not found in Vault")
            return default
        except Exception as e:
            logger.error(f"Error retrieving secret {self._format_key(key)} from Vault: {str(e)}")
            return default
    
    def get_secrets(self, keys):
        """
        Get multiple secrets from Vault.
        
        Args:
            keys: List of secret keys to retrieve
            
        Returns:
            Dictionary of key-value pairs for found secrets
        """
        result = {}
        for key in keys:
            value = self.get_secret(key)
            if value is not None:
                result[key] = value
        
        return result
    
    def has_secret(self, key):
        """
        Check if a secret exists in Vault.
        
        Args:
            key: The secret key to check
            
        Returns:
            True if the secret exists, False otherwise
        """
        return self.get_secret(key) is not None 