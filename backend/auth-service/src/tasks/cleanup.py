import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy.sql import text
from ..database import db
from ..models.auth import UserSession, EmailVerification, PasswordResetToken
from ..utils.database import transaction_context
from ..utils.session_service import SessionService
from ..utils.service_integration import ServiceIntegration

logger = logging.getLogger(__name__)

def cleanup_expired_data():
    """Cleanup expired sessions, tokens, and other temporary data"""
    try:
        start_time = datetime.utcnow()
        session_service = SessionService()
        service_integration = ServiceIntegration()
        
        logger.info("Starting cleanup of expired data")

        # Use direct SQL for more efficient deletion of expired sessions
        with transaction_context() as session:
            # Get count of sessions to be cleaned up for logging
            session_count_query = text("""
                SELECT COUNT(*) FROM user_sessions 
                WHERE expires_at < :now AND revoked = FALSE
            """)
            session_count = session.execute(
                session_count_query, 
                {"now": datetime.utcnow()}
            ).scalar() or 0
            
            # If there are sessions to clean up, process them in batches
            if session_count > 0:
                logger.info(f"Found {session_count} expired sessions to clean up")
                
                # Process in batches of 500 to avoid long-running transactions
                batch_size = 500
                batches_processed = 0
                total_processed = 0
                
                while total_processed < session_count:
                    # Update in batches
                    update_query = text("""
                        UPDATE user_sessions
                        SET revoked = TRUE,
                            revoked_at = :now,
                            revocation_reason = 'Expired'
                        WHERE id IN (
                            SELECT id FROM user_sessions
                            WHERE expires_at < :now AND revoked = FALSE
                            LIMIT :batch_size
                        )
                        RETURNING id
                    """)
                    
                    result = session.execute(
                        update_query, 
                        {
                            "now": datetime.utcnow(),
                            "batch_size": batch_size
                        }
                    )
                    
                    batch_processed = result.rowcount
                    if batch_processed == 0:
                        break  # No more to process
                        
                    total_processed += batch_processed
                    batches_processed += 1
                    
                    session.commit()  # Commit each batch
                    
                logger.info(f"Cleaned up {total_processed} expired sessions in {batches_processed} batches")
            else:
                logger.info("No expired sessions to clean up")
            
            # Cleanup expired email verifications
            expired_verifications = EmailVerification.query.filter(
                EmailVerification.expires_at < datetime.utcnow(),
                EmailVerification.is_used == False
            ).update({
                'is_used': True
            })
            
            if expired_verifications > 0:
                logger.info(f"Cleaned up {expired_verifications} expired email verifications")
            
            # Cleanup expired password reset tokens
            expired_tokens = PasswordResetToken.query.filter(
                PasswordResetToken.expires_at < datetime.utcnow(),
                PasswordResetToken.used == False
            ).update({
                'used': True
            })
            
            if expired_tokens > 0:
                logger.info(f"Cleaned up {expired_tokens} expired password reset tokens")
            
            # Sync cleanup with main service
            cleanup_data = {
                'expired_sessions': session_count,
                'expired_verifications': expired_verifications,
                'expired_tokens': expired_tokens,
                'cleanup_timestamp': datetime.utcnow().isoformat()
            }
            
            service_integration.sync_user_session(None, None, cleanup_data)
            
            # Calculate duration for monitoring
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Cleanup completed in {duration:.2f} seconds - "
                f"Cleaned up {session_count} sessions, "
                f"{expired_verifications} verifications, "
                f"{expired_tokens} reset tokens"
            )
            
            # Store metrics in Redis for monitoring
            try:
                redis_client = current_app.extensions.get('redis')
                if redis_client:
                    metrics = {
                        'expired_sessions': session_count,
                        'expired_verifications': expired_verifications,
                        'expired_tokens': expired_tokens,
                        'duration_seconds': duration,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    redis_client.hmset('metrics:last_cleanup', metrics)
                    redis_client.expire('metrics:last_cleanup', 86400)  # Keep for 24 hours
                    
                    # Store history for trend analysis
                    redis_client.lpush('metrics:cleanup_history', session_count)
                    redis_client.ltrim('metrics:cleanup_history', 0, 30)  # Keep last 30 entries
            except Exception as e:
                logger.error(f"Failed to store cleanup metrics: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        db.session.rollback() 