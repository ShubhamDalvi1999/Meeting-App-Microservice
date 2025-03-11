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
        """Initialize the Vault client and authenticate."""
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
                raise ValueError(f"Unsupported auth method: {self.auth_method}")
                
            if not self.client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")
                
            logger.info(f"Successfully authenticated with Vault at {self.url}")
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {str(e)}")
            raise
    
    def _get_path(self, key):
        """
        Get the full path for a secret key.
        
        Args:
            key: The secret key.
            
        Returns:
            The full path in Vault.
        """
        return f"{self.path_prefix}{key}"
    
    def get_secret(self, key, default=None):
        """
        Get a secret from Vault.
        
        Args:
            key: The secret key.
            default: The default value to return if the secret is not found.
            
        Returns:
            The secret value, or default if not found.
        """
        try:
            path = self._get_path(key)
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            
            if secret and 'data' in secret['data']:
                return secret['data']['data'].get('value', default)
            
            return default
        except Exception as e:
            logger.error(f"Error retrieving secret from Vault: {str(e)}")
            return default
    
    def get_secrets(self, keys):
        """
        Get multiple secrets from Vault.
        
        Args:
            keys: List of secret keys.
            
        Returns:
            Dictionary of key-value pairs.
        """
        return {key: self.get_secret(key) for key in keys}
    
    def has_secret(self, key):
        """
        Check if a secret exists in Vault.
        
        Args:
            key: The secret key.
            
        Returns:
            True if the secret exists, False otherwise.
        """
        try:
            path = self._get_path(key)
            self.client.secrets.kv.v2.read_secret_version(path=path)
            return True
        except Exception:
            return False 