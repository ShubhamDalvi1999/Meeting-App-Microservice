"""
Shared database utilities for transaction management across services.
"""
from contextlib import contextmanager
from sqlalchemy.orm import Session
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Dict, List, Union
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@contextmanager
def transaction_context(session: Session):
    """
    Context manager for database transactions.
    Commits the transaction if no exceptions occur, rolls back otherwise.
    
    Args:
        session: SQLAlchemy session object
        
    Yields:
        The session object
    """
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction error: {str(e)}")
        raise

def with_transaction(func):
    """
    Decorator for functions that need a transaction.
    Automatically commits or rolls back the transaction.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(session, *args, **kwargs):
        with transaction_context(session) as tx_session:
            return func(tx_session, *args, **kwargs)
    return wrapper

class DatabaseManager:
    """
    Database utility class for managing database operations.
    Provides a unified interface for database operations across services.
    """
    def __init__(self, db):
        self.db = db
        self.session = db.session
        self.logger = logging.getLogger(__name__)
    
    def commit(self) -> bool:
        """Safely commit database changes"""
        try:
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Database commit error: {str(e)}")
            return False
            
    def add(self, obj: Any, auto_commit: bool = True) -> bool:
        """Safely add an object to the database"""
        try:
            self.session.add(obj)
            if auto_commit:
                return self.commit()
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Database add error: {str(e)}")
            return False
            
    def delete(self, obj: Any, auto_commit: bool = True) -> bool:
        """Safely delete an object from the database"""
        try:
            self.session.delete(obj)
            if auto_commit:
                return self.commit()
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Database delete error: {str(e)}")
            return False 