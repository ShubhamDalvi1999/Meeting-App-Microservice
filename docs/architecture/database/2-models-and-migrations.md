# Database Migrations and Models

## Overview
This document explains the intermediate concepts of database migrations and models in our Flask application, using real examples from our meeting management system.

## Database Models

### 1. Model Definition
Models represent database tables using SQLAlchemy ORM:

```python
class Meeting(db.Model):
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
```

### 2. Relationships
Models can define relationships with other models:

```python
# One-to-Many relationship
creator = db.relationship('User', backref=db.backref('created_meetings', lazy=True))

# Many-to-Many relationship through association table
participants = db.relationship('MeetingParticipant', backref='meeting', lazy=True)
```

## Migrations

### 1. Creating Migrations
Migrations are created when models change:

```bash
flask db migrate -m "add meeting enhancements"
```

Example migration file:
```python
def upgrade():
    # Add new columns to meetings table
    op.add_column('meetings', sa.Column('meeting_type', sa.String(20)))
    op.add_column('meetings', sa.Column('max_participants', sa.Integer))
```

### 2. Applying Migrations
Migrations are applied to update the database:

```bash
flask db upgrade
```

### 3. Rolling Back
Migrations can be reversed:

```python
def downgrade():
    op.drop_column('meetings', 'meeting_type')
    op.drop_column('meetings', 'max_participants')
```

## Real-World Examples

### 1. Meeting Enhancement Migration
```python
def upgrade():
    # Add new columns
    op.add_column('meetings', sa.Column('meeting_type', sa.String(20)))
    op.add_column('meetings', sa.Column('requires_approval', sa.Boolean))
    
    # Create new table
    op.create_table(
        'meeting_co_hosts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('meeting_id', sa.Integer, nullable=False),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
```

### 2. Model Methods
```python
class Meeting(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }
```

## Best Practices

### 1. Migration Design
- Make migrations reversible
- Test both upgrade and downgrade
- Keep migrations focused and atomic
- Include meaningful comments

### 2. Model Design
- Use appropriate data types
- Define constraints at database level
- Implement proper indexing
- Use lazy loading for relationships

### 3. Data Integrity
- Use foreign key constraints
- Implement cascading deletes where appropriate
- Define default values
- Handle nullable fields properly

## Common Pitfalls

### 1. Migration Issues
```python
# Bad: Non-reversible migration
def upgrade():
    op.execute("UPDATE meetings SET status = 'active'")

# Good: Reversible migration
def upgrade():
    op.add_column('meetings', sa.Column('status', sa.String(20), server_default='active'))

def downgrade():
    op.drop_column('meetings', 'status')
```

### 2. Model Relationships
```python
# Bad: Eager loading by default
participants = db.relationship('User', backref='meetings')

# Good: Lazy loading with specific loading when needed
participants = db.relationship('User', backref='meetings', lazy='dynamic')
```

## Performance Considerations

### 1. Indexing
```python
# Add indexes for frequently queried columns
__table_args__ = (
    db.Index('idx_meeting_start_time', 'start_time'),
    db.Index('idx_meeting_status', 'status'),
)
```

### 2. Query Optimization
```python
# Bad: N+1 query problem
meetings = Meeting.query.all()
for meeting in meetings:
    print(meeting.creator.name)

# Good: Eager loading when needed
meetings = Meeting.query.options(joinedload('creator')).all()
```

## Testing

### 1. Migration Testing
```python
def test_migration():
    # Test upgrade
    upgrade()
    assert column_exists('meetings', 'meeting_type')
    
    # Test downgrade
    downgrade()
    assert not column_exists('meetings', 'meeting_type')
```

### 2. Model Testing
```python
def test_meeting_creation():
    meeting = Meeting(title="Test Meeting", start_time=datetime.now())
    db.session.add(meeting)
    db.session.commit()
    assert meeting.id is not None
``` 