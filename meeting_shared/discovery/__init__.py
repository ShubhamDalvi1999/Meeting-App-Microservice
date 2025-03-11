"""
Service discovery module for backend services.
Provides abstractions for discovering and registering services.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import discovery providers
try:
    from .static import StaticServiceDiscovery
    HAS_STATIC = True
except ImportError:
    HAS_STATIC = False

try:
    from .kubernetes import KubernetesServiceDiscovery
    HAS_K8S = True
except ImportError:
    HAS_K8S = False

# Global discovery provider instance
_discovery_provider = None

def get_discovery_provider(provider_type=None):
    """
    Get a service discovery provider instance.
    
    Args:
        provider_type: The type of provider to use.
            Options: 'static', 'kubernetes'
            If None, will try to determine from environment variables.
            
    Returns:
        A service discovery provider instance.
    """
    # Try to determine the provider type from environment variables
    if provider_type is None:
        provider_type = os.environ.get('SERVICE_DISCOVERY_PROVIDER', 'env').lower()
    
    if provider_type == 'static' and HAS_STATIC:
        return StaticServiceDiscovery()
    elif provider_type == 'kubernetes' and HAS_K8S:
        return KubernetesServiceDiscovery()
    else:
        logger.warning(f"Unsupported or unavailable service discovery provider: {provider_type}")
        return None

def get_service_url(service_name, default=None):
    """
    Get the URL for a service by name.
    
    Args:
        service_name: The service name to look up
        default: Default URL if service not found
        
    Returns:
        Service URL or default if not found
    """
    global _discovery_provider
    
    if _discovery_provider is None:
        _discovery_provider = get_discovery_provider()
        
    if _discovery_provider is None:
        # Fallback to environment variables
        env_var = f"{service_name.upper()}_URL"
        return os.environ.get(env_var, default)
        
    service = _discovery_provider.get_service(service_name)
    if service:
        return service.get('url', default)
    return default

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

def register_service(name: str, url: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Register a service with the discovery provider.
    
    Args:
        name: Service name
        url: Service URL
        metadata: Optional service metadata
    """
    global _discovery_provider
    
    if _discovery_provider is None:
        _discovery_provider = get_discovery_provider()
        
    if _discovery_provider:
        _discovery_provider.register_service(name, url, metadata)
    else:
        logger.warning(f"No service discovery provider available, cannot register service: {name}")

def set_discovery_provider(provider):
    """
    Explicitly set the service discovery provider to use.
    
    Args:
        provider: An instance of a ServiceDiscovery class
    """
    global _discovery_provider
    _discovery_provider = provider
    logger.info(f"Service discovery provider explicitly set to {provider.__class__.__name__}")

# Export public interface
__all__ = [
    'get_service_url',
    'get_service',
    'get_services',
    'register_service',
    'set_discovery_provider',
    'get_discovery_provider'
] 