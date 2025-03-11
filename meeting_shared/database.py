from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

@contextmanager
def transaction():
    """
    Context manager for database transactions.
    Automatically handles commit/rollback based on exceptions.
    
    Usage:
        with transaction():
            db.session.add(some_model)
            db.session.add(another_model)
    """
    try:
        yield
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        raise e

# Alias for backward compatibility
transaction_context = transaction

def init_db(app):
    """Initialize the database with the app"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all() 