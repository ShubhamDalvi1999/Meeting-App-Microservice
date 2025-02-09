from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging
from ..database import db

logger = logging.getLogger(__name__)

T = TypeVar('T')

@contextmanager
def transaction_context():
    """
    Context manager for database transactions.
    Automatically handles commit and rollback.
    
    Usage:
        with transaction_context() as session:
            session.add(user)
    """
    try:
        yield
        current_app.db.session.commit()
    except Exception as e:
        current_app.db.session.rollback()
        raise e

def with_transaction(f: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to wrap a function in a database transaction.
    Automatically handles commit and rollback.
    
    Usage:
        @with_transaction
        def create_user(data):
            user = User(**data)
            db.session.add(user)
            return user
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> T:
        try:
            result = f(*args, **kwargs)
            current_app.db.session.commit()
            return result
        except Exception as e:
            current_app.db.session.rollback()
            raise e
    return decorated

def safe_commit() -> bool:
    """Safely commit database changes"""
    try:
        current_app.db.session.commit()
        return True
    except SQLAlchemyError as e:
        current_app.db.session.rollback()
        logger.error(f"Database commit error: {str(e)}")
        return False

def safe_add(obj: Any, auto_commit: bool = True) -> bool:
    """Safely add an object to the database"""
    try:
        current_app.db.session.add(obj)
        if auto_commit:
            return safe_commit()
        return True
    except SQLAlchemyError as e:
        current_app.db.session.rollback()
        logger.error(f"Database add error: {str(e)}")
        return False

def safe_delete(obj: Any, auto_commit: bool = True) -> bool:
    """Safely delete an object from the database"""
    try:
        current_app.db.session.delete(obj)
        if auto_commit:
            return safe_commit()
        return True
    except SQLAlchemyError as e:
        current_app.db.session.rollback()
        logger.error(f"Database delete error: {str(e)}")
        return False

def cleanup_expired_sessions() -> int:
    """
    Cleanup expired sessions from the database.
    Returns the number of sessions cleaned up.
    """
    from datetime import datetime
    from ..models.auth import UserSession
    
    try:
        count = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow(),
            UserSession.revoked == False
        ).update({
            'revoked': True,
            'revocation_reason': 'Expired'
        })
        db.session.commit()
        return count
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error cleaning up expired sessions: {str(e)}")
        raise
    finally:
        db.session.close() 