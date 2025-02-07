from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_ENV_VARS = [
    'DATABASE_URL',
    'JWT_SECRET_KEY',
    'REDIS_URL'
]

# Check for required environment variables
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(","),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

try:
    # Initialize extensions
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

try:
    # Initialize Redis
    redis_client = redis.from_url(os.getenv('REDIS_URL'))
    redis_client.ping()  # Test connection
    logger.info("Redis connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    raise

# Health check endpoints
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/health/db')
def db_health_check():
    try:
        # Execute a simple query
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'message': 'Database connection successful'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'message': str(e)}), 500

@app.route('/health/redis')
def redis_health_check():
    try:
        # Try to ping Redis
        redis_client.ping()
        return jsonify({'status': 'healthy', 'message': 'Redis connection successful'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'message': str(e)}), 500

# Import and register blueprints
from .routes.auth import auth_bp
from .routes.meetings import meetings_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(meetings_bp, url_prefix='/api/meetings')

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    return jsonify({'error': 'Internal Server Error'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

logger.info("Application initialized successfully") 