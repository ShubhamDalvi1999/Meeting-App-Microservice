from functools import wraps
from flask import request, jsonify, current_app
from redis import Redis
from datetime import datetime
import logging
from meeting_shared.schemas.base import ErrorResponse

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, redis_url=None):
        self.redis = Redis.from_url(
            redis_url or current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        )

    def is_rate_limited(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """
        Check if request is rate limited
        
        Args:
            key: Rate limit key
            limit: Maximum number of requests
            window: Time window in seconds
            
        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        pipe = self.redis.pipeline()
        now = datetime.utcnow().timestamp()
        window_start = now - window
        
        # Remove old entries
        pipe.zremrangebyscore(key, '-inf', window_start)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry
        pipe.expire(key, window)
        
        _, _, count, _ = pipe.execute()
        
        return count > limit, max(0, limit - count)

def rate_limit(limit: int, window: int, key_func=None):
    """
    Rate limiting decorator
    
    Args:
        limit: Maximum number of requests
        window: Time window in seconds
        key_func: Optional function to generate rate limit key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter = RateLimiter()
            
            # Get rate limit key
            if key_func:
                key = f"rate_limit:{f.__name__}:{key_func(request)}"
            else:
                key = f"rate_limit:{f.__name__}:{request.remote_addr}"
            
            is_limited, remaining = limiter.is_rate_limited(key, limit, window)
            
            if is_limited:
                response = ErrorResponse(
                    error="Rate Limit Exceeded",
                    message="Too many requests",
                    details={
                        "limit": limit,
                        "window": window,
                        "retry_after": window
                    }
                )
                return jsonify(response.model_dump()), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response, status_code = response
            else:
                status_code = 200
                
            response.headers['X-RateLimit-Limit'] = str(limit)
            response.headers['X-RateLimit-Remaining'] = str(remaining)
            response.headers['X-RateLimit-Reset'] = str(int(datetime.utcnow().timestamp() + window))
            
            return response, status_code
            
        return decorated_function
    return decorator 