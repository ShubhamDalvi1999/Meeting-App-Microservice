import logging
from datetime import datetime, timedelta
from flask import current_app
from ..database import db
from ..models.auth import UserSession, EmailVerification, PasswordResetToken
from ..utils.database import transaction_context
from ..utils.session_service import SessionService
from ..utils.service_integration import ServiceIntegration

logger = logging.getLogger(__name__)

def cleanup_expired_data():
    """Cleanup expired sessions, tokens, and other temporary data"""
    try:
        session_service = SessionService()
        service_integration = ServiceIntegration()

        # Cleanup expired sessions
        expired_sessions = session_service.cleanup_expired_sessions()
        
        with transaction_context() as session:
            # Cleanup expired email verifications
            expired_verifications = EmailVerification.query.filter(
                EmailVerification.expires_at < datetime.utcnow(),
                EmailVerification.is_used == False
            ).update({
                'is_used': True
            })
            
            # Cleanup expired password reset tokens
            expired_tokens = PasswordResetToken.query.filter(
                PasswordResetToken.expires_at < datetime.utcnow(),
                PasswordResetToken.used == False
            ).update({
                'used': True
            })
            
            # Sync cleanup with main service
            cleanup_data = {
                'expired_sessions': expired_sessions,
                'expired_verifications': expired_verifications,
                'expired_tokens': expired_tokens,
                'cleanup_timestamp': datetime.utcnow().isoformat()
            }
            
            service_integration.sync_user_session(None, None, cleanup_data)
            
            logger.info(
                f"Cleaned up {expired_sessions} sessions, "
                f"{expired_verifications} verifications, "
                f"{expired_tokens} reset tokens"
            )
            
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise 