"""
Unit tests for the database models in the Flask service.
"""

import pytest
from datetime import datetime, timedelta
import uuid

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.model]


class TestMeetingModel:
    """Unit tests for the Meeting model."""
    
    def test_meeting_creation(self, app, db):
        """Test creating a new meeting."""
        with app.app_context():
            from src.models.meeting import Meeting
            
            # Create a meeting
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
            
            # Add to database
            db.session.add(meeting)
            db.session.commit()
            
            # Verify the meeting was created
            assert meeting.id is not None
            
            # Fetch the meeting from the database
            fetched_meeting = Meeting.query.get(meeting.id)
            
            # Check that the attributes match
            assert fetched_meeting.title == "Test Meeting"
            assert fetched_meeting.description == "This is a test meeting"
            assert fetched_meeting.location == "Conference Room A"
            assert fetched_meeting.meeting_type == "team"
            assert fetched_meeting.recurring is False
            assert isinstance(fetched_meeting.created_at, datetime)
            assert isinstance(fetched_meeting.updated_at, datetime)
    
    def test_meeting_to_dict(self, app, db):
        """Test the to_dict method of the Meeting model."""
        with app.app_context():
            from src.models.meeting import Meeting
            
            # Create a meeting
            now = datetime.utcnow()
            creator_id = str(uuid.uuid4())
            start_time = now + timedelta(days=1)
            end_time = now + timedelta(days=1, hours=1)
            
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
            
            # Convert to dictionary
            meeting_dict = meeting.to_dict()
            
            # Check the dictionary
            assert meeting_dict['id'] == meeting.id
            assert meeting_dict['title'] == "Test Meeting"
            assert meeting_dict['description'] == "This is a test meeting"
            assert meeting_dict['creator_id'] == creator_id
            assert meeting_dict['location'] == "Conference Room A"
            assert meeting_dict['meeting_type'] == "team"
            assert meeting_dict['recurring'] is False
            assert 'created_at' in meeting_dict
            assert 'updated_at' in meeting_dict
            assert 'start_time' in meeting_dict
            assert 'end_time' in meeting_dict
    
    def test_meeting_update(self, app, db):
        """Test updating a meeting."""
        with app.app_context():
            from src.models.meeting import Meeting
            
            # Create a meeting
            meeting = Meeting(
                title="Original Title",
                description="Original description",
                creator_id=str(uuid.uuid4()),
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=1, hours=1),
                location="Original Location",
                meeting_type="team",
                recurring=False
            )
            
            # Add to database
            db.session.add(meeting)
            db.session.commit()
            
            # Update the meeting
            meeting.title = "Updated Title"
            meeting.description = "Updated description"
            meeting.location = "Updated Location"
            original_updated_at = meeting.updated_at
            
            # Save the changes
            db.session.commit()
            
            # Fetch the meeting from the database
            fetched_meeting = Meeting.query.get(meeting.id)
            
            # Check that the attributes were updated
            assert fetched_meeting.title == "Updated Title"
            assert fetched_meeting.description == "Updated description"
            assert fetched_meeting.location == "Updated Location"
            assert fetched_meeting.updated_at > original_updated_at
    
    def test_meeting_deletion(self, app, db):
        """Test deleting a meeting."""
        with app.app_context():
            from src.models.meeting import Meeting
            
            # Create a meeting
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
            
            # Add to database
            db.session.add(meeting)
            db.session.commit()
            
            # Get the meeting ID
            meeting_id = meeting.id
            
            # Delete the meeting
            db.session.delete(meeting)
            db.session.commit()
            
            # Try to fetch the meeting from the database
            fetched_meeting = Meeting.query.get(meeting_id)
            
            # Check that the meeting was deleted
            assert fetched_meeting is None


class TestParticipantModel:
    """Unit tests for the Participant model."""
    
    def test_participant_creation(self, app, db):
        """Test creating a new participant."""
        with app.app_context():
            from src.models.meeting import Meeting, Participant
            
            # Create a meeting first
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
            
            # Add meeting to database
            db.session.add(meeting)
            db.session.commit()
            
            # Create a participant
            participant = Participant(
                meeting_id=meeting.id,
                user_id=str(uuid.uuid4()),
                email="participant@example.com",
                name="Test Participant",
                role="attendee",
                status="pending"
            )
            
            # Add participant to database
            db.session.add(participant)
            db.session.commit()
            
            # Verify the participant was created
            assert participant.id is not None
            
            # Fetch the participant from the database
            fetched_participant = Participant.query.get(participant.id)
            
            # Check that the attributes match
            assert fetched_participant.meeting_id == meeting.id
            assert fetched_participant.email == "participant@example.com"
            assert fetched_participant.name == "Test Participant"
            assert fetched_participant.role == "attendee"
            assert fetched_participant.status == "pending"
            assert isinstance(fetched_participant.created_at, datetime)
    
    def test_participant_to_dict(self, app, db):
        """Test the to_dict method of the Participant model."""
        with app.app_context():
            from src.models.meeting import Meeting, Participant
            
            # Create a meeting first
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
            
            # Add meeting to database
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
            
            # Add participant to database
            db.session.add(participant)
            db.session.commit()
            
            # Convert to dictionary
            participant_dict = participant.to_dict()
            
            # Check the dictionary
            assert participant_dict['id'] == participant.id
            assert participant_dict['meeting_id'] == meeting.id
            assert participant_dict['user_id'] == user_id
            assert participant_dict['email'] == "participant@example.com"
            assert participant_dict['name'] == "Test Participant"
            assert participant_dict['role'] == "attendee"
            assert participant_dict['status'] == "pending"
            assert 'created_at' in participant_dict
    
    def test_meeting_participants_relationship(self, app, db):
        """Test the relationship between meetings and participants."""
        with app.app_context():
            from src.models.meeting import Meeting, Participant
            
            # Create a meeting
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
            
            # Add meeting to database
            db.session.add(meeting)
            db.session.commit()
            
            # Create multiple participants
            participants = [
                Participant(
                    meeting_id=meeting.id,
                    user_id=str(uuid.uuid4()),
                    email=f"participant{i}@example.com",
                    name=f"Participant {i}",
                    role="attendee",
                    status="pending"
                )
                for i in range(3)
            ]
            
            # Add participants to database
            db.session.add_all(participants)
            db.session.commit()
            
            # Fetch the meeting with participants
            fetched_meeting = Meeting.query.get(meeting.id)
            
            # Check that the participants are related to the meeting
            assert len(fetched_meeting.participants) == 3
            
            # Check each participant
            for i, participant in enumerate(fetched_meeting.participants):
                assert participant.email == f"participant{i}@example.com"
                assert participant.name == f"Participant {i}"
                assert participant.meeting == fetched_meeting


class TestAgendaItemModel:
    """Unit tests for the AgendaItem model."""
    
    def test_agenda_item_creation(self, app, db):
        """Test creating a new agenda item."""
        with app.app_context():
            from src.models.meeting import Meeting, AgendaItem
            
            # Create a meeting first
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
            
            # Add meeting to database
            db.session.add(meeting)
            db.session.commit()
            
            # Create an agenda item
            agenda_item = AgendaItem(
                meeting_id=meeting.id,
                title="Test Agenda Item",
                description="This is a test agenda item",
                duration=15,
                order=1,
                presenter_id=str(uuid.uuid4())
            )
            
            # Add agenda item to database
            db.session.add(agenda_item)
            db.session.commit()
            
            # Verify the agenda item was created
            assert agenda_item.id is not None
            
            # Fetch the agenda item from the database
            fetched_agenda_item = AgendaItem.query.get(agenda_item.id)
            
            # Check that the attributes match
            assert fetched_agenda_item.meeting_id == meeting.id
            assert fetched_agenda_item.title == "Test Agenda Item"
            assert fetched_agenda_item.description == "This is a test agenda item"
            assert fetched_agenda_item.duration == 15
            assert fetched_agenda_item.order == 1
            assert isinstance(fetched_agenda_item.created_at, datetime)
    
    def test_agenda_item_to_dict(self, app, db):
        """Test the to_dict method of the AgendaItem model."""
        with app.app_context():
            from src.models.meeting import Meeting, AgendaItem
            
            # Create a meeting first
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
            
            # Add meeting to database
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
            
            # Add agenda item to database
            db.session.add(agenda_item)
            db.session.commit()
            
            # Convert to dictionary
            agenda_item_dict = agenda_item.to_dict()
            
            # Check the dictionary
            assert agenda_item_dict['id'] == agenda_item.id
            assert agenda_item_dict['meeting_id'] == meeting.id
            assert agenda_item_dict['title'] == "Test Agenda Item"
            assert agenda_item_dict['description'] == "This is a test agenda item"
            assert agenda_item_dict['duration'] == 15
            assert agenda_item_dict['order'] == 1
            assert agenda_item_dict['presenter_id'] == presenter_id
            assert 'created_at' in agenda_item_dict
    
    def test_meeting_agenda_items_relationship(self, app, db):
        """Test the relationship between meetings and agenda items."""
        with app.app_context():
            from src.models.meeting import Meeting, AgendaItem
            
            # Create a meeting
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
            
            # Add meeting to database
            db.session.add(meeting)
            db.session.commit()
            
            # Create multiple agenda items
            agenda_items = [
                AgendaItem(
                    meeting_id=meeting.id,
                    title=f"Agenda Item {i}",
                    description=f"Description for agenda item {i}",
                    duration=15,
                    order=i,
                    presenter_id=str(uuid.uuid4())
                )
                for i in range(1, 4)  # Items with orders 1, 2, 3
            ]
            
            # Add agenda items to database
            db.session.add_all(agenda_items)
            db.session.commit()
            
            # Fetch the meeting with agenda items
            fetched_meeting = Meeting.query.get(meeting.id)
            
            # Check that the agenda items are related to the meeting
            assert len(fetched_meeting.agenda_items) == 3
            
            # Check that items are ordered
            ordered_items = fetched_meeting.agenda_items
            for i, item in enumerate(ordered_items):
                assert item.order == i + 1
                assert item.title == f"Agenda Item {i + 1}"
                assert item.meeting == fetched_meeting 