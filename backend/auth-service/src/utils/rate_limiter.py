from functools import wraps
from flask import request, current_app, jsonify, g
from redis import Redis
import time
import hashlib
import logging

logger = logging.getLogger(__name__)

def get_client_identifier():
    """
    Create a unique client identifier based on IP and user agent
    This helps prevent rate limit circumvention
    """
    ip = request.remote_addr or 'unknown'
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    # Create a hash of the combined values for privacy
    client_id = hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()
    return client_id

def rate_limit(limit: int, window: int, key_func=None):
    """
    Enhanced rate limiting decorator
    
    Args:
        limit: Number of requests allowed
        window: Time window in seconds
        key_func: Optional custom function to generate rate limit key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            redis_client = Redis.from_url(current_app.config['REDIS_URL'])
            
            # Get rate limit key
            if key_func:
                client_id = key_func(request)
            else:
                client_id = get_client_identifier()
                
            key = f"rate_limit:{request.endpoint}:{client_id}"
            current = int(time.time())
            window_key = f"{key}:{current // window}"
            
            try:
                pipe = redis_client.pipeline()
                pipe.incr(window_key)
                pipe.expire(window_key, window)
                results = pipe.execute()
                count = results[0]
                
                if count > limit:
                    logger.warning(f"Rate limit exceeded for endpoint {request.endpoint} by client {client_id[:8]}...")
                    
                    # Store rate limit violation in Redis for analytics
                    violation_key = f"rate_limit_violations:{request.endpoint}"
                    redis_client.zincrby(violation_key, 1, client_id)
                    redis_client.expire(violation_key, 86400)  # Keep for 24 hours
                    
                    response = jsonify({
                        "error": "Too many requests",
                        "message": f"Request rate limit exceeded. Try again in {window} seconds.",
                        "retry_after": window
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(window)
                    return response
                
                # Execute the function
                response = f(*args, **kwargs)
                
                # Set rate limit headers
                if hasattr(response, 'headers'):
                    remaining = max(0, limit - count)
                    response.headers['X-RateLimit-Remaining'] = str(remaining)
                    response.headers['X-RateLimit-Limit'] = str(limit)
                    response.headers['X-RateLimit-Reset'] = str(current + window - (current % window))
                
                return response
                
            except Exception as e:
                logger.error(f"Rate limit error: {str(e)}")
                current_app.logger.exception("Redis error in rate limiter")
                # Fail open if Redis is down (allow the request)
                return f(*args, **kwargs)
            
        return decorated_function
    return decorator

# Alias for backward compatibility
custom_rate_limit = rate_limit 