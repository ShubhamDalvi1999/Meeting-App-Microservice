# Database Migration Guide

## Overview
This document outlines the standardized process for managing database migrations in our application.

## Migration Process

### 1. Creating a New Migration

When you make changes to database models (e.g., adding/modifying tables or columns), follow these steps:

1. Make your changes to the model files in `backend/flask-service/src/models/`
2. Create a new migration:
   ```bash
   cd backend/flask-service
   ./scripts/create_migration.sh "description of your changes"
   ```
3. Review the generated migration file in `migrations/versions/`
4. Commit the migration file to version control

### 2. Applying Migrations

Migrations are automatically applied when:
- The backend container starts
- The backend service is restarted

To manually apply migrations:
```bash
docker-compose exec backend flask db upgrade
```

### 3. Rolling Back Migrations

To roll back the most recent migration:
```bash
docker-compose exec backend flask db downgrade
```

## Best Practices

1. **One Change Per Migration**
   - Each migration should handle one logical change
   - Keep migrations focused and atomic

2. **Always Review Migrations**
   - Check the generated migration file before committing
   - Ensure both upgrade() and downgrade() functions are correct

3. **Test Migrations**
   - Test both applying and rolling back migrations
   - Verify data integrity after migration

4. **Version Control**
   - Always commit migration files
   - Include clear commit messages

## Common Issues

### 1. Migration Conflicts
If you get conflicts in migration files:
1. Roll back to a known good state
2. Delete conflicting migration files
3. Recreate migrations

### 2. Failed Migrations
If a migration fails:
1. Check the logs: `docker-compose logs backend`
2. Roll back to previous version
3. Fix the issue and retry

### 3. Data Loss Prevention
- Always backup the database before major migrations
- Test migrations on a copy of production data

## Migration File Structure

```python
"""migration message

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Changes to apply when upgrading
    pass

def downgrade():
    # Changes to apply when rolling back
    pass
```

## Automatic Migration Process

Our application includes automated migration handling:

1. **Container Startup**
   - Waits for database availability
   - Automatically runs pending migrations
   - Logs migration status

2. **Health Checks**
   - Verifies database connectivity
   - Ensures migrations are up to date

3. **Error Handling**
   - Logs migration failures
   - Prevents application startup if migrations fail

## Development Workflow

1. **Making Changes**
   ```bash
   # 1. Modify models
   vim backend/flask-service/src/models/your_model.py

   # 2. Create migration
   ./scripts/create_migration.sh "describe your changes"

   # 3. Review migration file
   vim migrations/versions/[new_migration_file].py

   # 4. Apply migration
   docker-compose restart backend
   ```

2. **Verifying Changes**
   ```bash
   # Check migration status
   docker-compose exec backend flask db current
   
   # View migration history
   docker-compose exec backend flask db history
   ```

## Production Considerations

1. **Backup First**
   ```bash
   # Backup before migrations
   pg_dump -U postgres -d your_db > backup.sql
   ```

2. **Testing Migrations**
   - Test on staging environment first
   - Verify data integrity
   - Check application functionality

3. **Monitoring**
   - Watch logs during migration
   - Monitor database performance
   - Check application health 