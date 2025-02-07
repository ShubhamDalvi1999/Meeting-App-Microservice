#!/bin/bash

# Wait for database to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

# Check if migrations are up to date
python -c "from src.app import create_app; from flask_migrate import current; app = create_app(initialize_db=False); assert current(app), 'Migrations are not up to date'"

# Check if required tables exist
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt" | grep -q "auth_users"

exit $? 