"""
Service discovery module for dynamically locating services.
Provides a unified interface for service discovery across different backends.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Import strategies (with fallback mechanism)
try:
    from .consul import ConsulServiceDiscovery
    HAS_CONSUL = True
except ImportError:
    logger.debug("Consul module not available")
    HAS_CONSUL = False

try:
    from .kubernetes import KubernetesServiceDiscovery
    HAS_K8S = True
except ImportError:
    logger.debug("Kubernetes module not available")
    HAS_K8S = False

from .static import StaticServiceDiscovery
from .env import EnvServiceDiscovery


def get_discovery_provider(provider_type=None):
    """
    Factory method to get the appropriate service discovery provider.
    
    Args:
        provider_type: Type of service discovery to use (consul, kubernetes, env, static)
                       If None, will try to determine from environment.
                       
    Returns:
        An instance of the appropriate service discovery class.
    """
    # If not specified, determine from environment
    if not provider_type:
        provider_type = os.environ.get('SERVICE_DISCOVERY', 'env').lower()
    
    if provider_type == 'consul' and HAS_CONSUL:
        logger.info("Using Consul for service discovery")
        consul_host = os.environ.get('CONSUL_HOST', 'localhost')
        consul_port = int(os.environ.get('CONSUL_PORT', '8500'))
        return ConsulServiceDiscovery(host=consul_host, port=consul_port)
    
    elif provider_type == 'kubernetes' and HAS_K8S:
        logger.info("Using Kubernetes for service discovery")
        namespace = os.environ.get('K8S_NAMESPACE', 'default')
        return KubernetesServiceDiscovery(namespace=namespace)
    
    elif provider_type == 'static':
        logger.info("Using static configuration for service discovery")
        config_file = os.environ.get('SERVICE_CONFIG', '/app/config/services.json')
        return StaticServiceDiscovery(config_file=config_file)
    
    # Default to environment variables
    logger.info("Using environment variables for service discovery")
    return EnvServiceDiscovery()


# Global service discovery instance
_discovery_provider = None

def get_service_url(service_name, default=None):
    """
    Get the URL for a service by name.
    
    Args:
        service_name: The service name to look up
        default: Default URL if service not found
        
    Returns:
        The service URL, or default if not found
    """
    global _discovery_provider
    
    if _discovery_provider is None:
        _discovery_provider = get_discovery_provider()
        
    return _discovery_provider.get_service_url(service_name, default)


def get_service(service_name, default=None):
    """
    Get detailed information for a service by name.
    
    Args:
        service_name: The service name to look up
        default: Default value if service not found
        
    Returns:
        Dictionary with service details, or default if not found
    """
    global _discovery_provider
    
    if _discovery_provider is None:
        _discovery_provider = get_discovery_provider()
        
    return _discovery_provider.get_service(service_name, default)


def get_services():
    """
    Get all available services.
    
    Returns:
        Dictionary of service name to service details
    """
    global _discovery_provider
    
    if _discovery_provider is None:
        _discovery_provider = get_discovery_provider()
        
    return _discovery_provider.get_services()


def register_service(service_name, service_data):
    """
    Register a service with the discovery system.
    
    Args:
        service_name: The service name to register
        service_data: Service details (URL, health check, etc.)
        
    Returns:
        True if registration was successful, False otherwise
    """
    global _discovery_provider
    
    if _discovery_provider is None:
        _discovery_provider = get_discovery_provider()
        
    return _discovery_provider.register_service(service_name, service_data)


def deregister_service(service_name):
    """
    Deregister a service from the discovery system.
    
    Args:
        service_name: The service name to deregister
        
    Returns:
        True if deregistration was successful, False otherwise
    """
    global _discovery_provider
    
    if _discovery_provider is None:
        _discovery_provider = get_discovery_provider()
        
    return _discovery_provider.deregister_service(service_name)


def set_discovery_provider(provider):
    """
    Explicitly set the service discovery provider to use.
    
    Args:
        provider: An instance of a ServiceDiscovery class
    """
    global _discovery_provider
    _discovery_provider = provider
    logger.info(f"Service discovery provider explicitly set to {provider.__class__.__name__}") 