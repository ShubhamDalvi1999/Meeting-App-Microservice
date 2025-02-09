import logging
from flask import Flask
from sqlalchemy.exc import IntegrityError
from ..models.auth import AuthUser

logger = logging.getLogger(__name__)

class DataSeeder:
    def __init__(self, app: Flask, db):
        self.app = app
        self.db = db

    def seed_admin_user(self):
        """Seed admin user if not exists"""
        try:
            with self.app.app_context():
                if not AuthUser.query.filter_by(email='admin@example.com').first():
                    admin = AuthUser(
                        email='admin@example.com',
                        first_name='Admin',
                        last_name='User',
                        is_email_verified=True
                    )
                    admin.set_password('Admin123!')
                    self.db.session.add(admin)
                    self.db.session.commit()
                    logger.info("Admin user seeded successfully")
                    return True
                return True
        except Exception as e:
            logger.error(f"Error seeding admin user: {str(e)}")
            return False

    def run_all_seeders(self):
        """Run all data seeders"""
        try:
            success = True
            if not self.seed_admin_user():
                success = False
            return success
        except Exception as e:
            logger.error(f"Error running seeders: {str(e)}")
            return False 