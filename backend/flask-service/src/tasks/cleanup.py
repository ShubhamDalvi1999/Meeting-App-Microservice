import logging
from datetime import datetime, timedelta, timezone
from flask import current_app
from sqlalchemy import text
from ..database import db
from ..models.meeting import Meeting
from ..models.meeting_audit_log import MeetingAuditLog

logger = logging.getLogger(__name__)

def cleanup_expired_meetings():
    """
    Cleanup meetings that have ended but not marked as ended.
    Also cleans up stale meeting resources.
    """
    try:
        logger.info("Starting cleanup of expired meetings")
        start_time = datetime.now(timezone.utc)
        
        with current_app.app_context():
            # Find meetings that have passed their end time but not marked as ended
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(minutes=30)  # Give 30 minute grace period
            
            # Find meetings to mark as ended
            expired_meetings = Meeting.query.filter(
                Meeting.end_time < cutoff_time,
                Meeting.ended_at.is_(None),
                Meeting.is_cancelled == False
            ).all()
            
            if expired_meetings:
                logger.info(f"Found {len(expired_meetings)} expired meetings to cleanup")
                
                for meeting in expired_meetings:
                    meeting.ended_at = meeting.end_time  # Use the scheduled end time
                    
                    # Log the auto-end
                    audit_log = MeetingAuditLog(
                        meeting_id=meeting.id,
                        user_id=meeting.created_by,
                        action='auto_ended',
                        details={
                            'reason': 'Meeting ended automatically after scheduled end time',
                            'ended_at': meeting.end_time.isoformat(),
                            'cleanup_time': current_time.isoformat()
                        }
                    )
                    db.session.add(audit_log)
                
                db.session.commit()
                logger.info(f"Successfully marked {len(expired_meetings)} meetings as ended")
                
                # Invalidate caches for affected users
                redis_client = current_app.extensions.get('redis')
                if redis_client:
                    for meeting in expired_meetings:
                        redis_client.delete(f"meetings:user:{meeting.created_by}")
                        redis_client.delete(f"meetings:user:{meeting.created_by}:active:true")
                        redis_client.delete(f"meetings:user:{meeting.created_by}:active:false")
            else:
                logger.info("No expired meetings to cleanup")
            
            # Archive old meetings (older than 6 months)
            archive_cutoff = current_time - timedelta(days=180)
            meetings_to_archive = Meeting.query.filter(
                Meeting.ended_at < archive_cutoff,
                Meeting.is_archived == False
            ).all()
            
            if meetings_to_archive:
                logger.info(f"Found {len(meetings_to_archive)} old meetings to archive")
                
                for meeting in meetings_to_archive:
                    meeting.is_archived = True
                    meeting.archived_at = current_time
                    
                    # Log the archiving
                    audit_log = MeetingAuditLog(
                        meeting_id=meeting.id,
                        user_id=meeting.created_by,
                        action='archived',
                        details={
                            'reason': 'Meeting archived automatically after 6 months',
                            'archived_at': current_time.isoformat()
                        }
                    )
                    db.session.add(audit_log)
                
                db.session.commit()
                logger.info(f"Successfully archived {len(meetings_to_archive)} meetings")
            else:
                logger.info("No old meetings to archive")
            
            # Calculate duration for monitoring
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Meeting cleanup completed in {duration:.2f} seconds")
            
            # Store metrics in Redis
            try:
                redis_client = current_app.extensions.get('redis')
                if redis_client:
                    metrics = {
                        'expired_meetings': len(expired_meetings),
                        'archived_meetings': len(meetings_to_archive),
                        'duration_seconds': duration,
                        'timestamp': current_time.isoformat()
                    }
                    redis_client.hmset('metrics:last_meeting_cleanup', metrics)
                    redis_client.expire('metrics:last_meeting_cleanup', 86400)  # 24 hours
            except Exception as e:
                logger.error(f"Failed to store cleanup metrics: {str(e)}")
                
            return {
                'expired_meetings': len(expired_meetings),
                'archived_meetings': len(meetings_to_archive),
                'duration_seconds': duration
            }
    
    except Exception as e:
        logger.error(f"Error during meeting cleanup: {str(e)}")
        if 'db' in locals() and db.session:
            db.session.rollback()
        return {'error': str(e)} 