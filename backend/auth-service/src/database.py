"""
This module re-exports the shared database module to maintain
backward compatibility with code that imports from here.
"""

from shared.database import db, transaction, init_db

# No need to initialize another SQLAlchemy instance
# as we're using the one from the shared module 