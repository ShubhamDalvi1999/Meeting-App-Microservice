from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps
import time
from typing import Optional
from flask import request, Flask
import os
import threading
import logging

logger = logging.getLogger(__name__)

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

db_connections_current = Gauge(
    'db_connections_current',
    'Current number of database connections'
)

redis_connections_current = Gauge(
    'redis_connections_current',
    'Current number of Redis connections'
)

class MetricsManager:
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize metrics with Flask app"""
        self.app = app
        
        if os.getenv('ENABLE_METRICS', 'false').lower() == 'true':
            # Start metrics server in a separate thread
            metrics_port = int(os.getenv('METRICS_PORT', 9090))
            threading.Thread(
                target=start_http_server,
                args=(metrics_port,),
                daemon=True
            ).start()
            logger.info(f"Metrics server started on port {metrics_port}")

            # Register metrics middleware
            app.before_request(self._before_request)
            app.after_request(self._after_request)

    def _before_request(self):
        """Store start time for request duration calculation"""
        request._prometheus_metrics_start_time = time.time()

    def _after_request(self, response):
        """Record request duration and update metrics"""
        if hasattr(request, '_prometheus_metrics_start_time'):
            duration = time.time() - request._prometheus_metrics_start_time
            endpoint = request.endpoint or 'unknown'
            
            # Record request duration
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            # Count total requests
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
        return response

def track_db_connections(f):
    """Decorator to track database connections"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        db_connections_current.inc()
        try:
            return f(*args, **kwargs)
        finally:
            db_connections_current.dec()
    return wrapped

def track_redis_connections(f):
    """Decorator to track Redis connections"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        redis_connections_current.inc()
        try:
            return f(*args, **kwargs)
        finally:
            redis_connections_current.dec()
    return wrapped 