from flask import Blueprint, jsonify, current_app
import requests
import time
from datetime import datetime, timezone
import logging
from sqlalchemy import text
from ..database import db

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'backend',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check that verifies all dependencies"""
    start_time = time.time()
    health_status = {
        'service': 'backend',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dependencies': {},
        'status': 'healthy'  # Will be updated if any dependency is unhealthy
    }
    
    # Check database
    try:
        db.session.execute(text('SELECT 1'))
        health_status['dependencies']['database'] = {
            'status': 'healthy',
            'type': 'postgres'
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status['dependencies']['database'] = {
            'status': 'unhealthy',
            'error': str(e),
            'type': 'postgres'
        }
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        redis_client = current_app.extensions.get('redis')
        if redis_client:
            redis_client.ping()
            health_status['dependencies']['redis'] = {
                'status': 'healthy'
            }
        else:
            health_status['dependencies']['redis'] = {
                'status': 'unavailable',
                'error': 'Redis client not initialized'
            }
            health_status['status'] = 'degraded'
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        health_status['dependencies']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Check auth service
    try:
        auth_service_url = current_app.config.get('AUTH_SERVICE_URL')
        response = requests.get(
            f"{auth_service_url}/health", 
            timeout=5
        )
        if response.status_code == 200:
            health_status['dependencies']['auth_service'] = {
                'status': 'healthy',
                'url': auth_service_url
            }
        else:
            health_status['dependencies']['auth_service'] = {
                'status': 'unhealthy',
                'error': f"Unexpected status code: {response.status_code}",
                'url': auth_service_url
            }
            health_status['status'] = 'unhealthy'
    except requests.RequestException as e:
        logger.error(f"Auth service health check failed: {str(e)}")
        health_status['dependencies']['auth_service'] = {
            'status': 'unhealthy',
            'error': str(e),
            'url': current_app.config.get('AUTH_SERVICE_URL')
        }
        health_status['status'] = 'unhealthy'
    
    # Check token validation
    try:
        # Try a basic token validation with a dummy token (should fail but connection should work)
        auth_service_url = current_app.config.get('AUTH_SERVICE_URL')
        service_key = current_app.config.get('SERVICE_KEY')
        
        response = requests.post(
            f"{auth_service_url}/api/auth/validate-token",
            json={"token": "dummy_test_token"},
            headers={"X-Service-Key": service_key},
            timeout=5
        )
        
        if response.status_code in [401, 400]:  # Expected for invalid token
            health_status['dependencies']['token_validation'] = {
                'status': 'healthy',
                'message': 'Token validation endpoint accessible'
            }
        else:
            health_status['dependencies']['token_validation'] = {
                'status': 'degraded',
                'error': f"Unexpected status code: {response.status_code}",
                'message': 'Token validation endpoint is accessible but not working as expected'
            }
            if health_status['status'] == 'healthy':
                health_status['status'] = 'degraded'
    except requests.RequestException as e:
        logger.error(f"Token validation health check failed: {str(e)}")
        health_status['dependencies']['token_validation'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Add response time
    health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
    
    # Return appropriate status code based on health
    status_code = 200
    if health_status['status'] == 'degraded':
        status_code = 200  # Still operational but with issues
    elif health_status['status'] == 'unhealthy':
        status_code = 503  # Service unavailable
        
    return jsonify(health_status), status_code 