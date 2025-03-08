"""
Static file-based service discovery.
Retrieves service information from a static JSON or YAML configuration file.
"""

import os
import json
import logging
from pathlib import Path
from .base import ServiceDiscovery

logger = logging.getLogger(__name__)

class StaticServiceDiscovery(ServiceDiscovery):
    """
    Service discovery that retrieves service information from a static configuration file.
    This is useful for development and testing environments, or when using Docker Compose.
    """
    
    def __init__(self, config_file='/app/config/services.json'):
        """
        Initialize static file service discovery.
        
        Args:
            config_file: Path to the configuration file (JSON or YAML)
        """
        self.config_file = Path(config_file)
        self.services = {}
        self.last_loaded = 0
        self._load_config()
    
    def get_service_url(self, service_name, default=None):
        """
        Get the URL for a service from the static configuration.
        
        Args:
            service_name: The service name to look up
            default: Default URL if service not found
            
        Returns:
            The service URL, or default if not found
        """
        self._maybe_reload()
        
        normalized_name = self._normalize_service_name(service_name)
        
        if normalized_name in self.services:
            service = self.services[normalized_name]
            
            # Return URL if available
            if 'url' in service:
                logger.debug(f"Found service URL for {service_name} in configuration")
                return service['url']
            
            # Construct URL from host and port if available
            if 'host' in service and 'port' in service:
                protocol = service.get('protocol', 'http')
                url = f"{protocol}://{service['host']}:{service['port']}"
                logger.debug(f"Constructed service URL for {service_name} from host/port")
                return url
        
        logger.debug(f"Service URL for {service_name} not found in configuration")
        return default
    
    def get_service(self, service_name, default=None):
        """
        Get detailed information for a service from the static configuration.
        
        Args:
            service_name: The service name to look up
            default: Default value if service not found
            
        Returns:
            Dictionary with service details, or default if not found
        """
        self._maybe_reload()
        
        normalized_name = self._normalize_service_name(service_name)
        return self.services.get(normalized_name, default)
    
    def get_services(self):
        """
        Get all available services from the static configuration.
        
        Returns:
            Dictionary of service name to service details
        """
        self._maybe_reload()
        return self.services
    
    def register_service(self, service_name, service_data):
        """
        Register a service in the static configuration.
        This updates the in-memory representation and writes to the configuration file.
        
        Args:
            service_name: The service name to register
            service_data: Service details (URL, health check, etc.)
            
        Returns:
            True if registration was successful, False otherwise
        """
        normalized_name = self._normalize_service_name(service_name)
        
        # Update in-memory representation
        self.services[normalized_name] = service_data
        
        # Write to file
        try:
            self._write_config()
            logger.info(f"Registered service {service_name} in configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {str(e)}")
            return False
    
    def deregister_service(self, service_name):
        """
        Deregister a service from the static configuration.
        This updates the in-memory representation and writes to the configuration file.
        
        Args:
            service_name: The service name to deregister
            
        Returns:
            True if deregistration was successful, False otherwise
        """
        normalized_name = self._normalize_service_name(service_name)
        
        # Check if service exists
        if normalized_name not in self.services:
            logger.warning(f"Service {service_name} not found in configuration")
            return False
        
        # Remove from in-memory representation
        del self.services[normalized_name]
        
        # Write to file
        try:
            self._write_config()
            logger.info(f"Deregistered service {service_name} from configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service {service_name}: {str(e)}")
            return False
    
    def _load_config(self):
        """Load services from the configuration file."""
        if not self.config_file.exists():
            logger.warning(f"Configuration file {self.config_file} does not exist")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.suffix.lower() == '.json':
                    self.services = json.load(f)
                elif self.config_file.suffix.lower() in ['.yaml', '.yml']:
                    try:
                        import yaml
                        self.services = yaml.safe_load(f)
                    except ImportError:
                        logger.error("YAML support requires PyYAML. Please install it with pip install PyYAML")
                        raise
                else:
                    logger.error(f"Unsupported configuration file format: {self.config_file.suffix}")
                    return
            
            self.last_loaded = self.config_file.stat().st_mtime
            logger.info(f"Loaded {len(self.services)} services from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration file {self.config_file}: {str(e)}")
    
    def _write_config(self):
        """Write services to the configuration file."""
        try:
            # Create parent directories if they don't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                if self.config_file.suffix.lower() == '.json':
                    json.dump(self.services, f, indent=2)
                elif self.config_file.suffix.lower() in ['.yaml', '.yml']:
                    try:
                        import yaml
                        yaml.dump(self.services, f)
                    except ImportError:
                        logger.error("YAML support requires PyYAML. Please install it with pip install PyYAML")
                        raise
                else:
                    logger.error(f"Unsupported configuration file format: {self.config_file.suffix}")
                    return
            
            self.last_loaded = self.config_file.stat().st_mtime
            logger.info(f"Wrote {len(self.services)} services to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to write configuration file {self.config_file}: {str(e)}")
            raise
    
    def _maybe_reload(self):
        """Reload the configuration file if it has been modified."""
        if not self.config_file.exists():
            return
        
        try:
            mtime = self.config_file.stat().st_mtime
            if mtime > self.last_loaded:
                logger.debug(f"Configuration file {self.config_file} has been modified, reloading")
                self._load_config()
        except Exception as e:
            logger.error(f"Failed to check configuration file modification time: {str(e)}") 