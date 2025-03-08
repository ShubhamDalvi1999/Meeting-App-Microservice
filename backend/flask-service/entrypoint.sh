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
export PYTHONPATH=/app:/app/shared

# Run database migrations
echo "Running database migrations..."
cd /app
flask db upgrade

# Start the application
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 8 --timeout 0 "src.app:create_app()" 