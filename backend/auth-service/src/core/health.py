"""
Health check module for auth service health monitoring and diagnostics.
Provides comprehensive health checks for all auth service dependencies.
"""

import logging
import time
import os
import socket
import platform
import psutil
from datetime import datetime
from flask import Blueprint, jsonify, current_app, request, g

from .config import get_config
from meeting_shared.middleware.request_id import get_request_id

logger = logging.getLogger(__name__)

# Try to import request ID functionality
try:
    HAS_REQUEST_ID = True
except ImportError:
    HAS_REQUEST_ID = False

# Create health blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for the auth service.
    Performs comprehensive checks on all dependencies.
    
    Returns:
        JSON response with health status and checks
    """
    start_time = time.time()
    
    # Initialize response
    response = {
        'service': 'auth-service',
        'status': 'healthy',
        'version': os.environ.get('VERSION', 'dev'),
        'environment': current_app.config.get('ENV', 'production'),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'checks': {}
    }
    
    # Add request ID if available
    if HAS_REQUEST_ID:
        request_id = get_request_id()
        if request_id:
            response['request_id'] = request_id
    
    # Perform database check
    db_status = _check_database()
    response['checks']['database'] = db_status
    
    # Perform Redis check
    redis_status = _check_redis()
    response['checks']['redis'] = redis_status
    
    # Perform email service check
    email_status = _check_email_service()
    response['checks']['email'] = email_status
    
    # Perform OAuth check
    oauth_status = _check_oauth()
    response['checks']['oauth'] = oauth_status
    
    # Add system information
    response['system'] = _get_system_info()
    
    # Determine overall status
    if any(check.get('status') == 'critical' for check in response['checks'].values()):
        response['status'] = 'critical'
    elif any(check.get('status') == 'warning' for check in response['checks'].values()):
        response['status'] = 'warning'
    
    # Add response time
    response['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
    
    # Set appropriate status code
    status_code = 200
    if response['status'] == 'critical':
        status_code = 503  # Service Unavailable
    elif response['status'] == 'warning':
        status_code = 200  # Still OK but with warnings
    
    # Log health check result
    logger_fn = logger.error if response['status'] == 'critical' else \
               logger.warning if response['status'] == 'warning' else \
               logger.info
    
    logger_fn(f"Health check result: {response['status']}")
    
    # Create response
    json_response = jsonify(response)
    
    # Add request ID to response headers if available
    if HAS_REQUEST_ID and get_request_id():
        json_response.headers['X-Request-ID'] = get_request_id()
    
    return json_response, status_code

def _check_database():
    """
    Check database connection and health.
    
    Returns:
        dict: Database health check result
    """
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    
    start_time = time.time()
    db = SQLAlchemy(current_app)
    
    try:
        # Execute simple query to check database connection
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        # Check connection pool statistics
        pool_info = {
            'size': db.engine.pool.size(),
            'checkedin': db.engine.pool.checkedin(),
            'overflow': db.engine.pool.overflow(),
            'checkedout': db.engine.pool.checkedout(),
        }
        
        # Database connection string (mask sensitive info)
        db_url = _mask_connection_string(current_app.config['SQLALCHEMY_DATABASE_URI'])
        
        return {
            'status': 'healthy',
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'pool': pool_info,
            'database_url': db_url
        }
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            'status': 'critical',
            'error': str(e),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Unexpected error during database health check: {str(e)}")
        return {
            'status': 'critical',
            'error': str(e),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }

def _check_redis():
    """
    Check Redis connection and health.
    
    Returns:
        dict: Redis health check result
    """
    import redis
    from redis.exceptions import RedisError
    
    start_time = time.time()
    redis_url = current_app.config.get('REDIS_URL')
    
    if not redis_url:
        return {
            'status': 'warning',
            'error': 'Redis URL not configured',
            'response_time_ms': 0
        }
    
    try:
        # Connect to Redis
        r = redis.from_url(redis_url)
        
        # Test connection with a ping
        assert r.ping()
        
        # Get Redis info
        info = r.info()
        
        redis_info = {
            'version': info.get('redis_version'),
            'used_memory_human': info.get('used_memory_human'),
            'connected_clients': info.get('connected_clients'),
            'uptime_in_seconds': info.get('uptime_in_seconds'),
        }
        
        return {
            'status': 'healthy',
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'info': redis_info,
            'redis_url': _mask_connection_string(redis_url)
        }
    except RedisError as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            'status': 'critical' if current_app.config.get('REDIS_REQUIRED', True) else 'warning',
            'error': str(e),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Unexpected error during Redis health check: {str(e)}")
        return {
            'status': 'critical' if current_app.config.get('REDIS_REQUIRED', True) else 'warning',
            'error': str(e),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }

def _check_email_service():
    """
    Check email service configuration and connectivity.
    
    Returns:
        dict: Email service health check result
    """
    start_time = time.time()
    
    # Check if email is configured
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT')
    smtp_username = current_app.config.get('SMTP_USERNAME')
    
    if not smtp_server or not smtp_port:
        return {
            'status': 'warning',
            'error': 'Email service not fully configured',
            'response_time_ms': 0
        }
    
    # Only check connectivity if email is configured
    if smtp_server and smtp_port:
        import socket
        
        try:
            # Try to connect to the SMTP server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)  # 3 second timeout
            
            # Only test connectivity, don't try to authenticate
            result = sock.connect_ex((smtp_server, int(smtp_port)))
            sock.close()
            
            if result == 0:
                return {
                    'status': 'healthy',
                    'response_time_ms': round((time.time() - start_time) * 1000, 2),
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'configured': True
                }
            else:
                return {
                    'status': 'warning',
                    'error': f'Could not connect to SMTP server (error code: {result})',
                    'response_time_ms': round((time.time() - start_time) * 1000, 2),
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'configured': True
                }
        except Exception as e:
            logger.warning(f"Email service check failed: {str(e)}")
            return {
                'status': 'warning',
                'error': str(e),
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'configured': True
            }
    
    return {
        'status': 'warning',
        'message': 'Email service not configured',
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'configured': False
    }

def _check_oauth():
    """
    Check OAuth provider configuration.
    
    Returns:
        dict: OAuth provider health check result
    """
    start_time = time.time()
    
    # Check if Google OAuth is configured
    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    google_client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    google_configured = bool(google_client_id and google_client_secret)
    
    oauth_providers = {
        'google': {
            'configured': google_configured
        }
    }
    
    # Determine status based on configuration
    if not any(provider['configured'] for provider in oauth_providers.values()):
        status = 'warning'
        message = 'No OAuth providers configured'
    else:
        status = 'healthy'
        message = 'OAuth providers configured'
    
    return {
        'status': status,
        'message': message,
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'providers': oauth_providers
    }

def _get_system_info():
    """
    Get system information for diagnostics.
    
    Returns:
        dict: System information
    """
    # Get CPU and memory info
    try:
        memory = psutil.virtual_memory()
        memory_info = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'used_percent': memory.percent
        }
        
        cpu_info = {
            'percent': psutil.cpu_percent(interval=0.1),
            'count': psutil.cpu_count(),
            'load': _get_load_avg()
        }
        
        disk = psutil.disk_usage('/')
        disk_info = {
            'total_gb': round(disk.total / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'used_percent': disk.percent
        }
    except Exception as e:
        logger.warning(f"Error getting system metrics: {str(e)}")
        memory_info = cpu_info = disk_info = {'error': str(e)}
    
    return {
        'hostname': socket.gethostname(),
        'os': platform.platform(),
        'python_version': platform.python_version(),
        'uptime': _get_uptime(),
        'memory': memory_info,
        'cpu': cpu_info,
        'disk': disk_info
    }

def _get_load_avg():
    """
    Get system load average if available.
    
    Returns:
        list: Load averages for 1, 5, and 15 minutes
    """
    try:
        if hasattr(os, 'getloadavg'):
            return list(os.getloadavg())
        return None
    except (AttributeError, OSError):
        return None

def _get_uptime():
    """
    Get system uptime if available.
    
    Returns:
        float: System uptime in seconds
    """
    try:
        return psutil.boot_time()
    except Exception:
        return None

def _mask_connection_string(conn_string):
    """
    Mask sensitive information in connection strings.
    
    Args:
        conn_string: Connection string to mask
        
    Returns:
        str: Masked connection string
    """
    if not conn_string:
        return None
    
    try:
        # Simple approach: just mask anything after : or @ and before the next /
        import re
        masked = re.sub(r'(?<=:)[^/]+(?=/)', '***', conn_string)
        masked = re.sub(r'(?<=@)[^/]+(?=/)', '***', masked)
        return masked
    except Exception:
        # If anything goes wrong, return a fully masked string
        return "***MASKED***" 