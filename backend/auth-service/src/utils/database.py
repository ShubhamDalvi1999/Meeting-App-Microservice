from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from ..database import db

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
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Transaction error: {str(e)}")
        raise
    finally:
        db.session.close()

def with_transaction(f: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle database transactions and rollback on error.
    
    Usage:
        @with_transaction
        def my_db_function():
            # Your database operations here
            pass
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> T:
        try:
            result = f(*args, **kwargs)
            if db.session.is_active:
                db.session.commit()
            return result
        except Exception as e:
            if db.session.is_active:
                db.session.rollback()
            current_app.logger.error(f"Database error in {f.__name__}: {str(e)}")
            raise
        finally:
            db.session.close()
    return decorated

def safe_commit() -> bool:
    """
    Safely commit database changes with automatic rollback on error.
    Returns True if commit was successful, False otherwise.
    """
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error during database commit: {str(e)}")
        raise
    finally:
        db.session.close()

def safe_add(obj: Any, auto_commit: bool = True) -> bool:
    """
    Safely add an object to the database session.
    
    Args:
        obj: The object to add
        auto_commit: Whether to commit immediately
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db.session.add(obj)
        if auto_commit:
            db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding object to database: {str(e)}")
        raise
    finally:
        if auto_commit:
            db.session.close()

def safe_delete(obj: Any, auto_commit: bool = True) -> bool:
    """
    Safely delete an object from the database.
    
    Args:
        obj: The object to delete
        auto_commit: Whether to commit immediately
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db.session.delete(obj)
        if auto_commit:
            db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting object from database: {str(e)}")
        raise
    finally:
        if auto_commit:
            db.session.close()

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