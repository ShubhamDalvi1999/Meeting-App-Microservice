#!/bin/bash

set -e  # Exit on error

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

# Wait for PostgreSQL
wait_for_postgres() {
    local retries=30
    local count=0
    log "Waiting for PostgreSQL to be ready..." "$YELLOW"
    
    until pg_isready -h postgres -U dev_user -d meetingapp > /dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -ge $retries ]; then
            error_exit "Timeout waiting for PostgreSQL"
        fi
        log "Waiting for PostgreSQL... ($count/$retries)" "$YELLOW"
        sleep 2
    done
    log "PostgreSQL is ready!" "$GREEN"
}

# Wait for Redis
wait_for_redis() {
    local retries=30
    local count=0
    log "Waiting for Redis to be ready..." "$YELLOW"
    
    until redis-cli -h redis -a dev-redis-123 ping > /dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -ge $retries ]; then
            error_exit "Timeout waiting for Redis"
        fi
        log "Waiting for Redis... ($count/$retries)" "$YELLOW"
        sleep 2
    done
    log "Redis is ready!" "$GREEN"
}

# Initialize database
init_database() {
    log "Checking database initialization..." "$YELLOW"
    
    # Check if migrations directory exists
    if [ ! -d "migrations" ]; then
        log "Initializing migrations directory..." "$YELLOW"
        flask db init || error_exit "Failed to initialize migrations"
        log "Migrations directory initialized" "$GREEN"
    fi
    
    # Check current migration status
    log "Checking current migration status..." "$YELLOW"
    if ! flask db current > /dev/null 2>&1; then
        log "No migrations found, creating initial migration..." "$YELLOW"
        flask db migrate -m "initial" || error_exit "Failed to create initial migration"
        log "Initial migration created" "$GREEN"
    fi
}

# Apply migrations
apply_migrations() {
    log "Applying database migrations..." "$YELLOW"
    
    # Run migrations
    if flask db upgrade; then
        log "Database migrations completed successfully!" "$GREEN"
        # Show current version
        log "Current migration version:" "$YELLOW"
        flask db current
        # Show migration history
        log "Migration history:" "$YELLOW"
        flask db history
    else
        error_exit "Database migrations failed"
    fi
}

# Verify database
verify_database() {
    log "Running database verification..." "$YELLOW"
    
    # Test database connection
    if python -c "
from src import app, db
with app.app_context():
    try:
        db.session.execute('SELECT 1')
        print('Database verification successful')
    except Exception as e:
        print(f'Database verification failed: {str(e)}')
        exit(1)
"; then
        log "Database verification completed successfully!" "$GREEN"
    else
        error_exit "Database verification failed"
    fi
}

# Main execution
main() {
    export FLASK_APP=src
    
    # Wait for dependencies
    wait_for_postgres
    wait_for_redis
    
    # Initialize and migrate database
    init_database
    apply_migrations
    verify_database
    
    log "Database initialization and migration completed successfully!" "$GREEN"
}

# Run main function
main 