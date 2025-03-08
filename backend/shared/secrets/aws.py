"""
AWS Secrets Manager secret manager.
Retrieves secrets from AWS Secrets Manager.
"""

import os
import json
import logging
from .base import SecretManager

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

logger = logging.getLogger(__name__)

class AWSSecretManager(SecretManager):
    """
    Secret manager that retrieves secrets from AWS Secrets Manager.
    Requires the boto3 package to be installed.
    """
    
    def __init__(self, 
                 region_name=None, 
                 prefix=None,
                 aws_access_key_id=None,
                 aws_secret_access_key=None,
                 profile_name=None):
        """
        Initialize AWS Secrets Manager secret manager.
        
        Args:
            region_name: AWS region name (defaults to AWS_REGION env var)
            prefix: Optional prefix for secret names
            aws_access_key_id: AWS access key ID (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret access key (defaults to AWS_SECRET_ACCESS_KEY env var)
            profile_name: AWS profile name (defaults to AWS_PROFILE env var)
        """
        if not HAS_BOTO3:
            raise ImportError("boto3 package is required for AWSSecretManager")
        
        self.region_name = region_name or os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION')
        if not self.region_name:
            raise ValueError("AWS region not provided and AWS_REGION environment variable not set")
        
        self.prefix = prefix
        self.aws_access_key_id = aws_access_key_id or os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = aws_secret_access_key or os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.profile_name = profile_name or os.environ.get('AWS_PROFILE')
        
        self.client = None
        self.cache = {}
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS Secrets Manager client."""
        try:
            kwargs = {'region_name': self.region_name}
            
            if self.aws_access_key_id and self.aws_secret_access_key:
                kwargs['aws_access_key_id'] = self.aws_access_key_id
                kwargs['aws_secret_access_key'] = self.aws_secret_access_key
            
            if self.profile_name:
                kwargs['profile_name'] = self.profile_name
            
            self.client = boto3.client('secretsmanager', **kwargs)
            logger.info(f"Successfully initialized AWS Secrets Manager client in region {self.region_name}")
        except Exception as e:
            logger.error(f"Error initializing AWS Secrets Manager client: {str(e)}")
            raise
    
    def get_secret(self, key, default=None):
        """
        Get a secret from AWS Secrets Manager.
        
        Args:
            key: The secret key to retrieve
            default: Default value if secret not found
            
        Returns:
            The secret value, or default if not found
        """
        if not self.client:
            logger.error("AWS Secrets Manager client not initialized")
            return default
        
        # Check cache first
        if key in self.cache:
            logger.debug(f"Retrieved secret {self._format_key(key)} from cache")
            return self.cache[key]
        
        # Construct secret name with prefix
        secret_name = key
        if self.prefix:
            secret_name = f"{self.prefix}/{key}"
        
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Extract the secret value
            if 'SecretString' in response:
                secret_value = response['SecretString']
                
                # Try to parse as JSON
                try:
                    secret_json = json.loads(secret_value)
                    
                    # If this is a JSON document with a key that matches our key name,
                    # return just that value; otherwise return the whole document
                    if isinstance(secret_json, dict):
                        # If the key name is just the last part of the path, extract it
                        key_parts = key.split('/')
                        short_key = key_parts[-1]
                        
                        if short_key in secret_json:
                            self.cache[key] = secret_json[short_key]
                            logger.debug(f"Retrieved secret {self._format_key(key)} from AWS Secrets Manager (JSON field)")
                            return secret_json[short_key]
                    
                    # Otherwise return the whole JSON document
                    self.cache[key] = secret_json
                    logger.debug(f"Retrieved secret {self._format_key(key)} from AWS Secrets Manager (JSON)")
                    return secret_json
                except json.JSONDecodeError:
                    # Not JSON, return as string
                    self.cache[key] = secret_value
                    logger.debug(f"Retrieved secret {self._format_key(key)} from AWS Secrets Manager (string)")
                    return secret_value
            
            elif 'SecretBinary' in response:
                # Binary secrets are less common but supported
                import base64
                binary_data = response['SecretBinary']
                self.cache[key] = binary_data
                logger.debug(f"Retrieved secret {self._format_key(key)} from AWS Secrets Manager (binary)")
                return binary_data
            
            logger.error(f"Unknown secret format for {self._format_key(key)}")
            return default
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'ResourceNotFoundException':
                logger.debug(f"Secret {self._format_key(key)} not found in AWS Secrets Manager")
                return default
            else:
                logger.error(f"Error retrieving secret {self._format_key(key)} from AWS Secrets Manager: {str(e)}")
                return default
        except Exception as e:
            logger.error(f"Error retrieving secret {self._format_key(key)} from AWS Secrets Manager: {str(e)}")
            return default
    
    def get_secrets(self, keys):
        """
        Get multiple secrets from AWS Secrets Manager.
        
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
        Check if a secret exists in AWS Secrets Manager.
        
        Args:
            key: The secret key to check
            
        Returns:
            True if the secret exists, False otherwise
        """
        if key in self.cache:
            return True
        
        secret_name = key
        if self.prefix:
            secret_name = f"{self.prefix}/{key}"
        
        try:
            self.client.describe_secret(SecretId=secret_name)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'ResourceNotFoundException':
                return False
            else:
                logger.error(f"Error checking secret {self._format_key(key)}: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Error checking secret {self._format_key(key)}: {str(e)}")
            return False 