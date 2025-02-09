from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from shared.database import db, init_db
from shared.middleware.error_handler import handle_api_errors
from shared.middleware.validation import validate_schema
from shared.middleware.rate_limiter import RateLimiter
from shared.config import config
from .routes.auth import auth_bp
from .utils.migrations_manager import MigrationsManager
from .utils.data_seeder import DataSeeder
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .tasks.cleanup import cleanup_expired_data
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions
migrate = Migrate()
csrf = CSRFProtect()
rate_limiter = None
cors = CORS()

def create_app(config_name='development', initialize_db=True):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Enable debug mode if FLASK_DEBUG is set
    app.debug = bool(int(os.getenv('FLASK_DEBUG', 0)))
    
    # Override config with environment variables if they exist
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['JWT_SECRET_KEY'])
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config['SQLALCHEMY_DATABASE_URI'])
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    
    # Service integration configuration
    app.config['FLASK_SERVICE_URL'] = os.getenv('FLASK_SERVICE_URL', app.config.get('FLASK_SERVICE_URL'))
    app.config['SERVICE_SYNC_ENABLED'] = os.getenv('SERVICE_SYNC_ENABLED', 'true').lower() == 'true'
    
    # Initialize rate limiter
    global rate_limiter
    rate_limiter = RateLimiter(app.config['REDIS_URL'])
    
    # CORS configuration
    cors.init_app(app)
    
    # CSRF configuration
    csrf.init_app(app)
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = True
    
    # Exempt non-browser endpoints from CSRF
    csrf.exempt(r'/api/auth/google/*')  # Google OAuth callbacks
    csrf.exempt(r'/api/auth/verify-email/*')  # Email verification links
    
    # Initialize extensions with app context
    init_db(app)  # Using shared database initialization
    migrate.init_app(app, db)
    
    # Register error handlers
    handle_api_errors(app)  # Using shared error handler

    # Initialize database if needed
    if initialize_db:
        with app.app_context():
            migrations_manager = MigrationsManager(app, db)
            migrations_manager.initialize_database()

            # Initialize data seeder
            data_seeder = DataSeeder(app, db)
            data_seeder.run_all_seeders()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Setup cleanup scheduler
    if not app.debug and app.config['FLASK_ENV'] == 'production':
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=cleanup_expired_data,
            trigger="interval",
            hours=1,
            next_run_time=datetime.now() + timedelta(minutes=5)
        )
        scheduler.start()

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"}), 200

    return app

def init_scheduler(app):
    """Initialize the background scheduler for cleanup tasks"""
    if not app.debug and app.config['FLASK_ENV'] == 'production':
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=cleanup_expired_data,
            trigger="interval",
            hours=1,
            next_run_time=datetime.now() + timedelta(minutes=5)
        )
        scheduler.start()
        return scheduler
    return None

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001) 