from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from shared.database import db, init_db
from shared.middleware.error_handler import handle_api_errors
from shared.middleware.validation import validate_schema
from shared.middleware.rate_limiter import RateLimiter
from shared.config import config
from .routes.meetings import meetings_bp
from .routes.auth_integration import auth_integration_bp
from .utils.migrations_manager import MigrationsManager
from .utils.data_seeder import DataSeeder
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions
migrate = Migrate()
csrf = CSRFProtect()
rate_limiter = None

def create_app(config_name='development', initialize_db=True):
    app = Flask(__name__)
    
    # Ensure required environment variables are set
    required_env_vars = [
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'REDIS_URL',
        'SERVICE_KEY',
        'AUTH_SERVICE_URL'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Load configuration from shared config
    app.config.from_object(config[config_name])
    
    # Ensure backup directory is configured
    app.config['BACKUP_DIR'] = os.getenv('BACKUP_DIR', os.path.join(app.root_path, 'db_backups'))
    
    # Initialize rate limiter
    global rate_limiter
    rate_limiter = RateLimiter(app.config['REDIS_URL'])
    
    # CORS configuration from shared config
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": app.config['CORS_METHODS'],
            "allow_headers": app.config['CORS_HEADERS'],
            "supports_credentials": True
        }
    })
    
    # CSRF configuration
    csrf.init_app(app)
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = True
    
    # Exempt non-browser endpoints from CSRF
    csrf.exempt(auth_integration_bp)
    
    # Initialize extensions with app context
    init_db(app)  # Using shared database initialization
    migrate.init_app(app, db)
    
    # Register error handlers from shared middleware
    handle_api_errors(app)

    # Initialize database if needed
    if initialize_db:
        with app.app_context():
            migrations_manager = MigrationsManager(app, db)
            migrations_manager.initialize_database()

            # Seed data in development
            if app.config['FLASK_ENV'] == 'development':
                data_seeder = DataSeeder(app, db)
                if not data_seeder.run_all_seeders():
                    logger.error("Failed to seed data")

    # Register blueprints
    app.register_blueprint(meetings_bp, url_prefix='/api/meetings')
    app.register_blueprint(auth_integration_bp, url_prefix='/api')

    @app.route('/health')
    def health_check():
        """Health check endpoint with service status"""
        try:
            # Check database connection
            with app.app_context():
                db.session.execute('SELECT 1')
            
            # Check Redis connection
            rate_limiter.redis.ping()
            
            return {
                'status': 'healthy',
                'service': 'flask',
                'database': 'connected',
                'redis': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'service': 'flask',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 