#!/bin/bash
# migrate.sh - Database migration management for the meeting application

# Initialize flags
SHOW_CURRENT=false
UPGRADE=false
MERGE=false
FORCE_INIT=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --show-current)
      SHOW_CURRENT=true
      ;;
    --upgrade)
      UPGRADE=true
      ;;
    --merge)
      MERGE=true
      ;;
    --force-init)
      FORCE_INIT=true
      ;;
    --help)
      echo -e "\e[36mDatabase Migration Management Script\e[0m"
      echo -e "\e[36mUsage: ./migrate.sh [options]\e[0m"
      echo ""
      echo -e "\e[33mOptions:\e[0m"
      echo -e "\e[90m  --show-current : Show current migration versions\e[0m"
      echo -e "\e[90m  --upgrade      : Apply all pending migrations\e[0m"
      echo -e "\e[90m  --merge        : Merge migration heads if multiple heads exist\e[0m"
      echo -e "\e[90m  --force-init   : Force initialize migrations if they don't exist\e[0m"
      echo ""
      echo -e "\e[32mExample: ./migrate.sh --upgrade\e[0m"
      exit 0
      ;;
  esac
done

# If no arguments provided, show help
if [[ "$SHOW_CURRENT" == "false" && "$UPGRADE" == "false" && "$MERGE" == "false" && "$FORCE_INIT" == "false" ]]; then
  echo -e "\e[36mDatabase Migration Management Script\e[0m"
  echo -e "\e[36mUsage: ./migrate.sh [options]\e[0m"
  echo ""
  echo -e "\e[33mOptions:\e[0m"
  echo -e "\e[90m  --show-current : Show current migration versions\e[0m"
  echo -e "\e[90m  --upgrade      : Apply all pending migrations\e[0m"
  echo -e "\e[90m  --merge        : Merge migration heads if multiple heads exist\e[0m"
  echo -e "\e[90m  --force-init   : Force initialize migrations if they don't exist\e[0m"
  echo ""
  echo -e "\e[32mExample: ./migrate.sh --upgrade\e[0m"
  exit 0
fi

# Show current migration versions
if [[ "$SHOW_CURRENT" == "true" ]]; then
  echo -e "\e[32mChecking current migration state for backend...\e[0m"
  docker-compose exec -T backend flask db current
  
  echo -e "\e[32mChecking current migration state for auth-service...\e[0m"
  docker-compose exec -T auth-service flask db current
fi

# Force initialize migrations if they don't exist
if [[ "$FORCE_INIT" == "true" ]]; then
  echo -e "\e[33mForce initializing migrations for backend (if needed)...\e[0m"
  docker-compose exec -T backend bash -c "if [ ! -f migrations/alembic.ini ]; then flask db init; fi"
  
  echo -e "\e[33mForce initializing migrations for auth-service (if needed)...\e[0m"
  docker-compose exec -T auth-service bash -c "if [ ! -f migrations/alembic.ini ]; then flask db init; fi"
fi

# Merge migration heads if multiple heads exist
if [[ "$MERGE" == "true" ]]; then
  echo -e "\e[33mMerging migration heads for backend...\e[0m"
  docker-compose exec -T backend flask db merge heads -m "merge_migration_heads"
  
  echo -e "\e[33mMerging migration heads for auth-service...\e[0m"
  docker-compose exec -T auth-service flask db merge heads -m "merge_migration_heads"
fi

# Apply all pending migrations
if [[ "$UPGRADE" == "true" ]]; then
  echo -e "\e[32mApplying pending migrations for backend...\e[0m"
  docker-compose exec -T backend flask db upgrade
  
  echo -e "\e[32mApplying pending migrations for auth-service...\e[0m"
  docker-compose exec -T auth-service flask db upgrade
fi

echo -e "\e[36mMigration operations completed\e[0m" 