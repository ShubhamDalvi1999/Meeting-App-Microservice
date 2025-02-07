#!/bin/bash

set -e  # Exit on error
set -u  # Exit on undefined variable

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

# Check if message was provided
if [ "$#" -ne 1 ]; then
    error_exit "Usage: $0 \"migration message\""
fi

MIGRATION_MESSAGE="$1"

# Validate migration message format
if [[ ! $MIGRATION_MESSAGE =~ ^[a-z0-9_]+$ ]]; then
    error_exit "Migration message must contain only lowercase letters, numbers, and underscores"
fi

# Set environment variables
export FLASK_APP=src

# Create timestamp for filename
TIMESTAMP=$(date +'%Y_%m_%d_%H%M%S')
MIGRATION_NAME="${TIMESTAMP}_${MIGRATION_MESSAGE}"

# Create migration
log "Creating migration: $MIGRATION_MESSAGE" "$YELLOW"
if flask db revision --autogenerate -m "$MIGRATION_MESSAGE"; then
    log "Migration created successfully" "$GREEN"
    
    # Find the latest migration file
    LATEST_MIGRATION=$(ls -t migrations/versions/*.py | head -n 1)
    if [ -n "$LATEST_MIGRATION" ]; then
        log "Latest migration file: $LATEST_MIGRATION" "$YELLOW"
        
        # Validate the migration
        log "Validating migration..." "$YELLOW"
        if python scripts/migration_validator.py "migrations/versions"; then
            log "Migration validation successful" "$GREEN"
            
            # Show migration contents
            log "Migration contents:" "$YELLOW"
            echo "----------------------------------------"
            cat "$LATEST_MIGRATION"
            echo "----------------------------------------"
            
            # Reminder about testing
            log "IMPORTANT: Remember to:" "$YELLOW"
            log "1. Review the generated migration file" "$YELLOW"
            log "2. Test the upgrade path: flask db upgrade" "$YELLOW"
            log "3. Test the downgrade path: flask db downgrade" "$YELLOW"
            log "4. Commit both model changes and migration file" "$YELLOW"
        else
            error_exit "Migration validation failed. Please fix the issues and try again."
        fi
    else
        error_exit "Could not find the generated migration file"
    fi
else
    error_exit "Failed to create migration"
fi

# Make the migration file executable
chmod +x "$LATEST_MIGRATION"

# Success message
log "Migration creation completed successfully!" "$GREEN" 