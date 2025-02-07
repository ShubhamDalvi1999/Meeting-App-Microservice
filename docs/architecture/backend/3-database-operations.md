# 3. Database Operations

## Overview
This document covers database operations and management in our Flask application using SQLAlchemy ORM. Understanding these concepts is crucial for efficient data handling and maintaining data integrity.

## Database Models

### 1. Base Model
```python
# src/models/base.py
from datetime import datetime
from src import db
from sqlalchemy.ext.declarative import declared_attr

class BaseModel(db.Model):
    """Base model class with common fields and methods."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    @declared_attr
    def __tablename__(cls):
        """Generate table name automatically."""
        return cls.__name__.lower() + 's'

    def save(self):
        """Save the model instance."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete the model instance."""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

### 2. Model Relationships
```python
# src/models/meeting.py
from src.models.base import BaseModel
from src import db

class Meeting(BaseModel):
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    # Relationships
    creator = db.relationship(
        'User',
        backref=db.backref('created_meetings', lazy='dynamic'),
        foreign_keys=[created_by]
    )

    participants = db.relationship(
        'User',
        secondary='meeting_participants',
        backref=db.backref('participated_meetings', lazy='dynamic')
    )

    def to_dict(self):
        """Convert meeting to dictionary with relationships."""
        data = super().to_dict()
        data.update({
            'creator': self.creator.to_dict(),
            'participants': [
                participant.to_dict()
                for participant in self.participants
            ]
        })
        return data

# Association tables
meeting_participants = db.Table(
    'meeting_participants',
    db.Column(
        'meeting_id',
        db.Integer,
        db.ForeignKey('meetings.id'),
        primary_key=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.id'),
        primary_key=True
    )
)
```

## Query Operations

### 1. Basic Queries
```python
# src/repositories/meeting_repository.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_, or_
from src.models import Meeting, User

class MeetingRepository:
    def get_by_id(self, meeting_id: int) -> Optional[Meeting]:
        """Get meeting by ID."""
        return Meeting.query.get(meeting_id)

    def get_all(
        self,
        page: int = 1,
        per_page: int = 20
    ) -> List[Meeting]:
        """Get all meetings with pagination."""
        return Meeting.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        ).items

    def get_by_user(
        self,
        user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Meeting]:
        """Get meetings for a user within a date range."""
        query = Meeting.query.filter(
            or_(
                Meeting.created_by == user.id,
                Meeting.participants.any(id=user.id)
            )
        )

        if start_date:
            query = query.filter(Meeting.start_time >= start_date)
        if end_date:
            query = query.filter(Meeting.end_time <= end_date)

        return query.order_by(Meeting.start_time).all()

    def get_overlapping(
        self,
        start_time: datetime,
        end_time: datetime,
        user_id: int
    ) -> List[Meeting]:
        """Get overlapping meetings for a user."""
        return Meeting.query.filter(
            and_(
                or_(
                    Meeting.created_by == user_id,
                    Meeting.participants.any(id=user_id)
                ),
                Meeting.start_time < end_time,
                Meeting.end_time > start_time
            )
        ).all()
```

### 2. Complex Queries
```python
# src/repositories/analytics_repository.py
from typing import List, Dict, Any
from sqlalchemy import func, extract
from src.models import Meeting, User

class AnalyticsRepository:
    def get_meeting_stats(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get meeting statistics for a user."""
        created_count = Meeting.query.filter_by(
            created_by=user_id
        ).count()

        participated_count = Meeting.query.filter(
            Meeting.participants.any(id=user_id)
        ).count()

        # Average meeting duration
        duration_query = db.session.query(
            func.avg(
                func.extract('epoch', Meeting.end_time) -
                func.extract('epoch', Meeting.start_time)
            )
        ).filter_by(created_by=user_id)

        avg_duration = duration_query.scalar() or 0

        return {
            'created_count': created_count,
            'participated_count': participated_count,
            'average_duration_minutes': avg_duration / 60
        }

    def get_monthly_meeting_counts(
        self,
        year: int
    ) -> List[Dict[str, Any]]:
        """Get meeting counts by month for a year."""
        return db.session.query(
            extract('month', Meeting.start_time).label('month'),
            func.count(Meeting.id).label('count')
        ).filter(
            extract('year', Meeting.start_time) == year
        ).group_by(
            extract('month', Meeting.start_time)
        ).all()

    def get_most_active_users(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most active users based on meeting participation."""
        return db.session.query(
            User,
            func.count(Meeting.id).label('meeting_count')
        ).join(
            meeting_participants,
            User.id == meeting_participants.c.user_id
        ).join(
            Meeting,
            Meeting.id == meeting_participants.c.meeting_id
        ).group_by(
            User.id
        ).order_by(
            func.count(Meeting.id).desc()
        ).limit(limit).all()
```

## Transaction Management

### 1. Basic Transactions
```python
# src/services/meeting_service.py
from src import db
from src.models import Meeting, User
from src.exceptions import ValidationError

class MeetingService:
    def create_meeting(
        self,
        data: Dict[str, Any],
        user: User
    ) -> Meeting:
        """Create a new meeting with participants."""
        try:
            meeting = Meeting(
                title=data['title'],
                description=data.get('description', ''),
                start_time=data['start_time'],
                end_time=data['end_time'],
                created_by=user.id
            )

            # Add participants
            participant_ids = data.get('participant_ids', [])
            participants = User.query.filter(
                User.id.in_(participant_ids)
            ).all()
            meeting.participants.extend(participants)

            db.session.add(meeting)
            db.session.commit()
            return meeting

        except Exception as e:
            db.session.rollback()
            raise ValidationError(str(e))
```

### 2. Nested Transactions
```python
# src/services/batch_service.py
from contextlib import contextmanager
from typing import List, Callable
from src import db
from src.models import Meeting

class BatchService:
    @contextmanager
    def transaction(self):
        """Transaction context manager."""
        try:
            yield
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def process_batch(
        self,
        items: List[Any],
        processor: Callable[[Any], None],
        batch_size: int = 100
    ):
        """Process items in batches with transaction management."""
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            with self.transaction():
                for item in batch:
                    processor(item)

    def bulk_create_meetings(
        self,
        meetings_data: List[Dict[str, Any]]
    ) -> List[Meeting]:
        """Bulk create meetings with error handling."""
        meetings = []
        errors = []

        for data in meetings_data:
            try:
                with self.transaction():
                    meeting = Meeting(**data)
                    db.session.add(meeting)
                    meetings.append(meeting)
            except Exception as e:
                errors.append({
                    'data': data,
                    'error': str(e)
                })

        return meetings, errors
```

## Migration Management

### 1. Migration Scripts
```python
# migrations/versions/xxxx_add_meeting_status.py
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = 'yyyy'

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
        'meeting_status_check',
        'meetings',
        sa.Column('status').in_([
            'scheduled',
            'in_progress',
            'completed',
            'cancelled'
        ])
    )

def downgrade():
    # Remove status check constraint
    op.drop_constraint(
        'meeting_status_check',
        'meetings'
    )

    # Remove status column
    op.drop_column('meetings', 'status')
```

### 2. Data Migrations
```python
# migrations/versions/xxxx_migrate_meeting_data.py
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'xxxx'
down_revision = 'yyyy'

def upgrade():
    # Create connection
    connection = op.get_bind()

    # Update meeting statuses based on time
    connection.execute("""
        UPDATE meetings
        SET status = CASE
            WHEN end_time < NOW() THEN 'completed'
            WHEN start_time <= NOW() AND end_time >= NOW() THEN 'in_progress'
            ELSE 'scheduled'
        END
    """)

def downgrade():
    # No downgrade necessary for data migration
    pass
```

## Best Practices

### 1. Query Optimization
- Use eager loading for relationships
- Implement proper indexing
- Use query caching when appropriate
- Optimize complex queries
- Monitor query performance

### 2. Data Integrity
- Implement proper constraints
- Use transactions appropriately
- Validate data before saving
- Handle race conditions
- Implement proper cascading

### 3. Migration Management
- Make migrations reversible
- Test migrations thoroughly
- Back up data before migrations
- Plan for data migrations
- Version control migrations

## Common Pitfalls

### 1. N+1 Query Problem
```python
# Bad: N+1 queries
meetings = Meeting.query.all()
for meeting in meetings:
    print(meeting.creator.name)  # Triggers additional query

# Good: Eager loading
meetings = Meeting.query.options(
    joinedload('creator')
).all()
for meeting in meetings:
    print(meeting.creator.name)  # No additional query
```

### 2. Memory Management
```python
# Bad: Loading all records into memory
all_meetings = Meeting.query.all()

# Good: Using pagination or yield_per
def process_meetings():
    for meeting in Meeting.query.yield_per(100):
        process_meeting(meeting)
```

## Next Steps
After mastering database operations, proceed to:
1. Error Handling (4_error_handling.md)
2. Testing (5_testing.md) 