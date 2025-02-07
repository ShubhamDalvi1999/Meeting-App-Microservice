# Database Migration Standards

## Overview
This document outlines the standardized process for managing database migrations in our application, ensuring idempotency and reproducible outputs.

## Migration Structure

### 1. Migration File Naming
```python
# Format: {timestamp}_{descriptive_name}.py
# Example: 2023_12_31_121000_add_security_fields.py

"""add security fields

Revision ID: add_security_fields
Revises: rename_username_to_name
Create Date: 2023-12-31 12:10:00.000000
"""
```

### 2. Standard Migration Template
```python
"""migration description

Revision ID: {revision_id}
Revises: {previous_revision}
Create Date: {timestamp}
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC

# revision identifiers
revision = 'unique_revision_id'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None

def upgrade():
    """
    Implement the forward migration.
    Must be idempotent.
    """
    pass

def downgrade():
    """
    Implement the reverse migration.
    Must restore database to previous state.
    """
    pass
```

## Migration Types

### 1. Schema Changes
```python
def upgrade():
    # Adding new columns
    op.add_column('table_name',
        sa.Column('new_column', sa.String(50), nullable=False, server_default='default_value')
    )
    
    # Creating indexes
    op.create_index(
        op.f('ix_table_column'),
        'table_name',
        ['column_name'],
        unique=False
    )
    
    # Adding constraints
    op.create_check_constraint(
        'constraint_name',
        'table_name',
        'column_name IN (value1, value2)'
    )

def downgrade():
    # Remove in reverse order
    op.drop_constraint('constraint_name', 'table_name')
    op.drop_index(op.f('ix_table_column'), 'table_name')
    op.drop_column('table_name', 'new_column')
```

### 2. Data Migrations
```python
def upgrade():
    # Get database connection
    connection = op.get_bind()
    
    # Execute data updates
    connection.execute("""
        UPDATE table_name
        SET new_column = CASE
            WHEN condition THEN value1
            ELSE value2
        END
        WHERE condition
    """)

def downgrade():
    connection = op.get_bind()
    # Reverse data changes if possible
    connection.execute("""
        UPDATE table_name
        SET new_column = default_value
        WHERE condition
    """)
```

## Migration Process

### 1. Creating New Migrations
```bash
# Using the create_migration.sh script
./scripts/create_migration.sh "descriptive_name"

# Script ensures:
# - Proper naming convention
# - Correct template usage
# - Validation of migration message
```

### 2. Applying Migrations
```bash
# Using the db_upgrade.sh script
./scripts/db_upgrade.sh

# Script performs:
# 1. Database connection verification
# 2. Migration directory initialization if needed
# 3. Migration status check
# 4. Safe migration application
# 5. Verification of results
```

## Best Practices

### 1. Migration Design
- Make all migrations reversible
- Keep migrations atomic (one logical change per migration)
- Include both 'up' and 'down' migrations
- Use explicit naming for constraints and indexes
- Add appropriate indexes for foreign keys

### 2. Data Safety
```python
def upgrade():
    # Always check existence before creating
    if not op.get_bind().dialect.has_table(op.get_bind(), 'table_name'):
        op.create_table(...)
    
    # Use transactions for data migrations
    connection = op.get_bind()
    transaction = connection.begin()
    try:
        # Perform data migration
        transaction.commit()
    except:
        transaction.rollback()
        raise
```

### 3. Performance Considerations
```python
def upgrade():
    # Batch large data migrations
    connection = op.get_bind()
    batch_size = 1000
    offset = 0
    
    while True:
        batch = connection.execute(f"""
            SELECT id FROM table_name
            ORDER BY id
            LIMIT {batch_size} OFFSET {offset}
        """).fetchall()
        
        if not batch:
            break
            
        # Process batch
        ids = [row[0] for row in batch]
        connection.execute(f"""
            UPDATE table_name
            SET column = new_value
            WHERE id = ANY(:ids)
        """, {'ids': ids})
        
        offset += batch_size
```

## Validation and Testing

### 1. Pre-Migration Checks
```python
def upgrade():
    connection = op.get_bind()
    
    # Verify preconditions
    result = connection.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'target_table'
        AND column_name = 'target_column'
    """).scalar()
    
    if result > 0:
        # Column already exists, skip creation
        return
```

### 2. Post-Migration Verification
```python
def upgrade():
    # Perform migration
    op.add_column(...)
    
    # Verify results
    connection = op.get_bind()
    result = connection.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'target_table'
        AND column_name = 'new_column'
    """).fetchone()
    
    if not result or result.data_type != 'expected_type':
        raise Exception("Migration verification failed")
```

## Troubleshooting

### 1. Common Issues
- Migration conflicts
- Data integrity issues
- Performance problems with large datasets
- Failed migrations

### 2. Recovery Procedures
```bash
# Rollback last migration
flask db downgrade

# Get current migration status
flask db current

# View migration history
flask db history

# Verify database state
flask db check
```

## Next Steps
1. Review [Query Optimization](3-query-optimization.md)
2. Implement [Database Maintenance](4-maintenance.md)
3. Monitor migration performance and optimize as needed
``` 