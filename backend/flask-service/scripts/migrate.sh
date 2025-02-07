#!/bin/bash

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
MAX_WAIT=60
WAIT_COUNT=0

# Parse DATABASE_URL for connection details
if [ -z "${DATABASE_URL:-}" ]; then
    error_exit "DATABASE_URL environment variable is not set"
fi

# Extract connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([^/]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\(.*\)/\1/p')

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${2:-$NC}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Error handling
error_exit() {
    log "ERROR: $1" "$RED" >&2
    exit 1
}

# Wait for database to be ready
log "Waiting for database to be ready..." "$YELLOW"
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; do
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        error_exit "Timed out waiting for database to be ready"
    fi
    WAIT_COUNT=$((WAIT_COUNT + 1))
    log "Waiting for PostgreSQL... ($WAIT_COUNT/$MAX_WAIT seconds)" "$YELLOW"
    sleep 1
done

log "Database is ready!" "$GREEN"

cd /app

# Initialize migrations if needed
if [ ! -d "migrations" ]; then
    log "Initializing migrations directory..." "$YELLOW"
    alembic init migrations || error_exit "Failed to initialize migrations"
    log "Migrations directory initialized" "$GREEN"
fi

# Run migrations
log "Running database migrations..." "$YELLOW"

# First, try to merge heads if there are multiple
if alembic -c migrations/alembic.ini heads | grep -q ","; then
    log "Multiple migration heads detected, attempting to merge..." "$YELLOW"
    alembic -c migrations/alembic.ini merge heads || error_exit "Failed to merge migration heads"
fi

# Now run the upgrade
if alembic -c migrations/alembic.ini upgrade heads; then
    log "Database migrations completed successfully!" "$GREEN"
    # Show current version
    log "Current migration version:" "$YELLOW"
    alembic -c migrations/alembic.ini current
else
    error_exit "Database migrations failed"
fi 