"""
Auth service application factory.
"""

import os
import logging
import random
import string

# Patch werkzeug.security.gen_salt to avoid secrets.choice issue
import werkzeug.security
def patched_gen_salt(length):
    """Generate a random string of SALT_CHARS with specified length."""
    if length <= 0:
        raise ValueError('Salt length must be positive')
    return ''.join(random.choice(werkzeug.security.SALT_CHARS) for _ in range(length))
werkzeug.security.gen_salt = patched_gen_salt

from flask import Flask, jsonify, g, current_app
from meeting_shared.config import get_config
from meeting_shared.shared_logging import setup_logging
from meeting_shared.middleware import register_middleware
from meeting_shared.database import init_db, db

logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Create Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name or os.getenv('FLASK_ENV', 'default'))
    app.config.from_object(config)
    logger.info(f"Initialized with configuration: {config_name or 'default'}")
    
    # Setup logging first
    setup_logging(app)
    logger.info("Logging configured")
    
    # Register middleware (before routes)
    register_middleware(app)
    logger.info("Middleware registered")
    
    # Initialize database
    init_db(app)  # This initializes the global db instance
    app.db = db   # Also store it on the app for easy access
    logger.info("Database initialized")
    
    # Register health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint with database verification."""
        status = "healthy"
        database_status = "available"
        
        # Verify database connection
        try:
            # Use current_app context to ensure we're using the correct app context
            db.session.execute('SELECT 1')
            status_code = 200
        except Exception as e:
            logger.error(f"Health check database error: {str(e)}")
            database_status = "unavailable"
            status = "degraded"
            status_code = 500
            
        return jsonify({
            'status': status,
            'service': app.config.get('APP_NAME', 'auth-service'),
            'database': database_status,
            'request_id': g.get('request_id', 'none')
        }), status_code
    
    # Register blueprints here
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    logger.info("Auth service initialization sequence complete")
    logger.info(f"Registered routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
    
    return app 