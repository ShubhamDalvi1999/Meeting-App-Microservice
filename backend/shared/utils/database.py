from functools import wraps
from typing import Any, Callable, Optional, TypeVar, List
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from contextlib import contextmanager
from shared.database import db, transaction  # Import from shared.database
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@contextmanager
def transaction_context():
    """
    Context manager for database transactions.
    Alias for shared.database.transaction to maintain compatibility.
    
    Usage:
        with transaction_context() as session:
            session.add(user)
    """
    with transaction():
        yield db.session

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
            logger.error(f"Database error in {f.__name__}: {str(e)}")
            raise
        finally:
            if db.session:
                db.session.close()
    return decorated

class DatabaseManager:
    """
    Utility class for handling database operations safely
    with automatic error handling and transactions.
    """
    def __init__(self, db_instance):
        self.db = db_instance

    def safe_commit(self) -> bool:
        """Safely commit database changes with automatic rollback on error"""
        try:
            self.db.session.commit()
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Failed to commit changes: {str(e)}")
            return False

    def safe_add(self, obj: Any, auto_commit: bool = True) -> bool:
        """Safely add an object to the database"""
        try:
            self.db.session.add(obj)
            if auto_commit:
                return self.safe_commit()
            return True
        except SQLAlchemyError as e:
            if auto_commit:
                self.db.session.rollback()
            logger.error(f"Error adding object to database: {str(e)}")
            raise

    def safe_delete(self, obj: Any, auto_commit: bool = True) -> bool:
        """Safely delete an object from the database"""
        try:
            self.db.session.delete(obj)
            if auto_commit:
                return self.safe_commit()
            return True
        except SQLAlchemyError as e:
            if auto_commit:
                self.db.session.rollback()
            logger.error(f"Error deleting object from database: {str(e)}")
            raise

    def safe_bulk_add(self, objects: List[Any], auto_commit: bool = True) -> bool:
        """Safely add multiple objects to the database"""
        try:
            self.db.session.bulk_save_objects(objects)
            if auto_commit:
                return self.safe_commit()
            return True
        except SQLAlchemyError as e:
            if auto_commit:
                self.db.session.rollback()
            logger.error(f"Error bulk adding objects to database: {str(e)}")
            raise

    def safe_bulk_delete(self, objects: List[Any], auto_commit: bool = True) -> bool:
        """Safely delete multiple objects from the database"""
        try:
            for obj in objects:
                self.db.session.delete(obj)
            if auto_commit:
                return self.safe_commit()
            return True
        except SQLAlchemyError as e:
            if auto_commit:
                self.db.session.rollback()
            logger.error(f"Error bulk deleting objects from database: {str(e)}")
            raise 