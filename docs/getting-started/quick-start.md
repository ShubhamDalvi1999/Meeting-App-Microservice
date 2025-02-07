# Database Migrations Quick Start Guide

## Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Flask-Migrate
- SQLAlchemy

## Quick Commands

### 1. First-Time Setup
```bash
# Initialize database
flask db init

# Apply all migrations
flask db upgrade
```

### 2. Creating New Migrations
```bash
# Generate migration
flask db migrate -m "describe your change"

# Review generated migration in:
# migrations/versions/[hash]_describe_your_change.py

# Apply new migration
flask db upgrade
```

### 3. Rolling Back Changes
```bash
# Rollback last migration
flask db downgrade

# Rollback to specific version
flask db downgrade <migration_id>
```

### 4. Migration Status
```bash
# View migration history
flask db history

# Check current version
flask db current

# Show pending migrations
flask db show
```

## Common Scenarios

### 1. Adding a New Column
```python
# In models/user.py
class User(db.Model):
    new_field = db.Column(db.String(50))

# Generate migration
$ flask db migrate -m "add new_field to user"
```

### 2. Modifying Existing Column
```python
# In migration file
def upgrade():
    op.alter_column('users', 'email',
                    existing_type=sa.String(120),
                    type_=sa.String(255))
```

### 3. Adding Indexes
```python
def upgrade():
    op.create_index('ix_users_email',
                    'users', ['email'],
                    unique=True)
```

### 4. Data Migrations
```python
def upgrade():
    # Add column
    op.add_column('users', 
        sa.Column('full_name', sa.String(100)))
    
    # Migrate data
    op.execute(
        "UPDATE users SET full_name = name"
    )
```

## Troubleshooting

### 1. Migration Conflicts
```bash
# Reset database (DEVELOPMENT ONLY!)
flask db stamp base
flask db upgrade
```

### 2. Failed Migration
```bash
# Roll back to last working version
flask db downgrade
```

### 3. Check Migration State
```bash
# View migration SQL
flask db upgrade --sql
```

## Best Practices

1. **Always Review Migrations**
   ```python
   # Check both upgrade and downgrade
   def upgrade():
       # Your changes
   
   def downgrade():
       # Must reverse all changes
   ```

2. **Test Before Committing**
   ```bash
   # Test upgrade
   flask db upgrade
   
   # Test downgrade
   flask db downgrade
   ```

3. **Include Dependencies**
   ```python
   # In migration file
   depends_on = ('previous_migration',)
   ```

## Project-Specific Notes

### Current Migration Chain
```
initial.py
└── add_ended_at.py
    └── rename_username_to_name.py
        └── add_security_fields.py
```

### Required Environment Variables
```bash
DATABASE_URL=postgresql://dev_user:dev-password-123@postgres:5432/meetingapp
FLASK_APP=src.app
FLASK_ENV=development
```

### Database Backup Before Migration
```bash
# In production
pg_dump meetingapp > backup.sql

# Restore if needed
psql meetingapp < backup.sql
``` 