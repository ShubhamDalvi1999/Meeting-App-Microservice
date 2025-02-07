from typing import Optional, Dict, Any
from flask import current_app
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from circuitbreaker import circuit
import logging
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

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        try:
            response = requests.request(
                method,
                f"{self.flask_service_url}{endpoint}",
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.ConnectionError as e:
            raise ServiceConnectionError(f"Failed to connect to service: {str(e)}")
        except requests.Timeout as e:
            raise ServiceTimeoutError(f"Service request timed out: {str(e)}")
        except requests.HTTPError as e:
            raise ServiceResponseError(f"Service returned error response: {str(e)}")
        except Exception as e:
            raise ServiceIntegrationError(f"Unexpected error in service request: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
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
            response = self._make_request(
                'POST',
                '/api/auth/sync-session',
                json={
                    "user_id": user_id,
                    "token": token,
                    "session_data": session_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return response.status_code == 200
        except ServiceIntegrationError as e:
            logger.error(f"Failed to sync session: {str(e)}")
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def sync_user_data(self, user: AuthUser) -> bool:
        """
        Synchronize user data with main service
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
            return response.status_code == 200
        except ServiceIntegrationError as e:
            logger.error(f"Failed to sync user data: {str(e)}")
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def revoke_user_sessions(self, user_id: int, reason: str = None) -> bool:
        """
        Revoke all user sessions in main service with retry logic
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
            return False

    def check_service_health(self) -> bool:
        """
        Check if the main service is healthy
        """
        try:
            response = self._make_request('GET', '/health')
            return response.status_code == 200
        except ServiceIntegrationError:
            return False 