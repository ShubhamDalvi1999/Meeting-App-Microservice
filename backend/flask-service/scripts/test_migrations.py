#!/usr/bin/env python
import os
import sys
import logging
import subprocess
import docker
import psycopg2
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationTester:
    def __init__(self, migrations_dir, app_dir):
        self.migrations_dir = migrations_dir
        self.app_dir = app_dir
        self.docker_client = docker.from_env()
        self.test_db_name = f"test_migrations_{int(time.time())}"
        self.container = None

    def setup_test_database(self):
        """Create a temporary PostgreSQL container for testing"""
        try:
            logger.info("Setting up test database container...")
            self.container = self.docker_client.containers.run(
                'postgres:15-alpine',
                environment={
                    'POSTGRES_DB': self.test_db_name,
                    'POSTGRES_USER': 'test_user',
                    'POSTGRES_PASSWORD': 'test_password'
                },
                ports={'5432/tcp': None},
                detach=True
            )

            # Wait for container to be ready
            time.sleep(5)
            port = self.container.ports['5432/tcp'][0]['HostPort']
            
            return f"postgresql://test_user:test_password@localhost:{port}/{self.test_db_name}"
        except Exception as e:
            logger.error(f"Failed to setup test database: {e}")
            self.cleanup()
            sys.exit(1)

    def test_migration(self, migration_id):
        """Test a specific migration"""
        try:
            # Set up test environment
            database_url = self.setup_test_database()
            os.environ['DATABASE_URL'] = database_url

            logger.info(f"Testing migration: {migration_id}")

            # Run migrations up to the target
            result = subprocess.run(
                ['flask', 'db', 'upgrade', migration_id],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Migration upgrade failed: {result.stderr}")
                return False

            # Test downgrade
            result = subprocess.run(
                ['flask', 'db', 'downgrade', '-1'],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Migration downgrade failed: {result.stderr}")
                return False

            # Test upgrade again
            result = subprocess.run(
                ['flask', 'db', 'upgrade'],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Second migration upgrade failed: {result.stderr}")
                return False

            logger.info(f"Migration {migration_id} tested successfully!")
            return True

        except Exception as e:
            logger.error(f"Error testing migration: {e}")
            return False
        finally:
            self.cleanup()

    def test_all_migrations(self):
        """Test all migrations in sequence"""
        try:
            database_url = self.setup_test_database()
            os.environ['DATABASE_URL'] = database_url

            logger.info("Testing all migrations in sequence...")

            # Get list of migrations
            result = subprocess.run(
                ['flask', 'db', 'history'],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to get migration history: {result.stderr}")
                return False

            migrations = [
                line.split(' ')[0] 
                for line in result.stdout.split('\n') 
                if line.strip() and not line.startswith('>')
            ]

            # Test each migration
            for migration_id in migrations:
                logger.info(f"Testing migration {migration_id}...")
                
                # Upgrade to this migration
                result = subprocess.run(
                    ['flask', 'db', 'upgrade', migration_id],
                    cwd=self.app_dir,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    logger.error(f"Failed to upgrade to {migration_id}: {result.stderr}")
                    return False

                # Verify database state
                if not self.verify_database_state():
                    logger.error(f"Database verification failed after migration {migration_id}")
                    return False

            logger.info("All migrations tested successfully!")
            return True

        except Exception as e:
            logger.error(f"Error testing migrations: {e}")
            return False
        finally:
            self.cleanup()

    def verify_database_state(self):
        """Verify database state after migration"""
        try:
            # Run application's verification logic
            result = subprocess.run(
                ['python', '-c', 'from src.app import create_app; app = create_app(); app.test_client()'],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False

    def cleanup(self):
        """Clean up test environment"""
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
                logger.info("Test database container cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up container: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_migrations.py <app_directory> [migration_id]")
        sys.exit(1)

    app_dir = sys.argv[1]
    migrations_dir = os.path.join(app_dir, 'migrations')

    if not os.path.exists(migrations_dir):
        print(f"Error: Migrations directory not found in {app_dir}")
        sys.exit(1)

    tester = MigrationTester(migrations_dir, app_dir)

    if len(sys.argv) > 2:
        # Test specific migration
        success = tester.test_migration(sys.argv[2])
    else:
        # Test all migrations
        success = tester.test_all_migrations()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 