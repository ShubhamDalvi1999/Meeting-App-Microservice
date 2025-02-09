from functools import wraps
from flask import request, current_app, jsonify
from redis import Redis
import time

def rate_limit(limit: int, window: int):
    """
    Rate limiting decorator
    
    Args:
        limit: Number of requests allowed
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            redis_client = Redis.from_url(current_app.config['REDIS_URL'])
            
            # Get rate limit key
            key = f"rate_limit:{request.remote_addr}:{request.endpoint}"
            current = int(time.time())
            window_key = f"{key}:{current // window}"
            
            try:
                count = redis_client.incr(window_key)
                if count == 1:
                    redis_client.expire(window_key, window)
                
                if count > limit:
                    response = jsonify({
                        "error": "Too many requests",
                        "retry_after": window
                    })
                    response.status_code = 429
                    return response
                
                # Execute the function
                response = f(*args, **kwargs)
                
                # Set rate limit headers
                if hasattr(response, 'headers'):
                    remaining = max(0, limit - count)
                    response.headers['X-RateLimit-Remaining'] = str(remaining)
                    response.headers['X-RateLimit-Limit'] = str(limit)
                    response.headers['X-RateLimit-Window'] = str(window)
                
                return response
                
            except Exception as e:
                current_app.logger.error(f"Rate limit error: {str(e)}")
                return f(*args, **kwargs)  # Fail open if Redis is down
            
        return decorated_function
    return decorator 