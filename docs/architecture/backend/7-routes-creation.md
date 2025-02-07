# Route Creation in Flask Backend

## Overview
This document explains the intermediate concepts of creating routes in our Flask backend application, using real examples from our meeting management system.

## Core Concepts

### 1. Blueprint Organization
Blueprints help organize routes into logical groups. In our application, we use separate blueprints for different features:

```python
from flask import Blueprint
meetings_bp = Blueprint('meetings', __name__)
```

### 2. Route Decoration
Routes are defined using decorators that specify the endpoint and HTTP method:

```python
@meetings_bp.route('/create', methods=['POST'])
@token_required
def create_meeting(current_user):
    # Route implementation
```

### 3. Authentication Middleware
We use decorators to enforce authentication:

```python
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Invalid token format'}), 401
        # Token validation logic
    return decorated
```

## Real-World Example: Meeting Creation Route

### 1. Input Validation
```python
# From backend/flask-service/src/routes/meetings.py
required_fields = ['title', 'description', 'start_time', 'end_time']
if not all(field in data for field in required_fields):
    return jsonify({'error': 'Missing required fields'}), 400
```

### 2. Data Sanitization
```python
title = bleach.clean(data['title'].strip())
description = bleach.clean(data['description'].strip())
```

### 3. Business Logic
```python
# Time validation
if start_time < current_time:
    return jsonify({'error': 'Meeting cannot start in the past'}), 400

# Overlapping meetings check
user_meetings = Meeting.query.filter(
    Meeting.created_by == current_user.id,
    Meeting.ended_at.is_(None),
    Meeting.end_time > start_time,
    Meeting.start_time < end_time
).first()
```

### 4. Database Operations
```python
try:
    db.session.add(meeting)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    return jsonify({'error': 'Server error occurred'}), 500
```

## Integration Points

### 1. Database Models
Routes interact with models:
- `Meeting`
- `MeetingParticipant`
- `MeetingCoHost`
- `MeetingAuditLog`

### 2. Authentication System
- JWT token validation
- User session management
- Permission checks

### 3. Frontend Integration
Routes provide APIs that the frontend uses:
```typescript
// Frontend API call example
const response = await fetch('/api/meetings/create', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(meetingData)
});
```

## Best Practices

1. **Error Handling**
   - Always return appropriate HTTP status codes
   - Provide meaningful error messages
   - Handle both expected and unexpected errors

2. **Input Validation**
   - Validate all user inputs
   - Sanitize data to prevent XSS attacks
   - Use type checking and data constraints

3. **Database Operations**
   - Use transactions for multiple operations
   - Implement proper error handling and rollbacks
   - Optimize queries for performance

4. **Security**
   - Implement authentication checks
   - Validate user permissions
   - Protect against common vulnerabilities

## Common Pitfalls

1. **Missing Error Handling**
   ```python
   # Bad
   meeting = Meeting.query.get(id)
   
   # Good
   meeting = Meeting.query.get(id)
   if not meeting:
       return jsonify({'error': 'Meeting not found'}), 404
   ```

2. **Insufficient Validation**
   ```python
   # Bad
   title = data['title']
   
   # Good
   title = bleach.clean(data['title'].strip())
   if not title:
       return jsonify({'error': 'Meeting title cannot be empty'}), 400
   ```

3. **Transaction Management**
   ```python
   # Bad
   db.session.add(meeting)
   db.session.commit()
   
   # Good
   try:
       db.session.add(meeting)
       db.session.commit()
   except Exception as e:
       db.session.rollback()
       raise
   ```

## Testing Routes

1. **Unit Testing**
   ```python
   def test_create_meeting():
       response = client.post('/api/meetings/create',
           json={'title': 'Test Meeting', ...},
           headers={'Authorization': f'Bearer {test_token}'})
       assert response.status_code == 201
   ```

2. **Integration Testing**
   ```python
   def test_meeting_workflow():
       # Create meeting
       meeting_id = create_test_meeting()
       # Join meeting
       response = client.get(f'/api/meetings/join/{meeting_id}')
       assert response.status_code == 200
   ``` 