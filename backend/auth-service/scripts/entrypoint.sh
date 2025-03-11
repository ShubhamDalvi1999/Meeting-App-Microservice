#!/bin/bash
set -e

echo "Waiting for auth-db..."
while ! pg_isready -h auth-db -p 5432 -U $AUTH_DB_USER; do
    sleep 1
done
echo "Postgres is up - executing command"

# List directory structure for debugging
echo "Directory structure in /app:"
ls -la /app

# Check if meeting_shared is properly mounted
if [ ! -d "/app/meeting_shared" ] || [ -z "$(ls -A /app/meeting_shared)" ]; then
    echo "WARNING: Shared modules not properly mounted. Volume mount issue possible."
fi

# Run migrations if they exist
if [ -f "migrations/env.py" ]; then
    echo "Running database migrations..."
    flask db upgrade
else
    echo "Warning: Migrations failed, but continuing..."
fi

# Start the application
exec gunicorn --bind 0.0.0.0:5001 \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    "src.app:create_app()" 