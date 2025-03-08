import os
import sys
import logging
import traceback
from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from redis import Redis

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Initializing Flask application module")
logger.debug(f"Python version: {sys.version}")
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Initial sys.path: {sys.path}")

# Log current environment variables
env_vars = {}
critical_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'REDIS_URL', 'SERVICE_KEY', 'AUTH_SERVICE_URL',
                'FLASK_APP', 'FLASK_DEBUG', 'PYTHONPATH']
for var in critical_vars:
    value = os.environ.get(var)
    if value:
        # Mask sensitive values
        if 'SECRET' in var or 'PASSWORD' in var:
            env_vars[var] = '***MASKED***'
        else:
            env_vars[var] = value
    else:
        env_vars[var] = 'NOT SET'

logger.info(f"Environment variables: {env_vars}")

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

logger.info(f"Updated sys.path: {sys.path}")

# Try multiple import patterns to handle different environments
try:
    # Try absolute import first (when PYTHONPATH includes shared)
    logger.info("Attempting to import shared modules using absolute import...")
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
        logger.info("Attempting to import shared modules using relative import...")
        from backend.shared.database import db, init_db
        from backend.shared.middleware.error_handler import handle_api_errors
        from backend.shared.middleware.validation import validate_schema
        from backend.shared.middleware.rate_limiter import RateLimiter
        from backend.shared.config import config
        logger.info("Successfully imported shared modules using relative import")
    except ImportError as e:
        logger.error(f"All import approaches failed: {e}")
        logger.error(f"Current sys.path: {sys.path}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # We'll handle this in create_app() to provide a meaningful error message

# Import local modules
try:
    logger.info("Attempting to import local modules...")
    from .routes.meetings import meetings_bp
    from .routes.auth_integration import bp as auth_integration_bp
    from .routes.health import health_bp
    from .utils.migrations_manager import MigrationsManager
    from .utils.data_seeder import DataSeeder
    from .utils.auth_integration import AuthIntegration
    logger.info("Successfully imported local modules")
except ImportError as e:
    logger.error(f"Failed to import local modules: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    # We'll handle this in create_app()

# Try to import APScheduler, but continue if it's not available
try:
    logger.info("Attempting to import APScheduler...")
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    has_apscheduler = True
    logger.info("Successfully imported APScheduler")
except ImportError as e:
    has_apscheduler = False
    logger.warning(f"APScheduler not available, some features will be disabled: {e}")

# Initialize extensions
migrate = Migrate()
csrf = CSRFProtect()
rate_limiter = None
cors = CORS()
redis_client = None

def get_redis_client():
    """Get or create Redis client singleton"""
    global redis_client
    logger.debug("get_redis_client called")
    if redis_client is None:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        logger.info(f"Initializing Redis client with URL: {redis_url.replace('redis://:', 'redis://***:')}")
        try:
            redis_client = Redis.from_url(redis_url)
            redis_client.ping()  # Test connection
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            redis_client = None
    return redis_client

def create_app(config_name='development', initialize_db=True):
    """Create and configure the Flask application"""
    # Import os again to ensure it's available in this function's scope
    import os
    logger.info(f"create_app called with config_name={config_name}, initialize_db={initialize_db}")
    logger.debug(f"'os' module is available in create_app scope: {os is not None}")
    
    try:
        app = Flask(__name__)
        logger.info("Flask app instance created")
        
        # In case of import errors, return a minimal app that explains the issue
        import_errors = []
        
        # Check if critical modules were imported
        if 'db' not in globals():
            import_errors.append("Failed to import shared database module")
        if 'meetings_bp' not in globals():
            import_errors.append("Failed to import meetings blueprint")
        
        if import_errors:
            logger.error(f"Critical import errors detected: {import_errors}")
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
        
        logger.info("Checking required environment variables...")
        
        # Check for missing environment variables
        missing_vars = []
        for var in required_env_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
                logger.error(f"Required environment variable not set: {var}")
            else:
                if 'SECRET' in var or 'PASSWORD' in var:
                    logger.info(f"Environment variable {var} is set")
                else:
                    logger.info(f"Environment variable {var}={value}")
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Load configuration from shared config
        logger.info(f"Loading configuration from config[{config_name}]")
        app.config.from_object(config[config_name])
        
        # Ensure backup directory is configured
        backup_dir = os.environ.get('BACKUP_DIR', os.path.join(app.root_path, 'db_backups'))
        logger.info(f"Setting backup directory to: {backup_dir}")
        app.config['BACKUP_DIR'] = backup_dir
        
        # Initialize rate limiter
        logger.info("Initializing rate limiter...")
        global rate_limiter
        rate_limiter = RateLimiter(app.config['REDIS_URL'])
        
        # Initialize Redis client and store in app extensions
        logger.info("Initializing Redis client...")
        redis = get_redis_client()
        if redis:
            app.extensions['redis'] = redis
            logger.info("Redis client added to app extensions")
        else:
            logger.warning("Redis client initialization failed")
        
        # Configure cache settings
        logger.info("Configuring cache settings...")
        app.config['CACHE_TYPE'] = 'redis'
        app.config['CACHE_REDIS_URL'] = app.config['REDIS_URL']
        
        # CORS configuration from shared config
        logger.info("Configuring CORS...")
        CORS(app, resources={
            r"/api/*": {
                "origins": app.config['CORS_ORIGINS'],
                "methods": app.config['CORS_METHODS'],
                "allow_headers": app.config['CORS_HEADERS'],
                "supports_credentials": True
            }
        })
        logger.info(f"CORS configured with origins: {app.config['CORS_ORIGINS']}")
        
        # CSRF configuration
        logger.info("Configuring CSRF protection...")
        csrf.init_app(app)
        app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
        app.config['WTF_CSRF_SSL_STRICT'] = True
        
        # Exempt non-browser endpoints from CSRF
        logger.info("Exempting auth_integration_bp from CSRF protection")
        csrf.exempt(auth_integration_bp)
        
        # Initialize database and migrations
        logger.info("Initializing database and migrations...")
        init_db(app)  # Using shared database initialization
        migrate.init_app(app, db)
        
        # Register error handlers
        logger.info("Registering error handlers...")
        handle_api_errors(app)
        
        # Initialize database if needed
        if initialize_db:
            logger.info("Initializing database...")
            with app.app_context():
                try:
                    migrations_manager = MigrationsManager(app, db)
                    migrations_manager.initialize_database()
                    logger.info("Database initialized successfully")

                    # Seed data in development
                    if app.config.get("FLASK_ENV") == "development":
                        logger.info("Seeding development data...")
                        data_seeder = DataSeeder(app, db)
                        if not data_seeder.run_all_seeders():
                            logger.error("Failed to seed data")
                        else:
                            logger.info("Data seeding completed successfully")
                except Exception as e:
                    logger.error(f"Database initialization error: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Register blueprints
        logger.info("Registering blueprints...")
        app.register_blueprint(meetings_bp, url_prefix='/api/meetings')
        app.register_blueprint(auth_integration_bp, url_prefix='/api')
        logger.info("Blueprints registered successfully")
        
        # Initialize background tasks if APScheduler is available
        if has_apscheduler:
            try:
                logger.info("Initializing background tasks...")
                from .tasks import initialize_tasks
                initialize_tasks(app)
                logger.info("Background tasks initialized successfully")
            except ImportError as e:
                logger.warning(f"Could not import tasks modules. Background tasks disabled: {e}")
        
        # Register health endpoint
        logger.info("Registering health endpoint...")
        @app.route("/health")
        def health_check():
            """Health check endpoint"""
            try:
                # Check database connection
                with app.app_context():
                    db.session.execute("SELECT 1")
                logger.debug("Database health check: OK")
                
                # Check Redis connection
                redis_status = "unavailable"
                if app.extensions.get("redis"):
                    try:
                        app.extensions["redis"].ping()
                        redis_status = "connected"
                        logger.debug("Redis health check: OK")
                    except Exception as e:
                        redis_status = f"error: {str(e)}"
                        logger.error(f"Redis health check failed: {str(e)}")
                
                health_data = {
                    "status": "healthy",
                    "service": "flask",
                    "database": "connected",
                    "redis": redis_status,
                    "apscheduler": "available" if has_apscheduler else "unavailable",
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.debug(f"Health check response: {health_data}")
                return health_data, 200
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {
                    "status": "unhealthy",
                    "service": "flask",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }, 500
        
        logger.info("Application initialized successfully")
        return app
        
    except Exception as e:
        logger.error(f"Error in create_app: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise 