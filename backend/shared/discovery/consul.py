"""
Consul service discovery.
Retrieves service information from HashiCorp Consul.
"""

import os
import logging
from .base import ServiceDiscovery

try:
    import consul
    HAS_CONSUL = True
except ImportError:
    HAS_CONSUL = False

logger = logging.getLogger(__name__)

class ConsulServiceDiscovery(ServiceDiscovery):
    """
    Service discovery that retrieves service information from HashiCorp Consul.
    Requires the python-consul package to be installed.
    """
    
    def __init__(self, host='localhost', port=8500, token=None, scheme='http'):
        """
        Initialize Consul service discovery.
        
        Args:
            host: Consul host (default: 'localhost')
            port: Consul port (default: 8500)
            token: Consul ACL token (optional)
            scheme: HTTP scheme (default: 'http')
        """
        if not HAS_CONSUL:
            raise ImportError("python-consul package is required for ConsulServiceDiscovery")
        
        self.host = host
        self.port = port
        self.token = token
        self.scheme = scheme
        
        self.client = consul.Consul(
            host=self.host,
            port=self.port,
            token=self.token,
            scheme=self.scheme
        )
        
        logger.info(f"Initialized Consul service discovery at {self.scheme}://{self.host}:{self.port}")
    
    def get_service_url(self, service_name, default=None):
        """
        Get the URL for a service from Consul.
        
        Args:
            service_name: The service name to look up
            default: Default URL if service not found
            
        Returns:
            The service URL, or default if not found
        """
        try:
            normalized_name = self._normalize_service_name(service_name)
            
            # Get service from Consul
            _, services = self.client.catalog.service(normalized_name)
            
            if not services:
                logger.debug(f"Service {service_name} not found in Consul")
                return default
            
            # Get the first service instance
            service = services[0]
            
            # Construct URL
            service_address = service.get('ServiceAddress') or service.get('Address')
            service_port = service.get('ServicePort')
            
            if not service_address or not service_port:
                logger.warning(f"Service {service_name} found in Consul but has no address or port")
                return default
            
            # Check for protocol tag
            tags = service.get('ServiceTags', [])
            protocol = 'https' if 'https' in tags else 'http'
            
            url = f"{protocol}://{service_address}:{service_port}"
            logger.debug(f"Found service URL for {service_name} in Consul: {url}")
            return url
        except Exception as e:
            logger.error(f"Error getting service URL from Consul: {str(e)}")
            return default
    
    def get_service(self, service_name, default=None):
        """
        Get detailed information for a service from Consul.
        
        Args:
            service_name: The service name to look up
            default: Default value if service not found
            
        Returns:
            Dictionary with service details, or default if not found
        """
        try:
            normalized_name = self._normalize_service_name(service_name)
            
            # Get service from Consul
            _, services = self.client.catalog.service(normalized_name)
            
            if not services:
                logger.debug(f"Service {service_name} not found in Consul")
                return default
            
            # Get the first service instance
            consul_service = services[0]
            
            # Format service information
            service_info = {
                'name': normalized_name,
                'id': consul_service.get('ServiceID'),
                'address': consul_service.get('ServiceAddress') or consul_service.get('Address'),
                'port': consul_service.get('ServicePort'),
                'tags': consul_service.get('ServiceTags', []),
                'meta': consul_service.get('ServiceMeta', {}),
                'node': consul_service.get('Node'),
                'datacenter': consul_service.get('Datacenter')
            }
            
            # Check for protocol tag
            tags = consul_service.get('ServiceTags', [])
            protocol = 'https' if 'https' in tags else 'http'
            
            # Construct URL
            if service_info['address'] and service_info['port']:
                service_info['url'] = f"{protocol}://{service_info['address']}:{service_info['port']}"
            
            logger.debug(f"Found service {service_name} in Consul")
            return service_info
        except Exception as e:
            logger.error(f"Error getting service from Consul: {str(e)}")
            return default
    
    def get_services(self):
        """
        Get all available services from Consul.
        
        Returns:
            Dictionary of service name to service details
        """
        try:
            # Get all services from Consul
            _, consul_services = self.client.catalog.services()
            
            services = {}
            
            # Get details for each service
            for service_name in consul_services:
                service_info = self.get_service(service_name)
                if service_info:
                    normalized_name = self._normalize_service_name(service_name)
                    services[normalized_name] = service_info
            
            logger.debug(f"Found {len(services)} services in Consul")
            return services
        except Exception as e:
            logger.error(f"Error getting services from Consul: {str(e)}")
            return {}
    
    def register_service(self, service_name, service_data):
        """
        Register a service with Consul.
        
        Args:
            service_name: The service name to register
            service_data: Service details (address, port, tags, etc.)
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            normalized_name = self._normalize_service_name(service_name)
            
            # Extract service information
            service_id = service_data.get('id', normalized_name)
            address = service_data.get('address', 'localhost')
            port = service_data.get('port', 80)
            tags = service_data.get('tags', [])
            
            # Extract health check information
            check = None
            if 'check' in service_data:
                check = service_data['check']
            elif 'url' in service_data:
                # Default HTTP check
                check = {
                    'http': service_data['url'] + '/health',
                    'interval': '10s',
                    'timeout': '5s'
                }
            
            # Register service
            result = self.client.agent.service.register(
                name=normalized_name,
                service_id=service_id,
                address=address,
                port=port,
                tags=tags,
                check=check
            )
            
            logger.info(f"Registered service {service_name} with Consul")
            return True
        except Exception as e:
            logger.error(f"Error registering service with Consul: {str(e)}")
            return False
    
    def deregister_service(self, service_name):
        """
        Deregister a service from Consul.
        
        Args:
            service_name: The service name to deregister
            
        Returns:
            True if deregistration was successful, False otherwise
        """
        try:
            normalized_name = self._normalize_service_name(service_name)
            
            # Get service ID (could be different from name)
            service_info = self.get_service(normalized_name)
            if not service_info:
                logger.warning(f"Service {service_name} not found in Consul")
                return False
            
            service_id = service_info.get('id', normalized_name)
            
            # Deregister service
            result = self.client.agent.service.deregister(service_id)
            
            logger.info(f"Deregistered service {service_name} from Consul")
            return True
        except Exception as e:
            logger.error(f"Error deregistering service from Consul: {str(e)}")
            return False 