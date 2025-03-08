import os
import sys
import logging
from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from redis import Redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for shared modules - try multiple approaches for Windows compatibility
potential_paths = [
    os.path.abspath(os.path.dirname(__file__)),  # Current directory
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')),  # Parent directory
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')),  # Grandparent directory
    '/app',  # Docker container path
    '/app/shared'  # Docker shared volume path
]

for path in potential_paths:
    if path not in sys.path:
        sys.path.append(path)
        logger.info(f"Added {path} to sys.path")

# Try multiple import patterns to handle different environments
try:
    # Try absolute import first (when PYTHONPATH includes shared)
    from shared.database import db, init_db
    from shared.middleware.error_handler import handle_api_errors
    from shared.middleware.validation import validate_schema
    from shared.middleware.rate_limiter import RateLimiter
    from shared.config import config
    logger.info("Successfully imported shared modules using absolute import")
except ImportError as e:
    logger.warning(f"Absolute import failed: {e}, trying relative import")
    try:
        # Fallback to relative path
        from backend.shared.database import db, init_db
        from backend.shared.middleware.error_handler import handle_api_errors
        from backend.shared.middleware.validation import validate_schema
        from backend.shared.middleware.rate_limiter import RateLimiter
        from backend.shared.config import config
        logger.info("Successfully imported shared modules using relative import")
    except ImportError as e:
        logger.error(f"All import approaches failed: {e}")
        logger.error(f"Current sys.path: {sys.path}")
        # We'll handle this in create_app() to provide a meaningful error message

# Import local modules
try:
    from .routes.meetings import meetings_bp
    from .routes.auth_integration import bp as auth_integration_bp
    from .routes.health import health_bp
    from .utils.migrations_manager import MigrationsManager
    from .utils.data_seeder import DataSeeder
    from .utils.auth_integration import AuthIntegration
except ImportError as e:
    logger.error(f"Failed to import local modules: {e}")
    # We'll handle this in create_app()

# Try to import APScheduler, but continue if it's not available
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    has_apscheduler = True
    logger.info("Successfully imported APScheduler")
except ImportError:
    has_apscheduler = False
    logger.warning("APScheduler not available, some features will be disabled")

# Initialize extensions
migrate = Migrate()
csrf = CSRFProtect()
rate_limiter = None
cors = CORS()
redis_client = None

def get_redis_client():
    """Get or create Redis client singleton"""
    global redis_client
    if redis_client is None:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            redis_client = Redis.from_url(redis_url)
            redis_client.ping()  # Test connection
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            redis_client = None
    return redis_client

def create_app(config_name='development', initialize_db=True):
    """Create and configure the Flask application"""
    # Import os again to ensure it's available in this function's scope
    import os
    
    app = Flask(__name__)
    
    # In case of import errors, return a minimal app that explains the issue
    import_errors = []
    
    # Check if critical modules were imported
    if 'db' not in globals():
        import_errors.append("Failed to import shared database module")
    if 'meetings_bp' not in globals():
        import_errors.append("Failed to import meetings blueprint")
    
    if import_errors:
        @app.route('/')
        def import_error():
            return jsonify({
                'status': 'error',
                'message': 'Application failed to start due to import errors',
                'errors': import_errors,
                'python_path': sys.path
            }), 500
            
        @app.route('/health')
        def minimal_health():
            return jsonify({
                'status': 'error',
                'message': 'Application is running but with import errors',
                'errors': import_errors
            }), 500
            
        return app

    # Ensure required environment variables are set
    required_env_vars = [
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'REDIS_URL',
        'SERVICE_KEY',
        'AUTH_SERVICE_URL'
    ]
    
    # Check for missing environment variables
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
    
    # Initialize database and migrations
    init_db(app)  # Using shared database initialization
    migrate.init_app(app, db)
    
    # Register error handlers
    handle_api_errors(app)
    
    # Initialize database if needed
    if initialize_db:
        with app.app_context():
            migrations_manager = MigrationsManager(app, db)
            migrations_manager.initialize_database()

            # Seed data in development
            if app.config.get("FLASK_ENV") == "development":
                data_seeder = DataSeeder(app, db)
                if not data_seeder.run_all_seeders():
                    logger.error("Failed to seed data")
    
    # Register blueprints
    app.register_blueprint(meetings_bp, url_prefix='/api/meetings')
    app.register_blueprint(auth_integration_bp, url_prefix='/api')
    
    # Initialize background tasks if APScheduler is available
    if has_apscheduler:
        try:
            from .tasks import initialize_tasks
            initialize_tasks(app)
        except ImportError:
            logger.warning("Could not import tasks modules. Background tasks disabled.")
    
    # Register health endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            with app.app_context():
                db.session.execute("SELECT 1")
            
            # Check Redis connection
            redis_status = "unavailable"
            if app.extensions.get("redis"):
                try:
                    app.extensions["redis"].ping()
                    redis_status = "connected"
                except Exception as e:
                    redis_status = f"error: {str(e)}"
            
            return {
                "status": "healthy",
                "service": "flask",
                "database": "connected",
                "redis": redis_status,
                "apscheduler": "available" if has_apscheduler else "unavailable",
                "timestamp": datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "service": "flask",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }, 500
    
    logger.info("Application initialized successfully")
    return app 