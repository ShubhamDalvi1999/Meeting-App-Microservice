from .auth import auth_bp
from .meetings import meetings_bp
from .health import health_bp
from .auth_integration import bp as auth_integration_bp

def register_routes(app):
    """Register all route blueprints with the Flask application.
    
    Args:
        app: The Flask application instance
    """
    # Register blueprints with appropriate URL prefixes
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(meetings_bp, url_prefix='/api/meetings')
    app.register_blueprint(auth_integration_bp, url_prefix='/api')
    
    return app