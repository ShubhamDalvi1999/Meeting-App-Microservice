import os
import sys
import logging
from flask import Flask
from flask_migrate import Migrate, upgrade
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class MigrationsManager:
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
        """Create a backup of the database before migrations"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.app.root_path, 'db_backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
            
            # Get database URL from app config
            db_url = self.app.config['SQLALCHEMY_DATABASE_URI']
            
            # Execute pg_dump
            os.system(f'pg_dump {db_url} > {backup_file}')
            logger.info(f"Database backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return None

    def run_migrations(self):
        """Run database migrations"""
        try:
            with self.app.app_context():
                logger.info("Starting database migrations...")
                # Create backup before migrations
                backup_file = self.backup_database()
                
                # Run migrations
                upgrade()
                
                logger.info("Database migrations completed successfully!")
                return True
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            if backup_file:
                logger.info(f"A backup was created at: {backup_file}")
            return False

    def verify_migrations(self):
        """Verify all migrations have been applied"""
        try:
            with self.app.app_context():
                # Check if all tables exist
                for table in self.db.metadata.tables:
                    if not self.db.engine.dialect.has_table(self.db.engine, table):
                        logger.error(f"Table {table} does not exist!")
                        return False
                logger.info("All database tables verified!")
                return True
        except Exception as e:
            logger.error(f"Error verifying migrations: {e}")
            return False

    def check_migration_status(self):
        """Check current migration status"""
        try:
            with self.app.app_context():
                from flask_migrate import current
                return current()
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return None

    def initialize_database(self):
        """Initialize database with migrations"""
        if not self.wait_for_db():
            logger.error("Could not connect to database")
            sys.exit(1)

        if not self.run_migrations():
            logger.error("Failed to run migrations")
            sys.exit(1)

        if not self.verify_migrations():
            logger.error("Failed to verify migrations")
            sys.exit(1)

        logger.info("Database initialization completed successfully!") 