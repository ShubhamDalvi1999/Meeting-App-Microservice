from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging

# Import from shared modules if available, otherwise use local implementation
try:
    from shared.database import db, transaction
    from shared.utils.database import transaction_context as shared_transaction_context
    from shared.utils.database import with_transaction as shared_with_transaction
    from shared.utils.database import DatabaseManager
    
    # Re-export shared functions
    transaction_context = shared_transaction_context
    with_transaction = shared_with_transaction
    
    logger = logging.getLogger(__name__)
    logger.info("Using shared database utilities")
except ImportError as e:
    logger.warning(f"Could not import shared database modules: {e}. Using local implementation.")
    from ..database import db
    
    logger = logging.getLogger(__name__)

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
            yield db.session
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Transaction error: {str(e)}")
            raise
        finally:
            db.session.close()

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
                db.session.commit()
                return result
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error in {f.__name__}: {str(e)}")
                raise
            finally:
                db.session.close()
        return decorated

# Common database utility functions (these should work with either implementation)
def safe_commit() -> bool:
    """Safely commit database changes"""
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database commit error: {str(e)}")
        return False

def safe_add(obj: Any, auto_commit: bool = True) -> bool:
    """Safely add an object to the database"""
    try:
        db.session.add(obj)
        if auto_commit:
            return safe_commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database add error: {str(e)}")
        return False

def safe_delete(obj: Any, auto_commit: bool = True) -> bool:
    """Safely delete an object from the database"""
    try:
        db.session.delete(obj)
        if auto_commit:
            return safe_commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
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
        logger.error(f"Error cleaning up expired sessions: {str(e)}")
        raise
    finally:
        db.session.close() 