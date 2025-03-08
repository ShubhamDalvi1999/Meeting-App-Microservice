"""
This module re-exports the shared rate limiter middleware to maintain
backward compatibility with code that imports from here.
"""

import logging
from functools import wraps
from shared.middleware.rate_limiter import RateLimiter, rate_limit as shared_rate_limit

logger = logging.getLogger(__name__)

# Add any auth-service specific rate limiting functionality here if needed

# For backward compatibility, re-export the get_client_identifier function
def get_client_identifier():
    """
    Create a unique client identifier based on IP and user agent
    This helps prevent rate limit circumvention
    """
    from flask import request
    import hashlib
    
    ip = request.remote_addr or 'unknown'
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    # Create a hash of the combined values for privacy
    client_id = hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()
    return client_id

# Re-export the shared rate_limit with potential customization
def rate_limit(limit: int, window: int, key_func=None):
    """
    Rate limiting decorator that uses the shared implementation
    but allows for custom key generation via key_func
    
    Args:
        limit: Number of requests allowed
        window: Time window in seconds
        key_func: Optional custom function to generate rate limit key
    """
    if key_func:
        # If a custom key_func is provided, wrap the shared implementation
        def custom_wrapper(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Use the shared implementation with our custom key function
                return shared_rate_limit(limit, window, key_func=key_func)(f)(*args, **kwargs)
            return wrapper
        return custom_wrapper
    else:
        # Otherwise, use the shared implementation directly
        return shared_rate_limit(limit, window)

# Alias for backward compatibility
custom_rate_limit = rate_limit 