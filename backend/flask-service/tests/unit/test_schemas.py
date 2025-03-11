"""
Unit tests for the validation schemas in the Flask service.
"""

import pytest
from datetime import datetime, timedelta
import uuid
from marshmallow import ValidationError

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.schema]


class TestMeetingSchema:
    """Unit tests for the Meeting schema."""
    
    def test_meeting_schema_validation_success(self, app):
        """Test validating a valid meeting with the schema."""
        with app.app_context():
            from src.schemas.meeting import MeetingSchema
            
            # Set up test data
            start_time = datetime.utcnow() + timedelta(days=1)
            end_time = start_time + timedelta(hours=1)
            
            # Valid meeting data
            meeting_data = {
                'title': 'Test Meeting',
                'description': 'This is a test meeting',
                'creator_id': str(uuid.uuid4()),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'location': 'Conference Room A',
                'meeting_type': 'team',
                'recurring': False
            }
            
            # Create schema instance
            schema = MeetingSchema()
            
            # Validate and deserialize data
            result = schema.load(meeting_data)
            
            # Check that the result contains the expected data
            assert result['title'] == meeting_data['title']
            assert result['description'] == meeting_data['description']
            assert result['creator_id'] == meeting_data['creator_id']
            assert isinstance(result['start_time'], datetime)
            assert isinstance(result['end_time'], datetime)
            assert result['location'] == meeting_data['location']
            assert result['meeting_type'] == meeting_data['meeting_type']
            assert result['recurring'] == meeting_data['recurring']
    
    def test_meeting_schema_validation_errors(self, app):
        """Test validation errors with the meeting schema."""
        with app.app_context():
            from src.schemas.meeting import MeetingSchema
            
            # Set up test data with errors
            
            # Missing required fields
            missing_fields_data = {
                'description': 'This is a test meeting',
                # Missing title, creator_id, start_time, end_time
                'location': 'Conference Room A'
            }
            
            # Invalid field values
            invalid_values_data = {
                'title': 'A' * 256,  # Title too long
                'description': 'This is a test meeting',
                'creator_id': 'not-a-uuid',  # Invalid UUID
                'start_time': 'not-a-datetime',  # Invalid datetime
                'end_time': datetime.utcnow().isoformat(),  # In the past
                'location': 'Conference Room A',
                'meeting_type': 'invalid-type',  # Invalid meeting type
                'recurring': 'not-a-boolean'  # Invalid boolean
            }
            
            # End time before start time
            invalid_times_data = {
                'title': 'Test Meeting',
                'description': 'This is a test meeting',
                'creator_id': str(uuid.uuid4()),
                'start_time': (datetime.utcnow() + timedelta(days=2)).isoformat(),
                'end_time': (datetime.utcnow() + timedelta(days=1)).isoformat(),  # End before start
                'location': 'Conference Room A',
                'meeting_type': 'team',
                'recurring': False
            }
            
            # Create schema instance
            schema = MeetingSchema()
            
            # Test missing fields
            with pytest.raises(ValidationError) as excinfo:
                schema.load(missing_fields_data)
            errors = excinfo.value.messages
            assert 'title' in errors
            assert 'creator_id' in errors
            assert 'start_time' in errors
            assert 'end_time' in errors
            
            # Test invalid values
            with pytest.raises(ValidationError) as excinfo:
                schema.load(invalid_values_data)
            errors = excinfo.value.messages
            assert 'title' in errors or 'creator_id' in errors or 'start_time' in errors or 'meeting_type' in errors
            
            # Test end time before start time
            with pytest.raises(ValidationError) as excinfo:
                schema.load(invalid_times_data)
            errors = excinfo.value.messages
            assert 'end_time' in errors or '_schema' in errors
    
    def test_meeting_schema_serialization(self, app, db):
        """Test serializing a meeting with the schema."""
        with app.app_context():
            from src.models.meeting import Meeting
            from src.schemas.meeting import MeetingSchema
            
            # Create a meeting
            start_time = datetime.utcnow() + timedelta(days=1)
            end_time = start_time + timedelta(hours=1)
            creator_id = str(uuid.uuid4())
            
            meeting = Meeting(
                title="Test Meeting",
                description="This is a test meeting",
                creator_id=creator_id,
                start_time=start_time,
                end_time=end_time,
                location="Conference Room A",
                meeting_type="team",
                recurring=False
            )
            
            # Add to database
            db.session.add(meeting)
            db.session.commit()
            
            # Create schema instance
            schema = MeetingSchema()
            
            # Serialize the meeting
            result = schema.dump(meeting)
            
            # Check that the result contains the expected data
            assert result['id'] == meeting.id
            assert result['title'] == "Test Meeting"
            assert result['description'] == "This is a test meeting"
            assert result['creator_id'] == creator_id
            assert 'start_time' in result
            assert 'end_time' in result
            assert result['location'] == "Conference Room A"
            assert result['meeting_type'] == "team"
            assert result['recurring'] is False
            assert 'created_at' in result
            assert 'updated_at' in result


class TestParticipantSchema:
    """Unit tests for the Participant schema."""
    
    def test_participant_schema_validation_success(self, app, db):
        """Test validating a valid participant with the schema."""
        with app.app_context():
            from src.models.meeting import Meeting
            from src.schemas.participant import ParticipantSchema
            
            # Create a meeting for testing
            meeting = Meeting(
                title="Test Meeting",
                description="This is a test meeting",
                creator_id=str(uuid.uuid4()),
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=1, hours=1),
                location="Conference Room A",
                meeting_type="team",
                recurring=False
            )
            
            db.session.add(meeting)
            db.session.commit()
            
            # Valid participant data
            participant_data = {
                'meeting_id': meeting.id,
                'user_id': str(uuid.uuid4()),
                'email': 'participant@example.com',
                'name': 'Test Participant',
                'role': 'attendee',
                'status': 'pending'
            }
            
            # Create schema instance
            schema = ParticipantSchema()
            
            # Validate and deserialize data
            result = schema.load(participant_data)
            
            # Check that the result contains the expected data
            assert result['meeting_id'] == participant_data['meeting_id']
            assert result['user_id'] == participant_data['user_id']
            assert result['email'] == participant_data['email']
            assert result['name'] == participant_data['name']
            assert result['role'] == participant_data['role']
            assert result['status'] == participant_data['status']
    
    def test_participant_schema_validation_errors(self, app):
        """Test validation errors with the participant schema."""
        with app.app_context():
            from src.schemas.participant import ParticipantSchema
            
            # Set up test data with errors
            
            # Missing required fields
            missing_fields_data = {
                # Missing meeting_id, email
                'name': 'Test Participant',
                'role': 'attendee'
            }
            
            # Invalid field values
            invalid_values_data = {
                'meeting_id': -1,  # Invalid ID
                'user_id': 'not-a-uuid',  # Invalid UUID
                'email': 'not-an-email',  # Invalid email
                'name': 'A' * 256,  # Name too long
                'role': 'invalid-role',  # Invalid role
                'status': 'invalid-status'  # Invalid status
            }
            
            # Create schema instance
            schema = ParticipantSchema()
            
            # Test missing fields
            with pytest.raises(ValidationError) as excinfo:
                schema.load(missing_fields_data)
            errors = excinfo.value.messages
            assert 'meeting_id' in errors
            assert 'email' in errors
            
            # Test invalid values
            with pytest.raises(ValidationError) as excinfo:
                schema.load(invalid_values_data)
            errors = excinfo.value.messages
            assert 'meeting_id' in errors or 'user_id' in errors or 'email' in errors or 'role' in errors or 'status' in errors
    
    def test_participant_schema_serialization(self, app, db):
        """Test serializing a participant with the schema."""
        with app.app_context():
            from src.models.meeting import Meeting, Participant
            from src.schemas.participant import ParticipantSchema
            
            # Create a meeting for testing
            meeting = Meeting(
                title="Test Meeting",
                description="This is a test meeting",
                creator_id=str(uuid.uuid4()),
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=1, hours=1),
                location="Conference Room A",
                meeting_type="team",
                recurring=False
            )
            
            db.session.add(meeting)
            db.session.commit()
            
            # Create a participant
            user_id = str(uuid.uuid4())
            participant = Participant(
                meeting_id=meeting.id,
                user_id=user_id,
                email="participant@example.com",
                name="Test Participant",
                role="attendee",
                status="pending"
            )
            
            db.session.add(participant)
            db.session.commit()
            
            # Create schema instance
            schema = ParticipantSchema()
            
            # Serialize the participant
            result = schema.dump(participant)
            
            # Check that the result contains the expected data
            assert result['id'] == participant.id
            assert result['meeting_id'] == meeting.id
            assert result['user_id'] == user_id
            assert result['email'] == "participant@example.com"
            assert result['name'] == "Test Participant"
            assert result['role'] == "attendee"
            assert result['status'] == "pending"
            assert 'created_at' in result


class TestAgendaItemSchema:
    """Unit tests for the AgendaItem schema."""
    
    def test_agenda_item_schema_validation_success(self, app, db):
        """Test validating a valid agenda item with the schema."""
        with app.app_context():
            from src.models.meeting import Meeting
            from src.schemas.agenda import AgendaItemSchema
            
            # Create a meeting for testing
            meeting = Meeting(
                title="Test Meeting",
                description="This is a test meeting",
                creator_id=str(uuid.uuid4()),
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=1, hours=1),
                location="Conference Room A",
                meeting_type="team",
                recurring=False
            )
            
            db.session.add(meeting)
            db.session.commit()
            
            # Valid agenda item data
            agenda_item_data = {
                'meeting_id': meeting.id,
                'title': 'Test Agenda Item',
                'description': 'This is a test agenda item',
                'duration': 15,
                'order': 1,
                'presenter_id': str(uuid.uuid4())
            }
            
            # Create schema instance
            schema = AgendaItemSchema()
            
            # Validate and deserialize data
            result = schema.load(agenda_item_data)
            
            # Check that the result contains the expected data
            assert result['meeting_id'] == agenda_item_data['meeting_id']
            assert result['title'] == agenda_item_data['title']
            assert result['description'] == agenda_item_data['description']
            assert result['duration'] == agenda_item_data['duration']
            assert result['order'] == agenda_item_data['order']
            assert result['presenter_id'] == agenda_item_data['presenter_id']
    
    def test_agenda_item_schema_validation_errors(self, app):
        """Test validation errors with the agenda item schema."""
        with app.app_context():
            from src.schemas.agenda import AgendaItemSchema
            
            # Set up test data with errors
            
            # Missing required fields
            missing_fields_data = {
                # Missing meeting_id, title
                'description': 'This is a test agenda item',
                'duration': 15
            }
            
            # Invalid field values
            invalid_values_data = {
                'meeting_id': -1,  # Invalid ID
                'title': 'A' * 256,  # Title too long
                'description': 'This is a test agenda item',
                'duration': -5,  # Negative duration
                'order': -1,  # Negative order
                'presenter_id': 'not-a-uuid'  # Invalid UUID
            }
            
            # Create schema instance
            schema = AgendaItemSchema()
            
            # Test missing fields
            with pytest.raises(ValidationError) as excinfo:
                schema.load(missing_fields_data)
            errors = excinfo.value.messages
            assert 'meeting_id' in errors
            assert 'title' in errors
            
            # Test invalid values
            with pytest.raises(ValidationError) as excinfo:
                schema.load(invalid_values_data)
            errors = excinfo.value.messages
            assert 'meeting_id' in errors or 'title' in errors or 'duration' in errors or 'order' in errors or 'presenter_id' in errors
    
    def test_agenda_item_schema_serialization(self, app, db):
        """Test serializing an agenda item with the schema."""
        with app.app_context():
            from src.models.meeting import Meeting, AgendaItem
            from src.schemas.agenda import AgendaItemSchema
            
            # Create a meeting for testing
            meeting = Meeting(
                title="Test Meeting",
                description="This is a test meeting",
                creator_id=str(uuid.uuid4()),
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=1, hours=1),
                location="Conference Room A",
                meeting_type="team",
                recurring=False
            )
            
            db.session.add(meeting)
            db.session.commit()
            
            # Create an agenda item
            presenter_id = str(uuid.uuid4())
            agenda_item = AgendaItem(
                meeting_id=meeting.id,
                title="Test Agenda Item",
                description="This is a test agenda item",
                duration=15,
                order=1,
                presenter_id=presenter_id
            )
            
            db.session.add(agenda_item)
            db.session.commit()
            
            # Create schema instance
            schema = AgendaItemSchema()
            
            # Serialize the agenda item
            result = schema.dump(agenda_item)
            
            # Check that the result contains the expected data
            assert result['id'] == agenda_item.id
            assert result['meeting_id'] == meeting.id
            assert result['title'] == "Test Agenda Item"
            assert result['description'] == "This is a test agenda item"
            assert result['duration'] == 15
            assert result['order'] == 1
            assert result['presenter_id'] == presenter_id
            assert 'created_at' in result 