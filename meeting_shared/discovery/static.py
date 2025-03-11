"""
Static service discovery provider.
Uses a static configuration for service discovery.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, List
import time

logger = logging.getLogger(__name__)

class StaticServiceDiscovery:
    """
    Static service discovery provider.
    Uses a static configuration for service discovery.
    """
    
    def __init__(self):
        """Initialize static service discovery."""
        self.services = {}
        self.health_check_interval = int(os.environ.get('SERVICE_HEALTH_CHECK_INTERVAL', '60'))
        self.health_check_timeout = int(os.environ.get('SERVICE_HEALTH_CHECK_TIMEOUT', '5'))
        self.last_health_check = {}
        
        # Load services from environment variables
        self._load_services_from_env()
        
        logger.info(f"Initialized static service discovery with {len(self.services)} services")
    
    def _load_services_from_env(self):
        """Load services from environment variables."""
        # Look for environment variables in the format SERVICE_NAME_URL
        for key, value in os.environ.items():
            if key.endswith('_URL') and not key.startswith('DATABASE') and not key.startswith('REDIS'):
                service_name = key[:-4].lower().replace('_', '-')
                self.register_service(service_name, value)
    
    def get_service(self, service_name: str, default: Any = None) -> Optional[Dict[str, Any]]:
        """
        Get service details by name.
        
        Args:
            service_name: The service name to look up
            default: Default value if service not found
            
        Returns:
            Service details or default if not found
        """
        service = self.services.get(service_name)
        if not service:
            return default
        
        # Check if we need to perform a health check
        current_time = time.time()
        last_check = self.last_health_check.get(service_name, 0)
        
        if current_time - last_check > self.health_check_interval:
            self._check_service_health(service_name, service)
            self.last_health_check[service_name] = current_time
        
        return service
    
    def get_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered services.
        
        Returns:
            Dictionary of service name to service details
        """
        return self.services
    
    def register_service(self, name: str, url: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a service.
        
        Args:
            name: Service name
            url: Service URL
            metadata: Optional service metadata
        """
        if not metadata:
            metadata = {}
        
        # Add health check URL if not provided
        if 'health_check_url' not in metadata:
            # Default health check URL is service URL + /health
            if url.endswith('/'):
                health_url = f"{url}health"
            else:
                health_url = f"{url}/health"
            metadata['health_check_url'] = health_url
        
        self.services[name] = {
            'name': name,
            'url': url,
            'metadata': metadata,
            'status': 'unknown'
        }
        
        logger.info(f"Registered service: {name} at {url}")
    
    def _check_service_health(self, service_name: str, service: Dict[str, Any]) -> None:
        """
        Check the health of a service.
        
        Args:
            service_name: Service name
            service: Service details
        """
        health_url = service.get('metadata', {}).get('health_check_url')
        if not health_url:
            logger.warning(f"No health check URL for service: {service_name}")
            return
        
        try:
            response = requests.get(health_url, timeout=self.health_check_timeout)
            
            if response.status_code == 200:
                service['status'] = 'healthy'
                logger.debug(f"Service {service_name} is healthy")
            else:
                service['status'] = 'unhealthy'
                logger.warning(f"Service {service_name} health check failed with status: {response.status_code}")
                
            # Store the last health check response
            service['last_health_check'] = {
                'timestamp': time.time(),
                'status_code': response.status_code,
                'response': response.text[:200]  # Store first 200 chars of response
            }
            
        except requests.RequestException as e:
            service['status'] = 'unavailable'
            logger.error(f"Health check failed for service {service_name}: {str(e)}")
            
            # Store the error
            service['last_health_check'] = {
                'timestamp': time.time(),
                'error': str(e)
            } 