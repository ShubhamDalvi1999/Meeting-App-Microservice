"""
Kubernetes service discovery.
Retrieves service information from the Kubernetes API.
"""

import os
import logging
from .base import ServiceDiscovery

try:
    from kubernetes import client, config
    HAS_K8S = True
except ImportError:
    HAS_K8S = False

logger = logging.getLogger(__name__)

class KubernetesServiceDiscovery(ServiceDiscovery):
    """
    Service discovery that retrieves service information from the Kubernetes API.
    Requires the kubernetes package to be installed.
    """
    
    def __init__(self, namespace=None, in_cluster=None):
        """
        Initialize Kubernetes service discovery.
        
        Args:
            namespace: Kubernetes namespace to search in (default: from env or 'default')
            in_cluster: Whether to use in-cluster config (default: auto-detect)
        """
        if not HAS_K8S:
            raise ImportError("kubernetes package is required for KubernetesServiceDiscovery")
        
        # Get namespace from environment or use default
        self.namespace = namespace or os.environ.get('KUBERNETES_NAMESPACE', 'default')
        
        # Auto-detect if we're running in a cluster
        if in_cluster is None:
            in_cluster = os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token')
        
        self.in_cluster = in_cluster
        
        # Initialize Kubernetes client
        if self.in_cluster:
            config.load_incluster_config()
            logger.info("Using in-cluster Kubernetes configuration")
        else:
            config.load_kube_config()
            logger.info("Using local Kubernetes configuration")
        
        self.core_api = client.CoreV1Api()
        logger.info(f"Initialized Kubernetes service discovery in namespace {self.namespace}")
    
    def get_service_url(self, service_name, default=None):
        """
        Get the URL for a service from Kubernetes.
        
        Args:
            service_name: The service name to look up
            default: Default URL if service not found
            
        Returns:
            The service URL, or default if not found
        """
        try:
            normalized_name = self._normalize_service_name(service_name)
            
            # Get service from Kubernetes
            service = self.core_api.read_namespaced_service(
                name=normalized_name,
                namespace=self.namespace
            )
            
            if not service:
                logger.debug(f"Service {service_name} not found in Kubernetes")
                return default
            
            # Get cluster IP
            cluster_ip = service.spec.cluster_ip
            
            # Get port
            if not service.spec.ports:
                logger.warning(f"Service {service_name} has no ports")
                return default
            
            # Use the first port by default
            port = service.spec.ports[0].port
            
            # Check for protocol annotation
            annotations = service.metadata.annotations or {}
            protocol = annotations.get('protocol', 'http')
            
            url = f"{protocol}://{normalized_name}.{self.namespace}.svc.cluster.local:{port}"
            logger.debug(f"Found service URL for {service_name} in Kubernetes: {url}")
            return url
        except client.rest.ApiException as e:
            if e.status == 404:
                logger.debug(f"Service {service_name} not found in Kubernetes")
                return default
            logger.error(f"Kubernetes API error: {str(e)}")
            return default
        except Exception as e:
            logger.error(f"Error getting service URL from Kubernetes: {str(e)}")
            return default
    
    def get_service(self, service_name, default=None):
        """
        Get detailed information for a service from Kubernetes.
        
        Args:
            service_name: The service name to look up
            default: Default value if service not found
            
        Returns:
            Dictionary with service details, or default if not found
        """
        try:
            normalized_name = self._normalize_service_name(service_name)
            
            # Get service from Kubernetes
            service = self.core_api.read_namespaced_service(
                name=normalized_name,
                namespace=self.namespace
            )
            
            if not service:
                logger.debug(f"Service {service_name} not found in Kubernetes")
                return default
            
            # Get endpoints for this service
            endpoints = self.core_api.read_namespaced_endpoints(
                name=normalized_name,
                namespace=self.namespace
            )
            
            # Format service information
            service_info = {
                'name': normalized_name,
                'namespace': self.namespace,
                'cluster_ip': service.spec.cluster_ip,
                'external_ip': None,
                'port': None,
                'ports': [],
                'annotations': service.metadata.annotations or {},
                'labels': service.metadata.labels or {},
                'type': service.spec.type,
                'endpoints': []
            }
            
            # Get external IP if available
            if service.status.load_balancer and service.status.load_balancer.ingress:
                for ingress in service.status.load_balancer.ingress:
                    if ingress.ip:
                        service_info['external_ip'] = ingress.ip
                        break
                    elif ingress.hostname:
                        service_info['external_hostname'] = ingress.hostname
                        break
            
            # Get ports
            if service.spec.ports:
                for port in service.spec.ports:
                    port_info = {
                        'name': port.name,
                        'port': port.port,
                        'target_port': port.target_port,
                        'protocol': port.protocol
                    }
                    service_info['ports'].append(port_info)
                
                # Set default port to the first one
                service_info['port'] = service.spec.ports[0].port
            
            # Get endpoints
            if endpoints and endpoints.subsets:
                for subset in endpoints.subsets:
                    for address in subset.addresses:
                        for port in subset.ports:
                            endpoint = {
                                'ip': address.ip,
                                'hostname': address.hostname,
                                'node_name': getattr(address, 'node_name', None),
                                'port': port.port,
                                'protocol': port.protocol
                            }
                            service_info['endpoints'].append(endpoint)
            
            # Check for protocol annotation
            annotations = service.metadata.annotations or {}
            protocol = annotations.get('protocol', 'http')
            
            # Construct URL
            service_info['url'] = f"{protocol}://{normalized_name}.{self.namespace}.svc.cluster.local"
            if service_info['port']:
                service_info['url'] += f":{service_info['port']}"
            
            logger.debug(f"Found service {service_name} in Kubernetes")
            return service_info
        except client.rest.ApiException as e:
            if e.status == 404:
                logger.debug(f"Service {service_name} not found in Kubernetes")
                return default
            logger.error(f"Kubernetes API error: {str(e)}")
            return default
        except Exception as e:
            logger.error(f"Error getting service from Kubernetes: {str(e)}")
            return default
    
    def get_services(self):
        """
        Get all available services in the namespace from Kubernetes.
        
        Returns:
            Dictionary of service name to service details
        """
        try:
            # Get all services in namespace
            service_list = self.core_api.list_namespaced_service(namespace=self.namespace)
            
            if not service_list or not service_list.items:
                logger.debug(f"No services found in namespace {self.namespace}")
                return {}
            
            services = {}
            
            # Get details for each service
            for k8s_service in service_list.items:
                service_name = k8s_service.metadata.name
                service_info = self.get_service(service_name)
                if service_info:
                    normalized_name = self._normalize_service_name(service_name)
                    services[normalized_name] = service_info
            
            logger.debug(f"Found {len(services)} services in namespace {self.namespace}")
            return services
        except Exception as e:
            logger.error(f"Error getting services from Kubernetes: {str(e)}")
            return {}
    
    def register_service(self, service_name, service_data):
        """
        Register a service with Kubernetes.
        Note: This is not typically how Kubernetes services are created.
        Kubernetes services are usually defined via YAML manifests or Helm charts.
        
        Args:
            service_name: The service name to register
            service_data: Service details
            
        Returns:
            False - not supported
        """
        logger.warning("Service registration via API is not recommended in Kubernetes")
        logger.warning("Use kubectl apply, Helm, or another deployment tool instead")
        return False
    
    def deregister_service(self, service_name):
        """
        Deregister a service from Kubernetes.
        Note: This is not typically how Kubernetes services are removed.
        
        Args:
            service_name: The service name to deregister
            
        Returns:
            False - not supported
        """
        logger.warning("Service deregistration via API is not recommended in Kubernetes")
        logger.warning("Use kubectl delete, Helm, or another deployment tool instead")
        return False 