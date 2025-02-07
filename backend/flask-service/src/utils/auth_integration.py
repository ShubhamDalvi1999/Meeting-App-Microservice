from typing import Optional, Dict, Any
from flask import current_app, request
from shared.database import db, transaction_context
from shared.middleware.auth import jwt_required
from shared.schemas.base import ErrorResponse
from ..models.user import User
import jwt
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AuthIntegration:
    def __init__(self):
        self.jwt_secret = current_app.config['JWT_SECRET_KEY']
        self.algorithm = 'HS256'

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload if valid"""
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

    def sync_user_session(self, data: Dict[str, Any]) -> bool:
        """
        Synchronize user session data from auth service
        """
        try:
            with transaction_context() as session:
                user_id = data.get('user_id')
                if not user_id:
                    return True  # Skip for cleanup notifications
                
                user = User.query.get(user_id)
                if not user:
                    logger.warning(f"User {user_id} not found during session sync")
                    return False

                # Update user's session state
                session_data = data.get('session_data', {})
                user.last_login_at = datetime.fromisoformat(session_data.get('expires_at')) if session_data.get('expires_at') else None
                user.is_active = session_data.get('is_active', True)
                
                return True
                
        except Exception as e:
            logger.error(f"Error syncing user session: {str(e)}")
            return False

    def sync_user_data(self, data: Dict[str, Any]) -> bool:
        """
        Synchronize user data from auth service
        """
        try:
            with transaction_context() as session:
                user_id = data.get('id')
                if not user_id:
                    return False

                user = User.query.get(user_id)
                if not user:
                    # Create user if doesn't exist
                    user = User(
                        id=user_id,
                        email=data['email'],
                        name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                        is_active=data['is_active'],
                        is_email_verified=data['is_email_verified']
                    )
                    session.add(user)
                else:
                    # Update existing user
                    user.email = data['email']
                    user.name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
                    user.is_active = data['is_active']
                    user.is_email_verified = data['is_email_verified']

                return True
        except Exception as e:
            logger.error(f"Error syncing user data: {str(e)}")
            return False

    def revoke_user_sessions(self, user_id: int, reason: str = None) -> bool:
        """
        Handle session revocation from auth service
        """
        try:
            with transaction_context() as session:
                user = User.query.get(user_id)
                if user:
                    user.last_login_at = None
                return True
        except Exception as e:
            logger.error(f"Error revoking user sessions: {str(e)}")
            return False

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        try:
            token = request.headers.get('Authorization', '').split(' ')[1]
            payload = self.validate_token(token)
            if not payload:
                return None
                
            return User.query.get(payload.get('user_id'))
            
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None 