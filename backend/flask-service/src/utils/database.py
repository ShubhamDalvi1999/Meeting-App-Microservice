from meeting_shared.database import transaction_context
from meeting_shared.utils.database import with_transaction, DatabaseManager
from meeting_shared.middleware.validation import validate_schema
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
import logging
from meeting_shared.database import db

logger = logging.getLogger(__name__)

# Re-export shared database utilities
__all__ = ['transaction_context', 'with_transaction', 'DatabaseManager']

# Initialize database manager
db_manager = None

def get_db_manager():
    """Get or create database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(db)
    return db_manager

def safe_commit():
    """Safely commit database changes"""
    return get_db_manager().safe_commit()

def safe_add(obj, auto_commit=True):
    """Safely add an object to the database"""
    return get_db_manager().safe_add(obj, auto_commit)

def safe_delete(obj, auto_commit=True):
    """Safely delete an object from the database"""
    return get_db_manager().safe_delete(obj, auto_commit)

def safe_bulk_add(objects, auto_commit=True):
    """Safely add multiple objects to the database"""
    return get_db_manager().safe_bulk_add(objects, auto_commit)

def safe_bulk_delete(objects, auto_commit=True):
    """Safely delete multiple objects from the database"""
    return get_db_manager().safe_bulk_delete(objects, auto_commit) 