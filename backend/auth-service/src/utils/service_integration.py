from typing import Optional, Dict, Any
from flask import current_app
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from circuitbreaker import circuit
import logging
import json
from redis import Redis
from ..models.auth import AuthUser, UserSession
from ..database import db
from .database import transaction_context

logger = logging.getLogger(__name__)

class ServiceIntegrationError(Exception):
    """Base exception for service integration errors"""
    pass

class ServiceConnectionError(ServiceIntegrationError):
    """Raised when connection to service fails"""
    pass

class ServiceTimeoutError(ServiceIntegrationError):
    """Raised when service request times out"""
    pass

class ServiceResponseError(ServiceIntegrationError):
    """Raised when service returns unexpected response"""
    pass

class ServiceIntegration:
    def __init__(self):
        self.flask_service_url = current_app.config.get('FLASK_SERVICE_URL', 'http://backend:5000')
        self.timeout = current_app.config.get('SERVICE_TIMEOUT', 5)
        self.enabled = current_app.config.get('SERVICE_SYNC_ENABLED', True)
        # Initialize Redis for metrics
        self.redis_client = None
        try:
            redis_url = current_app.config.get('REDIS_URL')
            if redis_url:
                self.redis_client = Redis.from_url(redis_url)
        except Exception as e:
            logger.error(f"Failed to initialize Redis for service integration metrics: {e}")

    def _record_metric(self, name: str, success: bool, duration_ms: float):
        """Record service integration metrics in Redis"""
        if not self.redis_client:
            return
            
        try:
            # Record the outcome (success/failure)
            status = "success" if success else "failure"
            self.redis_client.hincrby(f"metrics:service_integration:{name}", status, 1)
            
            # Record the response time
            self.redis_client.lpush(f"metrics:service_integration:{name}:duration", duration_ms)
            self.redis_client.ltrim(f"metrics:service_integration:{name}:duration", 0, 99)  # Keep last 100
            
            # Calculate and update average response time
            durations = self.redis_client.lrange(f"metrics:service_integration:{name}:duration", 0, -1)
            if durations:
                avg_duration = sum(float(d) for d in durations) / len(durations)
                self.redis_client.hset(f"metrics:service_integration:{name}", "avg_duration_ms", avg_duration)
                
            # Set expiry for metrics
            self.redis_client.expire(f"metrics:service_integration:{name}", 86400 * 7)  # 7 days
            self.redis_client.expire(f"metrics:service_integration:{name}:duration", 86400 * 7)  # 7 days
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        start_time = datetime.utcnow()
        success = False
        
        try:
            # Add service key to headers if available
            service_key = current_app.config.get('SERVICE_KEY')
            if service_key and 'headers' not in kwargs:
                kwargs['headers'] = {'X-Service-Key': service_key}
            elif service_key and 'headers' in kwargs:
                kwargs['headers'].update({'X-Service-Key': service_key})
                
            response = requests.request(
                method,
                f"{self.flask_service_url}{endpoint}",
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            success = True
            return response
        except requests.ConnectionError as e:
            raise ServiceConnectionError(f"Failed to connect to service: {str(e)}")
        except requests.Timeout as e:
            raise ServiceTimeoutError(f"Service request timed out: {str(e)}")
        except requests.HTTPError as e:
            raise ServiceResponseError(f"Service returned error response: {str(e)}")
        except Exception as e:
            raise ServiceIntegrationError(f"Unexpected error in service request: {str(e)}")
        finally:
            # Record metrics
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            endpoint_name = endpoint.split('/')[-1]
            self._record_metric(f"{method}_{endpoint_name}", success, duration_ms)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((ServiceConnectionError, ServiceTimeoutError))
    )
    @circuit(failure_threshold=5, recovery_timeout=60)
    def sync_user_session(self, user_id: int, token: str, session_data: Dict[str, Any]) -> bool:
        """
        Synchronize user session with main service with retry logic and circuit breaker
        """
        if not self.enabled:
            logger.info("Service synchronization is disabled")
            return True

        try:
            # For bulk operations, add a bulk flag to optimize
            is_bulk = user_id is None and token is None
            
            response = self._make_request(
                'POST',
                '/api/auth/sync-session',
                json={
                    "user_id": user_id,
                    "token": token,
                    "session_data": session_data,
                    "is_bulk": is_bulk,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # For successful responses, record successful sync
            if self.redis_client and user_id:
                sync_key = f"last_sync:user:{user_id}"
                self.redis_client.hset(sync_key, "timestamp", datetime.utcnow().isoformat())
                self.redis_client.hset(sync_key, "status", "success")
                self.redis_client.expire(sync_key, 86400)  # 24 hours
                
            return response.status_code == 200
        except ServiceIntegrationError as e:
            logger.error(f"Failed to sync session: {str(e)}")
            
            # For failures, record the failed sync
            if self.redis_client and user_id:
                sync_key = f"last_sync:user:{user_id}"
                self.redis_client.hset(sync_key, "timestamp", datetime.utcnow().isoformat())
                self.redis_client.hset(sync_key, "status", "failure")
                self.redis_client.hset(sync_key, "error", str(e))
                self.redis_client.expire(sync_key, 86400)  # 24 hours
                
                # Queue for retry if appropriate
                if isinstance(e, (ServiceConnectionError, ServiceTimeoutError)):
                    retry_key = f"sync_retry:user:{user_id}"
                    self.redis_client.lpush(retry_key, json.dumps({
                        "user_id": user_id,
                        "token": token,
                        "session_data": session_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    self.redis_client.expire(retry_key, 86400)  # 24 hours
            
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    @circuit(failure_threshold=5, recovery_timeout=60)
    def validate_token(self, token: str) -> Optional[dict]:
        """
        Validate token with main service with retry logic and circuit breaker
        """
        if not self.enabled:
            return None

        try:
            response = self._make_request(
                'POST',
                '/api/auth/validate-token',
                json={"token": token}
            )
            return response.json()
        except ServiceIntegrationError as e:
            logger.error(f"Failed to validate token: {str(e)}")
            return None

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=30))
    def sync_user_data(self, user: AuthUser) -> bool:
        """
        Synchronize user data with main service with enhanced retry logic
        """
        if not self.enabled:
            return True

        try:
            user_data = {
                "id": user.id,
                "email": user.email,
                "is_active": not user.is_locked(),
                "is_email_verified": user.is_email_verified,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_picture": user.profile_picture,
                "last_sync": datetime.utcnow().isoformat()
            }

            response = self._make_request(
                'POST',
                '/api/auth/sync-user',
                json=user_data
            )
            
            # Record successful sync
            if self.redis_client:
                sync_key = f"last_sync:user:{user.id}"
                self.redis_client.hset(sync_key, "timestamp", datetime.utcnow().isoformat())
                self.redis_client.hset(sync_key, "status", "success")
                self.redis_client.expire(sync_key, 86400)  # 24 hours
                
            return response.status_code == 200
        except ServiceIntegrationError as e:
            logger.error(f"Failed to sync user data: {str(e)}")
            
            # Record failed sync
            if self.redis_client:
                sync_key = f"last_sync:user:{user.id}"
                self.redis_client.hset(sync_key, "timestamp", datetime.utcnow().isoformat())
                self.redis_client.hset(sync_key, "status", "failure")
                self.redis_client.hset(sync_key, "error", str(e))
                self.redis_client.expire(sync_key, 86400)  # 24 hours
            
            return False

    def verify_user_consistency(self, user_id: int) -> bool:
        """
        Verify user data consistency across services
        """
        if not self.enabled:
            return True

        try:
            # Get user data from auth service
            auth_user = AuthUser.query.get(user_id)
            if not auth_user:
                return False

            # Get user data from main service
            response = self._make_request('GET', f'/api/users/{user_id}')
            flask_user = response.json()

            # Compare critical fields
            return all([
                auth_user.email == flask_user.get('email'),
                auth_user.is_email_verified == flask_user.get('is_email_verified'),
                not auth_user.is_locked() == flask_user.get('is_active')
            ])
        except ServiceIntegrationError as e:
            logger.error(f"Failed to verify user consistency: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=30))
    def revoke_user_sessions(self, user_id: int, reason: str = None) -> bool:
        """
        Revoke all user sessions in main service with enhanced retry logic
        """
        if not self.enabled:
            return True

        try:
            response = self._make_request(
                'POST',
                '/api/auth/revoke-user-sessions',
                json={
                    "user_id": user_id,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return response.status_code == 200
        except ServiceIntegrationError as e:
            logger.error(f"Failed to revoke sessions: {str(e)}")
            
            # Queue for retry if appropriate
            if isinstance(e, (ServiceConnectionError, ServiceTimeoutError)) and self.redis_client:
                retry_key = f"revoke_retry:user:{user_id}"
                self.redis_client.lpush(retry_key, json.dumps({
                    "user_id": user_id,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                self.redis_client.expire(retry_key, 86400)  # 24 hours
            
            return False
            
    def process_pending_syncs(self) -> int:
        """
        Process any pending sync operations that failed previously
        Returns the number of operations processed
        """
        if not self.enabled or not self.redis_client:
            return 0
            
        try:
            # Get all retry keys
            retry_keys = self.redis_client.keys("sync_retry:user:*")
            processed = 0
            
            for key in retry_keys:
                # Process up to 5 pending operations per user
                for _ in range(5):
                    retry_data = self.redis_client.lpop(key)
                    if not retry_data:
                        break
                        
                    try:
                        data = json.loads(retry_data)
                        if self.sync_user_session(
                            data.get("user_id"), 
                            data.get("token"), 
                            data.get("session_data")
                        ):
                            processed += 1
                    except Exception as e:
                        logger.error(f"Failed to process pending sync: {e}")
                        # Push back to queue
                        self.redis_client.rpush(key, retry_data)
                        break
                        
            # Similar logic for revocation retries
            revoke_keys = self.redis_client.keys("revoke_retry:user:*")
            for key in revoke_keys:
                for _ in range(5):
                    retry_data = self.redis_client.lpop(key)
                    if not retry_data:
                        break
                        
                    try:
                        data = json.loads(retry_data)
                        if self.revoke_user_sessions(
                            data.get("user_id"),
                            data.get("reason")
                        ):
                            processed += 1
                    except Exception as e:
                        logger.error(f"Failed to process pending revocation: {e}")
                        self.redis_client.rpush(key, retry_data)
                        break
                        
            return processed
        except Exception as e:
            logger.error(f"Error processing pending syncs: {e}")
            return 0 