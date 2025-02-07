# 5. Testing

## Overview
This document covers testing strategies and implementation in our Flask backend application. Comprehensive testing is crucial for maintaining code quality and preventing regressions.

## Test Structure

### 1. Test Configuration
```python
# tests/conftest.py
import pytest
from src import create_app, db
from src.models import User, Meeting

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('src.config.TestingConfig')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token(test_user)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def test_user():
    """Create test user."""
    user = User(
        email='test@example.com',
        name='Test User'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_meeting(test_user):
    """Create test meeting."""
    meeting = Meeting(
        title='Test Meeting',
        description='Test Description',
        start_time=datetime.utcnow() + timedelta(hours=1),
        end_time=datetime.utcnow() + timedelta(hours=2),
        created_by=test_user.id
    )
    db.session.add(meeting)
    db.session.commit()
    return meeting
```

### 2. Test Factories
```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from src.models import User, Meeting
from src import db
from datetime import datetime, timedelta

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    name = factory.Sequence(lambda n: f'User {n}')
    password_hash = factory.LazyAttribute(
        lambda _: User.hash_password('password123')
    )

class MeetingFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Meeting
        sqlalchemy_session = db.session

    title = factory.Sequence(lambda n: f'Meeting {n}')
    description = factory.Faker('paragraph')
    start_time = factory.LazyFunction(
        lambda: datetime.utcnow() + timedelta(hours=1)
    )
    end_time = factory.LazyFunction(
        lambda: datetime.utcnow() + timedelta(hours=2)
    )
    created_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def participants(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for participant in extracted:
                self.participants.append(participant)
```

## Unit Testing

### 1. Model Tests
```python
# tests/test_models.py
import pytest
from datetime import datetime, timedelta
from src.models import Meeting, User
from src.exceptions import ValidationError

def test_user_password_hashing(test_user):
    """Test password hashing."""
    assert test_user.check_password('password123')
    assert not test_user.check_password('wrong_password')

def test_meeting_validation():
    """Test meeting validation."""
    now = datetime.utcnow()
    
    # Test valid meeting
    meeting = Meeting(
        title='Test Meeting',
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2)
    )
    assert meeting.validate() is None

    # Test invalid meeting
    with pytest.raises(ValidationError):
        meeting = Meeting(
            title='Test Meeting',
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=1)
        )
        meeting.validate()

def test_meeting_participants(test_meeting, test_user):
    """Test meeting participants management."""
    participant = UserFactory()
    test_meeting.add_participant(participant)
    
    assert participant in test_meeting.participants
    assert test_meeting in participant.participated_meetings

    test_meeting.remove_participant(participant)
    assert participant not in test_meeting.participants
```

### 2. Service Tests
```python
# tests/test_services.py
import pytest
from datetime import datetime, timedelta
from src.services import meeting_service
from src.exceptions import MeetingConflictError

def test_create_meeting(test_user):
    """Test meeting creation."""
    meeting_data = {
        'title': 'Test Meeting',
        'description': 'Test Description',
        'start_time': datetime.utcnow() + timedelta(hours=1),
        'end_time': datetime.utcnow() + timedelta(hours=2)
    }

    meeting = meeting_service.create_meeting(meeting_data, test_user)
    assert meeting.title == meeting_data['title']
    assert meeting.created_by == test_user.id

def test_meeting_conflict(test_user):
    """Test meeting conflict detection."""
    # Create first meeting
    meeting1 = MeetingFactory(
        start_time=datetime.utcnow() + timedelta(hours=1),
        end_time=datetime.utcnow() + timedelta(hours=2),
        created_by=test_user
    )

    # Try to create overlapping meeting
    with pytest.raises(MeetingConflictError):
        meeting_service.create_meeting({
            'title': 'Conflicting Meeting',
            'start_time': meeting1.start_time + timedelta(minutes=30),
            'end_time': meeting1.end_time + timedelta(minutes=30)
        }, test_user)
```

## Integration Testing

### 1. API Tests
```python
# tests/test_api.py
import pytest
from datetime import datetime, timedelta

def test_create_meeting_api(client, auth_headers):
    """Test meeting creation API."""
    meeting_data = {
        'title': 'Test Meeting',
        'description': 'Test Description',
        'start_time': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        'end_time': (datetime.utcnow() + timedelta(hours=2)).isoformat()
    }

    response = client.post(
        '/api/meetings',
        json=meeting_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == meeting_data['title']

def test_get_meeting_list(client, auth_headers):
    """Test meeting list API."""
    # Create test meetings
    meetings = MeetingFactory.create_batch(3)
    
    response = client.get(
        '/api/meetings',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3

def test_update_meeting(client, auth_headers, test_meeting):
    """Test meeting update API."""
    update_data = {
        'title': 'Updated Meeting Title'
    }

    response = client.put(
        f'/api/meetings/{test_meeting.id}',
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == update_data['title']
```

### 2. Database Tests
```python
# tests/test_database.py
import pytest
from sqlalchemy.exc import IntegrityError
from src.models import Meeting, User

def test_cascade_delete(test_user, test_meeting):
    """Test cascade delete behavior."""
    meeting_id = test_meeting.id
    db.session.delete(test_user)
    db.session.commit()

    # Meeting should be deleted
    assert Meeting.query.get(meeting_id) is None

def test_unique_constraints():
    """Test unique constraints."""
    user1 = UserFactory(email='same@example.com')
    
    with pytest.raises(IntegrityError):
        user2 = UserFactory(email='same@example.com')
        db.session.commit()

def test_relationship_constraints(test_meeting):
    """Test relationship constraints."""
    participant = UserFactory()
    test_meeting.participants.append(participant)
    db.session.commit()

    # Test duplicate participant
    with pytest.raises(IntegrityError):
        test_meeting.participants.append(participant)
        db.session.commit()
```

## Performance Testing

### 1. Load Tests
```python
# tests/test_performance.py
import pytest
from locust import HttpUser, task, between

class MeetingUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup before tests."""
        self.login()

    def login(self):
        """Login user."""
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.token = response.json()['access_token']
        self.headers = {'Authorization': f'Bearer {self.token}'}

    @task(3)
    def get_meetings(self):
        """Test getting meetings list."""
        self.client.get(
            '/api/meetings',
            headers=self.headers
        )

    @task(1)
    def create_meeting(self):
        """Test creating a meeting."""
        self.client.post(
            '/api/meetings',
            headers=self.headers,
            json={
                'title': 'Load Test Meeting',
                'start_time': '2024-01-01T10:00:00',
                'end_time': '2024-01-01T11:00:00'
            }
        )
```

### 2. Query Performance Tests
```python
# tests/test_query_performance.py
import pytest
import time
from src.models import Meeting, User

def test_query_performance(test_user):
    """Test query performance."""
    # Create test data
    MeetingFactory.create_batch(
        100,
        created_by=test_user
    )

    # Test simple query
    start_time = time.time()
    meetings = Meeting.query.all()
    query_time = time.time() - start_time
    assert query_time < 0.1  # Should be fast

    # Test complex query
    start_time = time.time()
    meetings = Meeting.query.join(
        User
    ).filter(
        Meeting.created_by == test_user.id
    ).order_by(
        Meeting.start_time
    ).all()
    query_time = time.time() - start_time
    assert query_time < 0.1  # Should still be fast
```

## Mocking and Stubbing

### 1. External Service Mocks
```python
# tests/test_external_services.py
import pytest
from unittest.mock import patch, Mock
from src.services import notification_service

@pytest.fixture
def mock_email_service():
    """Mock email service."""
    with patch('src.services.notification_service.send_email') as mock:
        yield mock

def test_meeting_notification(mock_email_service, test_meeting):
    """Test meeting notification."""
    notification_service.notify_participants(test_meeting)
    
    mock_email_service.assert_called_once()
    call_args = mock_email_service.call_args[0]
    assert test_meeting.title in call_args[0]

@pytest.fixture
def mock_calendar_service():
    """Mock calendar service."""
    with patch('src.services.calendar_service.CalendarAPI') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

def test_calendar_integration(mock_calendar_service, test_meeting):
    """Test calendar integration."""
    calendar_service.create_event(test_meeting)
    
    mock_calendar_service.create_event.assert_called_once_with(
        summary=test_meeting.title,
        start_time=test_meeting.start_time,
        end_time=test_meeting.end_time
    )
```

### 2. Database Mocks
```python
# tests/test_with_mocks.py
import pytest
from unittest.mock import patch, Mock
from src.models import Meeting

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch('src.db.session') as mock:
        yield mock

def test_meeting_creation_with_mock(mock_db_session, test_user):
    """Test meeting creation with mocked database."""
    meeting = Meeting(
        title='Test Meeting',
        created_by=test_user.id
    )
    
    meeting.save()
    
    mock_db_session.add.assert_called_once_with(meeting)
    mock_db_session.commit.assert_called_once()
```

## Best Practices

### 1. Test Organization
- Group tests logically
- Use descriptive test names
- Keep tests focused and atomic
- Use appropriate fixtures
- Maintain test independence

### 2. Test Coverage
- Aim for high coverage
- Test edge cases
- Test error conditions
- Test performance critical paths
- Test security features

### 3. Test Maintenance
- Keep tests up to date
- Refactor tests with code
- Remove obsolete tests
- Document test requirements
- Use test automation

## Common Pitfalls

### 1. Poor Test Isolation
```python
# Bad: Tests affecting each other
def test_first():
    global_state = 'modified'
    assert something()

def test_second():
    # Depends on global_state from first test
    assert global_state == 'modified'

# Good: Isolated tests
def test_first(clean_state):
    state = clean_state
    state.modify()
    assert state.check()

def test_second(clean_state):
    assert clean_state.is_clean()
```

### 2. Brittle Tests
```python
# Bad: Testing implementation details
def test_implementation():
    service = Service()
    assert service._internal_cache == {}

# Good: Testing behavior
def test_behavior():
    service = Service()
    result = service.process_data({'key': 'value'})
    assert result.is_valid()
```

## Next Steps
After mastering testing, you have completed the backend documentation series! You can now:
1. Review all documentation
2. Implement new features
3. Improve existing code
4. Share knowledge with team 