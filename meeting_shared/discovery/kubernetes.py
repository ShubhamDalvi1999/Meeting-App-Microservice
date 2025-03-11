"""
Kubernetes service discovery provider.
Uses the Kubernetes API for service discovery.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, List
import time
import json

logger = logging.getLogger(__name__)

class KubernetesServiceDiscovery:
    """
    Kubernetes service discovery provider.
    Uses the Kubernetes API for service discovery.
    """
    
    def __init__(self):
        """Initialize Kubernetes service discovery."""
        self.services = {}
        self.namespace = os.environ.get('KUBERNETES_NAMESPACE', 'default')
        self.health_check_interval = int(os.environ.get('SERVICE_HEALTH_CHECK_INTERVAL', '60'))
        self.health_check_timeout = int(os.environ.get('SERVICE_HEALTH_CHECK_TIMEOUT', '5'))
        self.last_health_check = {}
        
        # Kubernetes API details
        self.api_host = os.environ.get('KUBERNETES_SERVICE_HOST')
        self.api_port = os.environ.get('KUBERNETES_SERVICE_PORT')
        self.token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
        self.ca_cert_path = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
        
        # Check if we're running in Kubernetes
        if not self.api_host or not self.api_port:
            logger.warning("Not running in Kubernetes, or Kubernetes API environment variables not set")
            return
        
        # Load services from Kubernetes API
        self._load_services_from_kubernetes()
        
        logger.info(f"Initialized Kubernetes service discovery with {len(self.services)} services")
    
    def _load_services_from_kubernetes(self):
        """Load services from Kubernetes API."""
        try:
            # Read the service account token
            with open(self.token_path, 'r') as f:
                token = f.read().strip()
            
            # Build the API URL
            api_url = f"https://{self.api_host}:{self.api_port}/api/v1/namespaces/{self.namespace}/services"
            
            # Make the API request
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                api_url,
                headers=headers,
                verify=self.ca_cert_path,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get services from Kubernetes API: {response.status_code} {response.text}")
                return
            
            # Parse the response
            services_data = response.json()
            
            # Register each service
            for item in services_data.get('items', []):
                service_name = item.get('metadata', {}).get('name')
                if not service_name:
                    continue
                
                # Get service ports
                ports = item.get('spec', {}).get('ports', [])
                if not ports:
                    continue
                
                # Use the first port for the service URL
                port = ports[0].get('port')
                
                # Build the service URL
                service_url = f"http://{service_name}.{self.namespace}.svc.cluster.local:{port}"
                
                # Register the service
                self.register_service(service_name, service_url)
                
        except Exception as e:
            logger.error(f"Error loading services from Kubernetes: {str(e)}")
    
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