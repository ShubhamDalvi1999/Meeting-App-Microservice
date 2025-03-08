"""
Main application factory for the Auth Service.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

# Configure import paths for shared modules
shared_module_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../backend'))
]

for path in shared_module_paths:
    if path not in sys.path:
        sys.path.append(path)

# Import core modules
from flask import Flask, jsonify, g
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Try to import from shared modules with fallbacks
try:
    from shared.config import get_config
except ImportError:
    from core.config import get_config

try:
    from shared.logging import setup_logging
except ImportError:
    from core.logging import setup_logging

try:
    from shared.middleware import register_middleware
except ImportError:
    from core.middleware import register_middleware

# Import local modules
from core import (
    db, jwt, migrate, mail, limiter, csrf,
    register_error_handlers, register_cli_commands
)
from api.auth import auth_bp
from api.users import users_bp

# Configure logger
logger = logging.getLogger(__name__)

def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: Configuration environment name (default: from FLASK_ENV)

    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config(config_name or os.getenv('FLASK_ENV', 'development'))
    app.config.from_object(config_obj)
    
    # Override database URL from environment if provided
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'AUTH_DATABASE_URL', 
        app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///auth.db')
    )
    
    # Configure logging
    setup_logging(
        app=app, 
        service_name='auth-service',
        log_level=app.config.get('LOG_LEVEL', 'INFO')
    )
    
    # Configure proxy settings for running behind a reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
    
    # Register middleware
    register_middleware(app)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    
    # Exempt the entire auth blueprint from CSRF protection
    # This includes OAuth callbacks, token endpoints, etc.
    csrf.exempt(auth_bp)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Add healthcheck endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for the auth service."""
        health_data = {
            'status': 'ok',
            'service': 'auth-service',
            'version': os.getenv('VERSION', '0.1.0'),
            'request_id': getattr(g, 'request_id', 'none')
        }
        
        # Add database status check
        try:
            db.session.execute('SELECT 1')
            health_data['database'] = 'ok'
        except Exception as e:
            health_data['database'] = 'error'
            health_data['database_error'] = str(e)
            health_data['status'] = 'degraded'
            
        return jsonify(health_data)
    
    # Log application startup
    logger.info(f"Auth service started in {app.config.get('ENV')} mode")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001) 