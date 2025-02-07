from datetime import datetime, timedelta
import jwt
from typing import Optional, Dict, Any
from flask import current_app
import logging
from .service_integration import ServiceIntegration

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self):
        self.secret_key = current_app.config['JWT_SECRET_KEY']
        self.algorithm = 'HS256'
        self.service_integration = ServiceIntegration()

    def generate_token(self, user_id: int, expires_delta: timedelta = None) -> str:
        """Generate a new JWT token"""
        if expires_delta is None:
            expires_delta = timedelta(days=1)

        data = {
            'user_id': user_id,
            'exp': datetime.utcnow() + expires_delta,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(self, user_id: int, session_id: int) -> str:
        """Generate a refresh token"""
        data = {
            'user_id': user_id,
            'session_id': session_id,
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str, verify_type: str = None) -> Optional[Dict[str, Any]]:
        """Validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if verify_type and payload.get('type') != verify_type:
                logger.warning(f"Invalid token type: expected {verify_type}, got {payload.get('type')}")
                return None

            # Sync validation with main service
            if not self.service_integration.validate_token(token):
                logger.warning("Token validation failed in main service")
                return None

            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        payload = self.validate_token(refresh_token, verify_type='refresh')
        if not payload:
            return None

        return self.generate_token(payload['user_id'])

    def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get('user_id')
            
            # Revoke in main service
            return self.service_integration.revoke_user_sessions(user_id, reason='Token revoked')
        except jwt.InvalidTokenError:
            return False 