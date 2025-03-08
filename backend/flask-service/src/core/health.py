"""
Health check module for service health monitoring and diagnostics.
Provides comprehensive health checks for all service dependencies.
"""

import logging
import time
import os
import socket
import platform
import psutil
from datetime import datetime
from flask import Blueprint, jsonify, current_app

from .config import get_config

logger = logging.getLogger(__name__)

# Create health blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint for the service.
    Checks database, Redis, auth service, and system resources.
    """
    start_time = time.time()
    health_data = {
        "service": "Meeting API Service",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": _get_uptime(),
        "status": "checking",
        "checks": {},
        "system": _get_system_info()
    }
    
    # Perform all health checks
    try:
        # Check database
        db_status = _check_database()
        health_data["checks"]["database"] = db_status
        
        # Check Redis
        redis_status = _check_redis()
        health_data["checks"]["redis"] = redis_status
        
        # Check Auth Service connection
        auth_status = _check_auth_service()
        health_data["checks"]["auth_service"] = auth_status
        
        # Determine overall status (healthy only if all checks pass)
        critical_services = [db_status, redis_status]
        if all(service.get('status') == 'healthy' for service in critical_services):
            health_data["status"] = "healthy"
        else:
            health_data["status"] = "unhealthy"
            
    except Exception as e:
        logger.error(f"Error performing health check: {str(e)}")
        health_data["status"] = "error"
        health_data["error"] = str(e)
    
    # Add response time
    health_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Determine response status code
    status_code = 200 if health_data["status"] == "healthy" else 503
    
    return jsonify(health_data), status_code


def _check_database():
    """
    Check database connectivity and health
    """
    from flask_sqlalchemy import SQLAlchemy
    
    try:
        start_time = time.time()
        db = SQLAlchemy(current_app)
        
        # Execute a simple query to verify connection
        result = db.session.execute("SELECT 1").fetchone()
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if result and result[0] == 1:
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "details": {
                    "connection_string": _mask_connection_string(current_app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown'))
                }
            }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "error": "Database query did not return expected result"
            }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _check_redis():
    """
    Check Redis connectivity and health
    """
    from redis import Redis
    
    try:
        start_time = time.time()
        redis_url = current_app.config.get('REDIS_URL')
        redis_client = Redis.from_url(redis_url)
        
        # Ping Redis to verify connection
        if redis_client.ping():
            # Get Redis info
            info = redis_client.info()
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "details": {
                    "redis_version": info.get('redis_version', 'unknown'),
                    "connected_clients": info.get('connected_clients', 'unknown'),
                    "used_memory_human": info.get('used_memory_human', 'unknown')
                }
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Redis ping failed"
            }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _check_auth_service():
    """
    Check Auth Service connectivity
    """
    import requests
    
    try:
        start_time = time.time()
        auth_url = current_app.config.get('AUTH_SERVICE_URL')
        health_url = f"{auth_url}/health"
        
        # Set a short timeout for the request
        timeout = current_app.config.get('HEALTH_TIMEOUT', 3)
        
        # Make request to auth service health endpoint
        response = requests.get(health_url, timeout=timeout)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            try:
                auth_data = response.json()
                return {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "details": {
                        "auth_service_status": auth_data.get('status', 'unknown'),
                        "auth_service_version": auth_data.get('version', 'unknown')
                    }
                }
            except:
                return {
                    "status": "degraded",
                    "response_time_ms": response_time,
                    "error": "Invalid JSON response from auth service"
                }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "error": f"Auth service returned status code {response.status_code}"
            }
    except requests.Timeout:
        return {
            "status": "unhealthy",
            "error": "Auth service connection timeout"
        }
    except requests.ConnectionError:
        return {
            "status": "unhealthy",
            "error": "Could not connect to auth service"
        }
    except Exception as e:
        logger.error(f"Auth service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _get_system_info():
    """
    Get system information for diagnostics
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": disk.percent
            },
            "load_avg": _get_load_avg()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {"error": "Could not retrieve system information"}


def _get_load_avg():
    """
    Get system load average, with Windows compatibility
    """
    try:
        if hasattr(os, 'getloadavg'):
            # Unix systems
            load1, load5, load15 = os.getloadavg()
            return {"1min": round(load1, 2), "5min": round(load5, 2), "15min": round(load15, 2)}
        else:
            # Windows systems
            return {"cpu_percent": psutil.cpu_percent(interval=0.1)}
    except:
        return {"error": "Could not retrieve load average"}


def _get_uptime():
    """
    Get service uptime
    """
    try:
        # Get process start time
        p = psutil.Process(os.getpid())
        start_time = datetime.fromtimestamp(p.create_time())
        uptime = datetime.now() - start_time
        
        # Format uptime as days, hours, minutes, seconds
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "days": int(days),
            "hours": int(hours),
            "minutes": int(minutes),
            "seconds": int(seconds),
            "total_seconds": int(uptime.total_seconds())
        }
    except Exception as e:
        logger.error(f"Error getting uptime: {str(e)}")
        return {"error": "Could not determine uptime"}


def _mask_connection_string(conn_string):
    """
    Mask sensitive information in database connection string
    """
    if not conn_string or '://' not in conn_string:
        return 'invalid-connection-string'
    
    try:
        # Split connection string into parts
        protocol_part, rest = conn_string.split('://')
        
        # Mask username and password if present
        if '@' in rest:
            auth_part, host_part = rest.split('@')
            
            # Replace password with asterisks if present
            if ':' in auth_part:
                username, password = auth_part.split(':')
                masked_auth = f"{username}:***"
            else:
                masked_auth = auth_part
                
            return f"{protocol_part}://{masked_auth}@{host_part}"
        else:
            # No auth part
            return conn_string
    except:
        # If parsing fails, return a generic masked string
        return f"{conn_string.split('://')[0]}://***" 