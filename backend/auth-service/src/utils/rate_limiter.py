from flask import request, jsonify, current_app
from functools import wraps
from redis import Redis
from datetime import datetime, timedelta
import json

redis_client = Redis(
    host=current_app.config.get('REDIS_HOST', 'localhost'),
    port=current_app.config.get('REDIS_PORT', 6379),
    db=current_app.config.get('REDIS_DB', 0)
)

class RateLimiter:
    def __init__(self, key_prefix: str, limit: int, window: int):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window

    def _get_key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    def is_rate_limited(self, identifier: str) -> tuple[bool, int]:
        """Check if the identifier is rate limited"""
        key = self._get_key(identifier)
        pipe = redis_client.pipeline()
        
        now = datetime.utcnow().timestamp()
        window_start = now - self.window
        
        # Remove old entries
        pipe.zremrangebyscore(key, '-inf', window_start)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry
        pipe.expire(key, self.window)
        
        _, _, count, _ = pipe.execute()
        
        return count > self.limit, count

class IPBlocker:
    def __init__(self, block_duration: int = 3600):
        self.block_duration = block_duration
        self.blocked_ips_key = "blocked_ips"

    def is_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked"""
        blocked_until = redis_client.hget(self.blocked_ips_key, ip)
        if not blocked_until:
            return False
        
        return float(blocked_until) > datetime.utcnow().timestamp()

    def block_ip(self, ip: str, reason: str = None):
        """Block an IP address"""
        expires_at = (datetime.utcnow() + timedelta(seconds=self.block_duration)).timestamp()
        redis_client.hset(self.blocked_ips_key, ip, expires_at)
        if reason:
            redis_client.hset(f"{self.blocked_ips_key}:reasons", ip, reason)

    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        redis_client.hdel(self.blocked_ips_key, ip)
        redis_client.hdel(f"{self.blocked_ips_key}:reasons", ip)

def rate_limit(requests: int, window: int, key_func=None):
    """Rate limiting decorator"""
    def decorator(f):
        limiter = RateLimiter(f.__name__, requests, window)
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = key_func(request) if key_func else request.remote_addr
            is_limited, current_count = limiter.is_rate_limited(identifier)
            
            if is_limited:
                return jsonify({
                    'error': 'Too many requests',
                    'retry_after': window,
                    'current_count': current_count,
                    'limit': requests
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ip_block_check(f):
    """IP blocking decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip_blocker = IPBlocker()
        if ip_blocker.is_blocked(request.remote_addr):
            return jsonify({
                'error': 'IP address blocked',
                'code': 'ip_blocked'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def track_failed_attempts(key_prefix: str, identifier: str, max_attempts: int = 5, window: int = 900):
    """Track failed attempts and automatically block if threshold is reached"""
    key = f"{key_prefix}:failed:{identifier}"
    pipe = redis_client.pipeline()
    
    now = datetime.utcnow().timestamp()
    window_start = now - window
    
    pipe.zremrangebyscore(key, '-inf', window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)
    
    _, _, count, _ = pipe.execute()
    
    if count >= max_attempts:
        ip_blocker = IPBlocker()
        ip_blocker.block_ip(
            identifier,
            f"Exceeded maximum failed attempts ({max_attempts} in {window}s)"
        )
        return True, 0
    
    return False, max_attempts - count 