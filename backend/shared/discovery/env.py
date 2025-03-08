"""
Environment variable-based service discovery.
Retrieves service information from environment variables.
"""

import os
import logging
from .base import ServiceDiscovery

logger = logging.getLogger(__name__)

class EnvServiceDiscovery(ServiceDiscovery):
    """
    Service discovery that retrieves service information from environment variables.
    This is the simplest implementation and the default fallback.
    
    Environment variables should be in the format:
    - SERVICE_<NAME>_URL for the URL
    - SERVICE_<NAME>_HOST and SERVICE_<NAME>_PORT for host/port
    
    For example:
    - SERVICE_AUTH_URL=http://auth-service:5001
    - SERVICE_BACKEND_HOST=backend
    - SERVICE_BACKEND_PORT=5000
    """
    
    def __init__(self, prefix='SERVICE'):
        """
        Initialize environment variable service discovery.
        
        Args:
            prefix: Prefix for environment variables (default: 'SERVICE')
        """
        self.prefix = prefix
        self.services_cache = None
    
    def get_service_url(self, service_name, default=None):
        """
        Get the URL for a service from environment variables.
        
        Args:
            service_name: The service name to look up
            default: Default URL if service not found
            
        Returns:
            The service URL, or default if not found
        """
        # Normalize service name
        normalized_name = self._normalize_service_name(service_name)
        
        # Try direct URL environment variable first
        url_key = f"{self.prefix}_{normalized_name.upper()}_URL"
        url = os.environ.get(url_key)
        
        if url:
            logger.debug(f"Found service URL for {service_name} in environment variable {url_key}")
            return url
        
        # Try host/port combination
        host_key = f"{self.prefix}_{normalized_name.upper()}_HOST"
        port_key = f"{self.prefix}_{normalized_name.upper()}_PORT"
        
        host = os.environ.get(host_key)
        port = os.environ.get(port_key)
        
        if host and port:
            logger.debug(f"Found service host/port for {service_name} in environment variables {host_key}/{port_key}")
            protocol = 'https' if port == '443' else 'http'
            return f"{protocol}://{host}:{port}"
        
        # Try special case for common services
        if normalized_name == 'auth':
            if 'AUTH_SERVICE_URL' in os.environ:
                logger.debug(f"Using AUTH_SERVICE_URL for {service_name}")
                return os.environ['AUTH_SERVICE_URL']
        elif normalized_name == 'backend':
            if 'BACKEND_URL' in os.environ:
                logger.debug(f"Using BACKEND_URL for {service_name}")
                return os.environ['BACKEND_URL']
        elif normalized_name == 'websocket':
            if 'WEBSOCKET_URL' in os.environ:
                logger.debug(f"Using WEBSOCKET_URL for {service_name}")
                return os.environ['WEBSOCKET_URL']
        
        logger.debug(f"Service URL for {service_name} not found in environment variables")
        return default
    
    def get_service(self, service_name, default=None):
        """
        Get detailed information for a service from environment variables.
        
        Args:
            service_name: The service name to look up
            default: Default value if service not found
            
        Returns:
            Dictionary with service details, or default if not found
        """
        # Refresh services cache
        services = self.get_services()
        
        # Normalize service name
        normalized_name = self._normalize_service_name(service_name)
        
        # Return service details or default
        return services.get(normalized_name, default)
    
    def get_services(self):
        """
        Get all available services from environment variables.
        
        Returns:
            Dictionary of service name to service details
        """
        # Return cached result if available
        if self.services_cache is not None:
            return self.services_cache
        
        services = {}
        
        # Scan environment variables for service information
        for key, value in os.environ.items():
            if not key.startswith(f"{self.prefix}_"):
                continue
            
            # Extract service name from environment variable
            parts = key.split('_')
            if len(parts) < 3:
                continue
            
            # SERVICE_NAME_URL or SERVICE_NAME_HOST or SERVICE_NAME_PORT
            service_name = parts[1].lower()
            attribute = parts[2].lower()
            
            # Initialize service if not already in services
            if service_name not in services:
                services[service_name] = {'name': service_name}
            
            # Add attribute to service
            if attribute == 'url':
                services[service_name]['url'] = value
            elif attribute == 'host':
                services[service_name]['host'] = value
            elif attribute == 'port':
                services[service_name]['port'] = value
        
        # Add special case services
        special_cases = {
            'auth': 'AUTH_SERVICE_URL',
            'backend': 'BACKEND_URL',
            'websocket': 'WEBSOCKET_URL'
        }
        
        for name, env_var in special_cases.items():
            if env_var in os.environ and name not in services:
                services[name] = {
                    'name': name,
                    'url': os.environ[env_var]
                }
        
        # Derive URLs for services with host and port but no URL
        for name, service in services.items():
            if 'url' not in service and 'host' in service and 'port' in service:
                protocol = 'https' if service['port'] == '443' else 'http'
                service['url'] = f"{protocol}://{service['host']}:{service['port']}"
        
        # Cache for future use
        self.services_cache = services
        
        logger.debug(f"Found {len(services)} services in environment variables")
        return services
    
    def register_service(self, service_name, service_data):
        """
        Register a service with the environment variables.
        Note: This is a no-op for environment variables as they can't be modified at runtime.
        
        Args:
            service_name: The service name to register
            service_data: Service details (URL, health check, etc.)
            
        Returns:
            False (not supported)
        """
        logger.warning("Service registration not supported with environment variable discovery")
        return False
    
    def deregister_service(self, service_name):
        """
        Deregister a service from the environment variables.
        Note: This is a no-op for environment variables as they can't be modified at runtime.
        
        Args:
            service_name: The service name to deregister
            
        Returns:
            False (not supported)
        """
        logger.warning("Service deregistration not supported with environment variable discovery")
        return False 