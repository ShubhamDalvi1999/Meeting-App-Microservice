# 6. Performance Optimization

## Overview
This document covers performance optimization strategies in our Flask backend application. Understanding and implementing these concepts is crucial for maintaining a responsive and scalable application.

## Database Optimization

### 1. Query Optimization
```python
# Example: Optimizing database queries
from sqlalchemy import func
from src.models import Meeting, User

# Bad: N+1 Query Problem
def get_meetings_with_creator():
    meetings = Meeting.query.all()
    # This causes N additional queries
    return [(m, User.query.get(m.created_by)) for m in meetings]

# Good: Using JOIN
def get_meetings_with_creator():
    return Meeting.query.join(
        User,
        Meeting.created_by == User.id
    ).add_columns(
        Meeting,
        User
    ).all()

# Bad: Loading unnecessary data
def get_meeting_titles():
    meetings = Meeting.query.all()
    return [m.title for m in meetings]

# Good: Selecting only needed columns
def get_meeting_titles():
    return Meeting.query.with_entities(Meeting.title).all()

# Bad: Inefficient counting
def count_meetings():
    return len(Meeting.query.all())

# Good: Using COUNT
def count_meetings():
    return Meeting.query.with_entities(func.count()).scalar()
```

### 2. Indexing Strategy
```python
# Example: Adding indexes to models
from sqlalchemy import Index

class Meeting(db.Model):
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Add index for frequent queries
    __table_args__ = (
        Index('idx_meeting_time_range', 'start_time', 'end_time'),
        Index('idx_meeting_creator', 'created_by'),
    )

# Example: Composite index for common query pattern
class Participant(db.Model):
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20))
    
    __table_args__ = (
        Index('idx_participant_meeting_status', 'meeting_id', 'status'),
    )
```

### 3. Bulk Operations
```python
# Example: Efficient bulk operations
from sqlalchemy.orm import Session

# Bad: Individual inserts
def create_meetings(meeting_data_list):
    for data in meeting_data_list:
        meeting = Meeting(**data)
        db.session.add(meeting)
        db.session.commit()

# Good: Bulk insert
def create_meetings(meeting_data_list):
    meetings = [Meeting(**data) for data in meeting_data_list]
    db.session.bulk_save_objects(meetings)
    db.session.commit()

# Example: Bulk updates
def update_meeting_statuses(meeting_ids, new_status):
    Meeting.query.filter(
        Meeting.id.in_(meeting_ids)
    ).update(
        {Meeting.status: new_status},
        synchronize_session=False
    )
    db.session.commit()
```

## Caching Strategies

### 1. In-Memory Caching
```python
# Example: Using Flask-Caching
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Cache frequently accessed data
@cache.memoize(timeout=300)
def get_user_meetings(user_id):
    return Meeting.query.filter_by(created_by=user_id).all()

# Cache expensive computations
@cache.memoize(timeout=3600)
def calculate_meeting_statistics(user_id):
    meetings = Meeting.query.filter_by(created_by=user_id).all()
    total_duration = sum(
        (m.end_time - m.start_time).total_seconds()
        for m in meetings
    )
    return {
        'total_meetings': len(meetings),
        'total_duration': total_duration,
        'average_duration': total_duration / len(meetings)
    }

# Cache invalidation
def update_meeting(meeting_id, data):
    meeting = Meeting.query.get(meeting_id)
    for key, value in data.items():
        setattr(meeting, key, value)
    db.session.commit()
    # Invalidate cache
    cache.delete_memoized(get_user_meetings, meeting.created_by)
```

### 2. Redis Caching
```python
# Example: Using Redis for caching
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, db=0)

class RedisCache:
    @staticmethod
    def set(key, value, expire=300):
        """Set cache with expiration."""
        redis_client.setex(
            key,
            expire,
            json.dumps(value)
        )
    
    @staticmethod
    def get(key):
        """Get cached value."""
        value = redis_client.get(key)
        return json.loads(value) if value else None

# Example usage
def get_meeting_details(meeting_id):
    cache_key = f'meeting:{meeting_id}'
    
    # Try cache first
    cached = RedisCache.get(cache_key)
    if cached:
        return cached
    
    # Query database if not in cache
    meeting = Meeting.query.get(meeting_id)
    if not meeting:
        return None
    
    data = meeting.to_dict()
    RedisCache.set(cache_key, data)
    return data
```

## Request Processing

### 1. Asynchronous Tasks
```python
# Example: Using Celery for background tasks
from celery import Celery
from src.services import notification_service

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def send_meeting_notifications(meeting_id):
    """Send notifications asynchronously."""
    meeting = Meeting.query.get(meeting_id)
    for participant in meeting.participants:
        notification_service.notify_user(
            participant.id,
            f'New meeting: {meeting.title}'
        )

# Use in route
@app.route('/api/meetings', methods=['POST'])
def create_meeting():
    meeting = Meeting(**request.json)
    db.session.add(meeting)
    db.session.commit()
    
    # Schedule notification task
    send_meeting_notifications.delay(meeting.id)
    return jsonify(meeting.to_dict())
```

### 2. Request Middleware
```python
# Example: Performance monitoring middleware
import time
from flask import request, g
from functools import wraps

def performance_monitor():
    """Measure request processing time."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            result = f(*args, **kwargs)
            
            duration = time.time() - start_time
            app.logger.info(
                f'Request to {request.path} took {duration:.2f} seconds'
            )
            
            return result
        return decorated_function
    return decorator

@app.route('/api/meetings')
@performance_monitor()
def get_meetings():
    return jsonify(Meeting.query.all())
```

## Load Balancing

### 1. Application Configuration
```python
# Example: Configuration for different environments
class Config:
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30

class ProductionConfig(Config):
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_MAX_OVERFLOW = 40
    SQLALCHEMY_POOL_RECYCLE = 300
```

### 2. Connection Pooling
```python
# Example: Database connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:pass@localhost/dbname',
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=300
)
```

## Best Practices

### 1. Query Optimization
- Use appropriate indexes
- Avoid N+1 queries
- Select only needed columns
- Use bulk operations
- Implement efficient pagination

### 2. Caching Strategy
- Cache frequently accessed data
- Use appropriate cache backends
- Implement proper cache invalidation
- Monitor cache hit rates
- Cache at appropriate levels

### 3. Resource Management
- Use connection pooling
- Implement request timeouts
- Monitor resource usage
- Scale horizontally when needed
- Use asynchronous processing

## Common Pitfalls

### 1. Memory Leaks
```python
# Bad: Memory leak in cache
cache = {}
def get_data(key):
    if key not in cache:
        cache[key] = expensive_operation()
    return cache[key]

# Good: LRU Cache
from functools import lru_cache

@lru_cache(maxsize=100)
def get_data(key):
    return expensive_operation()
```

### 2. Resource Exhaustion
```python
# Bad: No timeout on external service
def call_external_service():
    return requests.get('http://api.example.com/data')

# Good: Implement timeouts
def call_external_service():
    return requests.get(
        'http://api.example.com/data',
        timeout=5
    )
```

## Next Steps
After mastering performance optimization, you have completed the backend documentation series! You can now:
1. Review all documentation
2. Implement new features with performance in mind
3. Optimize existing code
4. Monitor and improve application performance
5. Share knowledge with team 