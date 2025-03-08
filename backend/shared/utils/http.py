"""
HTTP utility module for making requests with proper request ID propagation.
"""

import logging
import requests
from typing import Dict, Any, Optional, Union, List
import json
import time

# Try to import request ID functions, with fallbacks if not available
try:
    from ..middleware.request_id import get_request_id, get_correlation_id
except (ImportError, ValueError):
    # Simple fallback implementations
    def get_request_id():
        return None
        
    def get_correlation_id():
        return None

logger = logging.getLogger(__name__)

def add_request_id_headers(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Add request ID headers to an existing headers dictionary.
    
    Args:
        headers: Existing headers dictionary or None
        
    Returns:
        Headers dictionary with request ID headers added
    """
    if headers is None:
        headers = {}
    
    # Add request ID headers if they exist
    request_id = get_request_id()
    if request_id:
        headers.setdefault('X-Request-ID', request_id)
    
    correlation_id = get_correlation_id()
    if correlation_id:
        headers.setdefault('X-Correlation-ID', correlation_id)
    
    return headers

def make_request(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    files: Optional[Dict[str, Any]] = None,
    auth: Optional[Any] = None,
    timeout: Union[float, tuple] = 10.0,
    verify: bool = True,
    cert: Optional[Union[str, tuple]] = None,
    allow_redirects: bool = True,
    proxies: Optional[Dict[str, str]] = None,
    stream: bool = False,
    retry_count: int = 3,
    retry_backoff_factor: float = 0.3,
    retry_status_codes: Optional[List[int]] = None
) -> requests.Response:
    """
    Make an HTTP request with proper request ID propagation and retries.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: URL to request
        headers: Optional request headers
        params: Optional URL parameters
        json_data: Optional JSON data to send
        data: Optional form data to send
        files: Optional files to upload
        auth: Optional authentication tuple or object
        timeout: Request timeout in seconds (default: 10.0)
        verify: Whether to verify SSL certificates
        cert: Optional SSL client certificate
        allow_redirects: Whether to follow redirects
        proxies: Optional proxy servers
        stream: Whether to stream the response
        retry_count: Number of retries for transient errors
        retry_backoff_factor: Backoff factor for retries
        retry_status_codes: Status codes to retry (default: 429, 500, 502, 503, 504)
        
    Returns:
        Response object
    """
    # Add request ID headers
    headers = add_request_id_headers(headers)
    
    # Default retry status codes
    if retry_status_codes is None:
        retry_status_codes = [429, 500, 502, 503, 504]
    
    # Logging context
    log_context = {
        "method": method,
        "url": url,
        "service": url.split('/')[2] if '://' in url else url.split('/')[0]
    }
    
    if params:
        log_context["params"] = params
    
    logger.debug(f"Making {method} request to {url}", extra=log_context)
    
    # Retry loop
    last_exception = None
    for retry in range(retry_count + 1):
        try:
            # Starting timer for the request
            start_time = time.time()
            
            # Make the request
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data,
                files=files,
                auth=auth,
                timeout=timeout,
                verify=verify,
                cert=cert,
                allow_redirects=allow_redirects,
                proxies=proxies,
                stream=stream
            )
            
            # Calculate request duration
            duration = time.time() - start_time
            log_context["duration"] = f"{duration:.3f}s"
            log_context["status_code"] = response.status_code
            
            # Check if we should retry based on status code
            if response.status_code in retry_status_codes and retry < retry_count:
                logger.warning(
                    f"Received status {response.status_code} from {url}, retrying ({retry+1}/{retry_count})",
                    extra=log_context
                )
                time.sleep(retry_backoff_factor * (2 ** retry))
                continue
            
            # Log success or non-retryable failure
            if response.status_code < 400:
                logger.debug(
                    f"Successfully called {url} ({response.status_code})",
                    extra=log_context
                )
            else:
                logger.error(
                    f"Error calling {url} ({response.status_code}): {response.text[:100]}",
                    extra=log_context
                )
            
            return response
            
        except (requests.RequestException, IOError) as e:
            last_exception = e
            if retry < retry_count:
                logger.warning(
                    f"Request to {url} failed: {str(e)}, retrying ({retry+1}/{retry_count})",
                    extra=log_context
                )
                time.sleep(retry_backoff_factor * (2 ** retry))
            else:
                logger.error(
                    f"Request to {url} failed after {retry_count} retries: {str(e)}",
                    extra=log_context
                )
    
    # If we get here, all retries failed
    if last_exception:
        raise last_exception
    
    # This should never happen, but just in case
    raise RuntimeError(f"Failed to make request to {url} after {retry_count} retries")


# Convenience methods for common HTTP verbs
def get(url, **kwargs):
    """Make a GET request."""
    return make_request("GET", url, **kwargs)

def post(url, **kwargs):
    """Make a POST request."""
    return make_request("POST", url, **kwargs)

def put(url, **kwargs):
    """Make a PUT request."""
    return make_request("PUT", url, **kwargs)

def delete(url, **kwargs):
    """Make a DELETE request."""
    return make_request("DELETE", url, **kwargs)

def patch(url, **kwargs):
    """Make a PATCH request."""
    return make_request("PATCH", url, **kwargs)


# Export symbols
__all__ = [
    'make_request',
    'add_request_id_headers',
    'get',
    'post',
    'put',
    'delete',
    'patch'
] 