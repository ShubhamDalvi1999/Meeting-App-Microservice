from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import sys
import os
import logging
from datetime import datetime, timedelta

# Add the current directory to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Try to import from local shared directory first
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared')))
    from database import db, init_db
    from middleware.error_handler import handle_api_errors
    from middleware.validation import validate_schema
    from middleware.rate_limiter import RateLimiter
    from config import config
    print("Successfully imported shared modules from local shared directory")
except ImportError:
    # Fall back to parent shared directory
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../shared')))
    from shared.database import db, init_db
    from shared.middleware.error_handler import handle_api_errors
    from shared.middleware.validation import validate_schema
    from shared.middleware.rate_limiter import RateLimiter
    from shared.config import config
    print("Successfully imported shared modules from parent shared directory")

# Import APScheduler if available
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    has_apscheduler = True
    print("APScheduler is available")
except ImportError:
    has_apscheduler = False
    print("APScheduler not available, some features will be disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions
migrate = Migrate()
csrf = CSRFProtect()
rate_limiter = None

# Import blueprints
from .routes.meetings import meetings_bp
from .routes.auth_integration import bp as auth_integration_bp
from .routes.health import health_bp

# Import database management
from .utils.migrations_manager import MigrationsManager
from .utils.data_seeder import DataSeeder
from .utils.auth_integration import AuthIntegration

# Initialize Redis client (will be used for caching and rate limiting)
from redis import Redis
redis_client = None

def get_redis_client():
    """Get or create Redis client singleton"""
    global redis_client
    if redis_client is None:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        try:
            redis_client = Redis.from_url(redis_url)
            redis_client.ping()  # Test connection
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            redis_client = None
    return redis_client

def create_app(config_name='development', initialize_db=True):
    # os is now imported at the top of the file
    app = Flask(__name__)
    
    # Ensure required environment variables are set
    required_env_vars = [
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'REDIS_URL',
        'SERVICE_KEY',
        'AUTH_SERVICE_URL'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Load configuration from shared config
    app.config.from_object(config[config_name])
    
    # Ensure backup directory is configured
    app.config['BACKUP_DIR'] = os.environ.get('BACKUP_DIR', os.path.join(app.root_path, 'db_backups'))
    
    # Initialize rate limiter
    global rate_limiter
    rate_limiter = RateLimiter(app.config['REDIS_URL'])
    
    # Initialize Redis client and store in app extensions
    redis = get_redis_client()
    if redis:
        app.extensions['redis'] = redis
    
    # Configure cache settings
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    app.config['CACHE_KEY_PREFIX'] = 'flask_cache_'
    app.config['CACHE_REDIS_URL'] = app.config['REDIS_URL']
    
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
    app.register_blueprint(health_bp, url_prefix='/api')  # Health checks

    # Initialize background tasks if APScheduler is available
    if has_apscheduler:
        scheduler = BackgroundScheduler()
        
        # Import tasks here to avoid circular imports
        from .tasks.cleanup import cleanup_expired_meetings
        from .tasks.metrics import update_system_metrics
        
        # Add cleanup job to run every 6 hours
        scheduler.add_job(
            func=cleanup_expired_meetings,
            trigger=IntervalTrigger(hours=6),
            id='cleanup_meetings',
            name='Clean up expired meetings',
            replace_existing=True
        )
        
        # Add metrics collection job to run every 5 minutes
        scheduler.add_job(
            func=update_system_metrics,
            trigger=IntervalTrigger(minutes=5),
            id='update_metrics',
            name='Update system metrics',
            replace_existing=True
        )
        
        # Add token cache cleanup job to run every hour
        def cleanup_token_cache():
            with app.app_context():
                auth_integration = AuthIntegration()
                removed = auth_integration.cleanup_token_cache()
                logger.info(f"Cleaned up {removed} expired token cache entries")
                
        scheduler.add_job(
            func=cleanup_token_cache,
            trigger=IntervalTrigger(hours=1),
            id='cleanup_token_cache',
            name='Clean up expired token cache entries',
            replace_existing=True
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Background scheduler started with cleanup and metrics jobs")

    @app.route('/health')
    def quick_health_check():
        """Simple health check endpoint for load balancers"""
        try:
            # Check database connection
            with app.app_context():
                db.session.execute('SELECT 1')
            
            # Check Redis connection
            redis_status = "unavailable"
            if app.extensions.get('redis'):
                try:
                    app.extensions['redis'].ping()
                    redis_status = "connected"
                except:
                    redis_status = "error"
            
            return {
                'status': 'healthy',
                'service': 'flask',
                'database': 'connected',
                'redis': redis_status,
                'apscheduler': 'available' if has_apscheduler else 'unavailable',
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 