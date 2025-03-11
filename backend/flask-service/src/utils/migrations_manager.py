import os
import sys
import logging
from flask import Flask
from flask_migrate import Migrate, upgrade, downgrade, current
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import time
from datetime import datetime
from meeting_shared.utils.migrations_manager import MigrationsManager as SharedMigrationsManager

logger = logging.getLogger(__name__)

class MigrationsManager(SharedMigrationsManager):
    def __init__(self, app: Flask, db, max_retries=5, retry_interval=5):
        self.app = app
        self.db = db
        self.migrate = Migrate(app, db)
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.migration_history = []

    def wait_for_db(self):
        """Wait for database to be ready"""
        logger.info("Waiting for database...")
        for attempt in range(self.max_retries):
            try:
                with self.app.app_context():
                    self.db.session.execute(text('SELECT 1'))
                logger.info("Database is ready!")
                return True
            except OperationalError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Database connection failed after {self.max_retries} attempts: {e}")
                    return False
                logger.warning(f"Database not ready (attempt {attempt + 1}/{self.max_retries}), waiting...")
                time.sleep(self.retry_interval)

    def backup_database(self):
        """Create a database backup before migrations"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"backup_{timestamp}.sql"
            backup_path = os.path.join(self.app.config['BACKUP_DIR'], backup_file)
            
            # Ensure backup directory exists
            os.makedirs(self.app.config['BACKUP_DIR'], exist_ok=True)
            
            # Create backup using pg_dump
            os.system(f"pg_dump {self.app.config['SQLALCHEMY_DATABASE_URI']} > {backup_path}")
            logger.info(f"Database backup created: {backup_file}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return None

    def restore_database(self, backup_path):
        """Restore database from backup"""
        try:
            os.system(f"psql {self.app.config['SQLALCHEMY_DATABASE_URI']} < {backup_path}")
            logger.info("Database restored from backup")
            return True
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False

    def run_migrations(self):
        """Run database migrations with safety checks"""
        try:
            with self.app.app_context():
                # Get current migration version
                current_version = current(self.app)
                logger.info(f"Current migration version: {current_version}")

                # Create backup before migrations
                backup_path = self.backup_database()
                if not backup_path:
                    logger.error("Failed to create backup, aborting migrations")
                    return False

                # Run migrations
                logger.info("Starting database migrations...")
                upgrade()
                
                # Verify migrations
                if not self.verify_migrations():
                    logger.error("Migration verification failed, initiating rollback...")
                    if self.restore_database(backup_path):
                        logger.info("Successfully rolled back to previous state")
                    else:
                        logger.error("Failed to rollback, manual intervention required")
                    return False

                logger.info("Database migrations completed successfully!")
                return True
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            return False

    def verify_migrations(self):
        """Verify all migrations have been applied correctly"""
        try:
            with self.app.app_context():
                # Check if all tables exist
                for table in self.db.metadata.tables:
                    if not self.db.engine.dialect.has_table(self.db.engine, table):
                        logger.error(f"Table {table} does not exist!")
                        return False

                # Verify table constraints
                for table_name in self.db.metadata.tables:
                    result = self.db.session.execute(
                        text(f"SELECT conname FROM pg_constraint WHERE conrelid = '{table_name}'::regclass")
                    ).fetchall()
                    if not result:
                        logger.warning(f"No constraints found for table {table_name}")

                logger.info("All database tables and constraints verified!")
                return True
        except Exception as e:
            logger.error(f"Error verifying migrations: {e}")
            return False

    def check_migration_status(self):
        """Check and log migration status"""
        try:
            with self.app.app_context():
                current_version = current(self.app)
                logger.info(f"Current migration version: {current_version}")
                
                # Get all migration versions
                migrations_dir = os.path.join(os.path.dirname(self.app.root_path), 'migrations', 'versions')
                available_migrations = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
                
                logger.info(f"Available migrations: {len(available_migrations)}")
                return True
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return False

    def initialize_database(self):
        """Initialize database with migrations and verify integrity"""
        if not self.wait_for_db():
            logger.error("Could not connect to database")
            sys.exit(1)

        if not self.check_migration_status():
            logger.error("Failed to check migration status")
            sys.exit(1)

        if not self.run_migrations():
            logger.error("Failed to run migrations")
            sys.exit(1)

        logger.info("Database initialization completed successfully!")

# Re-export the shared MigrationsManager
__all__ = ['MigrationsManager'] 