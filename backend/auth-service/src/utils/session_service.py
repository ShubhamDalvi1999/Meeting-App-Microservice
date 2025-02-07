from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from flask import current_app
import logging
from ..models.auth import UserSession
from ..database import db
from .service_integration import ServiceIntegration
from .database import transaction_context, safe_commit

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self.service_integration = ServiceIntegration()

    def create_session(self, user_id: int, device_info: Optional[Dict[str, Any]] = None) -> Optional[UserSession]:
        """Create a new user session"""
        try:
            with transaction_context() as session:
                user_session = UserSession(
                    user_id=user_id,
                    device_info=device_info,
                    expires_at=datetime.utcnow() + timedelta(days=1)
                )
                session.add(user_session)
                session.flush()  # Get the session ID

                # Sync with main service
                if not self.service_integration.sync_user_session(
                    user_id, 
                    user_session.token,
                    {
                        'session_id': user_session.id,
                        'device_info': device_info,
                        'expires_at': user_session.expires_at.isoformat()
                    }
                ):
                    logger.error("Failed to sync session with main service")
                    raise Exception("Session sync failed")

                return user_session
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return None

    def get_active_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user"""
        return UserSession.query.filter(
            UserSession.user_id == user_id,
            UserSession.revoked == False,
            UserSession.expires_at > datetime.utcnow()
        ).all()

    def revoke_session(self, session_id: int, reason: str = None) -> bool:
        """Revoke a specific session"""
        try:
            with transaction_context() as session:
                user_session = UserSession.query.get(session_id)
                if not user_session:
                    return False

                user_session.revoke(reason)
                
                # Sync with main service
                if not self.service_integration.revoke_user_sessions(
                    user_session.user_id,
                    reason=f"Session {session_id} revoked: {reason}"
                ):
                    logger.error("Failed to sync session revocation with main service")
                    raise Exception("Session revocation sync failed")

                return True
        except Exception as e:
            logger.error(f"Error revoking session: {str(e)}")
            return False

    def revoke_all_user_sessions(self, user_id: int, reason: str = None) -> bool:
        """Revoke all sessions for a user"""
        try:
            with transaction_context() as session:
                UserSession.query.filter(
                    UserSession.user_id == user_id,
                    UserSession.revoked == False
                ).update({
                    'revoked': True,
                    'revoked_at': datetime.utcnow(),
                    'revocation_reason': reason
                })

                # Sync with main service
                if not self.service_integration.revoke_user_sessions(user_id, reason=reason):
                    logger.error("Failed to sync session revocations with main service")
                    raise Exception("Session revocations sync failed")

                return True
        except Exception as e:
            logger.error(f"Error revoking all sessions: {str(e)}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            with transaction_context() as session:
                result = UserSession.query.filter(
                    UserSession.expires_at < datetime.utcnow(),
                    UserSession.revoked == False
                ).update({
                    'revoked': True,
                    'revoked_at': datetime.utcnow(),
                    'revocation_reason': 'Expired'
                })

                # Sync cleanup with main service if any sessions were cleaned up
                if result > 0:
                    self.service_integration.sync_user_session(
                        None,
                        None,
                        {'cleanup_timestamp': datetime.utcnow().isoformat()}
                    )

                return result
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0

    def extend_session(self, session_id: int, duration: timedelta = None) -> bool:
        """Extend a session's expiration time"""
        if duration is None:
            duration = timedelta(days=1)

        try:
            with transaction_context() as session:
                user_session = UserSession.query.get(session_id)
                if not user_session or user_session.revoked:
                    return False

                new_expiry = datetime.utcnow() + duration
                user_session.expires_at = new_expiry

                # Sync with main service
                if not self.service_integration.sync_user_session(
                    user_session.user_id,
                    user_session.token,
                    {'expires_at': new_expiry.isoformat()}
                ):
                    logger.error("Failed to sync session extension with main service")
                    raise Exception("Session extension sync failed")

                return True
        except Exception as e:
            logger.error(f"Error extending session: {str(e)}")
            return False 