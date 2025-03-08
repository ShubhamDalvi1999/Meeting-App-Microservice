"""
Base class for service discovery.
Defines the interface that all service discovery implementations must follow.
"""

from abc import ABC, abstractmethod


class ServiceDiscovery(ABC):
    """
    Abstract base class for service discovery.
    All service discovery implementations must extend this class.
    """
    
    @abstractmethod
    def get_service_url(self, service_name, default=None):
        """
        Get the URL for a service by name.
        
        Args:
            service_name: The service name to look up
            default: Default URL if service not found
            
        Returns:
            The service URL, or default if not found
        """
        pass
    
    @abstractmethod
    def get_service(self, service_name, default=None):
        """
        Get detailed information for a service by name.
        
        Args:
            service_name: The service name to look up
            default: Default value if service not found
            
        Returns:
            Dictionary with service details, or default if not found
        """
        pass
    
    @abstractmethod
    def get_services(self):
        """
        Get all available services.
        
        Returns:
            Dictionary of service name to service details
        """
        pass
    
    @abstractmethod
    def register_service(self, service_name, service_data):
        """
        Register a service with the discovery system.
        
        Args:
            service_name: The service name to register
            service_data: Service details (URL, health check, etc.)
            
        Returns:
            True if registration was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def deregister_service(self, service_name):
        """
        Deregister a service from the discovery system.
        
        Args:
            service_name: The service name to deregister
            
        Returns:
            True if deregistration was successful, False otherwise
        """
        pass
    
    def _normalize_service_name(self, service_name):
        """
        Normalize a service name to match the discovery system's requirements.
        
        Args:
            service_name: The service name to normalize
            
        Returns:
            Normalized service name
        """
        # Default implementation just converts to lowercase and replaces spaces with hyphens
        # Subclasses can override this if needed
        return service_name.lower().replace(' ', '-').replace('_', '-') 