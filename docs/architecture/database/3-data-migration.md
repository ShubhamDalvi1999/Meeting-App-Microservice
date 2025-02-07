# 2. Data Migration

## Overview
This document covers database migration strategies and implementation in our meeting management system. Understanding these concepts is crucial for maintaining database schema changes and data integrity throughout the application's lifecycle.

## Migration Types

### 1. Schema Migrations
```python
# migrations/versions/xxxx_create_initial_tables.py
"""Create initial tables

Revision ID: xxxx
Revises: None
Create Date: 2024-01-01 10:00:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create meetings table
    op.create_table(
        'meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('end_time > start_time', name='valid_time_range')
    )

def downgrade():
    op.drop_table('meetings')
    op.drop_table('users')
```

### 2. Data Migrations
```python
# migrations/versions/yyyy_add_meeting_status.py
"""Add meeting status

Revision ID: yyyy
Revises: xxxx
Create Date: 2024-01-02 10:00:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add status column
    op.add_column(
        'meetings',
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='scheduled'
        )
    )

    # Add status check constraint
    op.create_check_constraint(
        'valid_status',
        'meetings',
        "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')"
    )

    # Update existing records
    connection = op.get_bind()
    connection.execute("""
        UPDATE meetings
        SET status = CASE
            WHEN end_time < NOW() THEN 'completed'
            WHEN start_time <= NOW() AND end_time >= NOW() THEN 'in_progress'
            ELSE 'scheduled'
        END
    """)

def downgrade():
    op.drop_constraint('valid_status', 'meetings')
    op.drop_column('meetings', 'status')
```

### 3. Index Migrations
```python
# migrations/versions/zzzz_add_meeting_indexes.py
"""Add meeting indexes

Revision ID: zzzz
Revises: yyyy
Create Date: 2024-01-03 10:00:00
"""
from alembic import op

def upgrade():
    # Add performance indexes
    op.create_index(
        'idx_meetings_time_range',
        'meetings',
        ['start_time', 'end_time']
    )
    op.create_index(
        'idx_meetings_status',
        'meetings',
        ['status']
    )
    op.create_index(
        'idx_meetings_creator',
        'meetings',
        ['created_by']
    )

def downgrade():
    op.drop_index('idx_meetings_creator')
    op.drop_index('idx_meetings_status')
    op.drop_index('idx_meetings_time_range')
```

## Migration Management

### 1. Alembic Configuration
```python
# alembic.ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 2. Migration Commands
```bash
# Generate new migration
alembic revision -m "create users table"

# Run all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade xxxx

# View migration history
alembic history --verbose

# View current version
alembic current

# Generate automatic migration
alembic revision --autogenerate -m "add user fields"
```

## Migration Strategies

### 1. Zero-Downtime Migrations
```python
# Example: Adding a new column without locking
def upgrade():
    # 1. Add nullable column
    op.add_column(
        'users',
        sa.Column('phone', sa.String(20), nullable=True)
    )

    # 2. Backfill data
    connection = op.get_bind()
    connection.execute("""
        UPDATE users
        SET phone = 'unknown'
        WHERE phone IS NULL
    """)

    # 3. Make column non-nullable
    op.alter_column(
        'users',
        'phone',
        nullable=False,
        server_default='unknown'
    )

def downgrade():
    op.drop_column('users', 'phone')
```

### 2. Data Transformation
```python
# Example: Complex data transformation
def upgrade():
    # 1. Create temporary table
    op.create_table(
        'meeting_participants_new',
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('meeting_id', 'user_id')
    )

    # 2. Transform and copy data
    connection = op.get_bind()
    connection.execute("""
        INSERT INTO meeting_participants_new (meeting_id, user_id, status)
        SELECT meeting_id, user_id,
            CASE WHEN attended THEN 'accepted' ELSE 'declined' END
        FROM meeting_participants_old
    """)

    # 3. Drop old table and rename new
    op.drop_table('meeting_participants_old')
    op.rename_table('meeting_participants_new', 'meeting_participants')
```

## Best Practices

### 1. Migration Design
- Make migrations reversible
- Use transactions appropriately
- Test migrations thoroughly
- Document complex migrations
- Consider performance impact

### 2. Migration Safety
- Backup data before migrating
- Test on staging environment
- Monitor system during migration
- Have rollback plan
- Use appropriate locks

### 3. Migration Performance
- Batch large operations
- Use appropriate indexes
- Monitor resource usage
- Schedule during low traffic
- Consider zero-downtime approaches

## Common Pitfalls

### 1. Non-Reversible Migrations
```python
# Bad: Non-reversible migration
def upgrade():
    op.execute("DROP TABLE users")  # Data loss!

# Good: Reversible migration
def upgrade():
    op.rename_table('users', 'users_old')
    # Create new table and migrate data
    
def downgrade():
    op.rename_table('users_old', 'users')
```

### 2. Long-Running Migrations
```python
# Bad: Single large update
def upgrade():
    connection.execute("UPDATE huge_table SET status = 'active'")

# Good: Batched update
def upgrade():
    while True:
        result = connection.execute("""
            UPDATE huge_table 
            SET status = 'active' 
            WHERE id IN (
                SELECT id FROM huge_table 
                WHERE status IS NULL 
                LIMIT 1000
            )
        """)
        if result.rowcount == 0:
            break
```

## Next Steps
After mastering data migration, proceed to:
1. Query Optimization (3_query_optimization.md)
2. Database Maintenance (4_database_maintenance.md) 