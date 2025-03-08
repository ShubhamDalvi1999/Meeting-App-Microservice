#!/bin/bash

# Wait for postgres
echo "Waiting for postgres..."
while ! pg_isready -h postgres -p 5432 -U $POSTGRES_USER -d $POSTGRES_DB; do
    echo "Postgres is unavailable - sleeping"
    sleep 1
done
echo "Postgres is up - executing command"

# Print directory structure for debugging
echo "Directory structure in /app:"
ls -la /app
echo "Directory structure in /app/shared:"
ls -la /app/shared
echo "Directory structure in /app/src:"
ls -la /app/src

# Set Python path
echo "Setting PYTHONPATH to: /app:/app/shared"
export PYTHONPATH=/app:/app/shared
echo "Environment variables:"
env | grep -E 'FLASK|DATABASE|REDIS|JWT|SERVICE|AUTH|POSTGRES|PYTHONPATH'

# Run database migrations
echo "Running database migrations..."
cd /app
flask db upgrade || echo "Warning: Migrations failed, but continuing..."

# Create a simple Flask app instead of using the problematic one
echo "Starting application with enhanced logging..."
cat > /app/app_wrapper.py << 'EOF'
import sys
import os
import logging
import traceback

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app_wrapper")
logger.setLevel(logging.DEBUG)

# Log system information
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Initial sys.path: {sys.path}")

# Ensure necessary paths are in sys.path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/shared')
logger.info(f"Updated sys.path: {sys.path}")

# Log environment variables
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

try:
    logger.info("Attempting to import src.app...")
    # Import the create_app function
    import src.app
    logger.info("Successfully imported src.app")
    
    # Check modules in src.app
    logger.info(f"Available in src.app: {dir(src.app)}")
    logger.info(f"'os' in src.app globals: {'os' in dir(src.app)}")
    
    # Monkey patch os if needed
    if 'os' not in dir(src.app):
        logger.warning("'os' not in src.app namespace, adding it...")
        src.app.os = os
    
    # Create the Flask application
    logger.info("Creating Flask application...")
    app = src.app.create_app()
    logger.info("Flask application created successfully")
    
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise
except Exception as e:
    logger.error(f"Error creating app: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

if __name__ == '__main__':
    logger.info("Running Flask application...")
    app.run(host='0.0.0.0', port=5000)
EOF

# Start the application with the wrapper
echo "Starting Gunicorn with app_wrapper.py..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 --log-level debug "app_wrapper:app" 