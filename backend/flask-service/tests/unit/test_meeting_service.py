"""
Unit tests for the meeting service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add pytest mark for test categories
pytestmark = [pytest.mark.unit, pytest.mark.meetings, pytest.mark.service]


class TestMeetingService:
    """Unit tests for the meeting service."""
    
    def test_create_meeting(self, app, db):
        """Test creating a meeting."""
        with app.app_context():
            from src.services.meeting_service import create_meeting
            
            # Meeting data
            meeting_data = {
                'title': 'Test Meeting',
                'description': 'This is a test meeting',
                'start_time': datetime.utcnow() + timedelta(days=1),
                'end_time': datetime.utcnow() + timedelta(days=1, hours=1),
                'creator_id': 1,
                'location': 'Conference Room A',
                'meeting_type': 'team'
            }
            
            # Create meeting
            meeting = create_meeting(**meeting_data)
            
            # Verify meeting
            assert meeting is not None
            assert meeting.title == meeting_data['title']
            assert meeting.description == meeting_data['description']
            assert meeting.creator_id == meeting_data['creator_id']
            assert meeting.id is not None
    
    def test_get_meeting_by_id(self, app, db, test_meeting):
        """Test getting a meeting by ID."""
        with app.app_context():
            from src.services.meeting_service import get_meeting_by_id
            
            # Get meeting
            meeting = get_meeting_by_id(test_meeting['id'])
            
            # Verify meeting
            assert meeting is not None
            assert meeting.id == test_meeting['id']
            assert meeting.title == test_meeting['title']
    
    def test_get_meeting_by_id_nonexistent(self, app, db):
        """Test getting a nonexistent meeting by ID."""
        with app.app_context():
            from src.services.meeting_service import get_meeting_by_id
            
            # Attempt to get nonexistent meeting
            meeting = get_meeting_by_id(999)
            
            # Verify result
            assert meeting is None
    
    def test_update_meeting(self, app, db, test_meeting):
        """Test updating a meeting."""
        with app.app_context():
            from src.services.meeting_service import update_meeting
            
            # Update data
            update_data = {
                'title': 'Updated Meeting Title',
                'description': 'Updated meeting description'
            }
            
            # Update meeting
            meeting = update_meeting(test_meeting['id'], **update_data)
            
            # Verify update
            assert meeting is not None
            assert meeting.id == test_meeting['id']
            assert meeting.title == update_data['title']
            assert meeting.description == update_data['description']
    
    def test_update_meeting_nonexistent(self, app, db):
        """Test updating a nonexistent meeting."""
        with app.app_context():
            from src.services.meeting_service import update_meeting
            from src.core.errors import ResourceNotFoundError
            
            # Update data
            update_data = {
                'title': 'Updated Meeting Title',
                'description': 'Updated meeting description'
            }
            
            # Attempt to update nonexistent meeting
            with pytest.raises(ResourceNotFoundError):
                update_meeting(999, **update_data)
    
    def test_delete_meeting(self, app, db, test_meeting):
        """Test deleting a meeting."""
        with app.app_context():
            from src.services.meeting_service import delete_meeting, get_meeting_by_id
            
            # Delete meeting
            result = delete_meeting(test_meeting['id'])
            
            # Verify deletion
            assert result is True
            
            # Verify meeting no longer exists
            meeting = get_meeting_by_id(test_meeting['id'])
            assert meeting is None
    
    def test_delete_meeting_nonexistent(self, app, db):
        """Test deleting a nonexistent meeting."""
        with app.app_context():
            from src.services.meeting_service import delete_meeting
            from src.core.errors import ResourceNotFoundError
            
            # Attempt to delete nonexistent meeting
            with pytest.raises(ResourceNotFoundError):
                delete_meeting(999)
    
    def test_get_meetings_by_creator(self, app, db, test_meeting):
        """Test getting meetings by creator."""
        with app.app_context():
            from src.services.meeting_service import get_meetings_by_creator
            
            # Get meetings
            meetings = get_meetings_by_creator(test_meeting['creator_id'])
            
            # Verify meetings
            assert meetings is not None
            assert len(meetings) > 0
            assert any(m.id == test_meeting['id'] for m in meetings)
    
    def test_get_meetings_by_participant(self, app, db, test_meeting, test_participant):
        """Test getting meetings by participant."""
        with app.app_context():
            from src.services.meeting_service import get_meetings_by_participant
            
            # Get meetings
            meetings = get_meetings_by_participant(test_participant['user_id'])
            
            # Verify meetings
            assert meetings is not None
            assert len(meetings) > 0
            assert any(m.id == test_meeting['id'] for m in meetings)
    
    def test_search_meetings(self, app, db, test_meeting):
        """Test searching meetings."""
        with app.app_context():
            from src.services.meeting_service import search_meetings
            
            # Search for meetings with a keyword in the title
            keyword = test_meeting['title'].split()[0]
            meetings = search_meetings(keyword)
            
            # Verify search results
            assert meetings is not None
            assert len(meetings) > 0
            assert any(m.id == test_meeting['id'] for m in meetings)
    
    def test_add_participant(self, app, db, test_meeting):
        """Test adding a participant to a meeting."""
        with app.app_context():
            from src.services.meeting_service import add_participant
            
            # Add participant
            user_id = 2  # A different user than the creator
            participant = add_participant(test_meeting['id'], user_id)
            
            # Verify participant
            assert participant is not None
            assert participant.meeting_id == test_meeting['id']
            assert participant.user_id == user_id
    
    def test_add_participant_duplicate(self, app, db, test_meeting, test_participant):
        """Test adding a duplicate participant to a meeting."""
        with app.app_context():
            from src.services.meeting_service import add_participant
            from src.core.errors import ResourceExistsError
            
            # Attempt to add duplicate participant
            with pytest.raises(ResourceExistsError):
                add_participant(test_meeting['id'], test_participant['user_id'])
    
    def test_add_agenda_item(self, app, db, test_meeting):
        """Test adding an agenda item to a meeting."""
        with app.app_context():
            from src.services.meeting_service import add_agenda_item
            
            # Agenda item data
            agenda_data = {
                'title': 'Test Agenda Item',
                'description': 'This is a test agenda item',
                'duration': 15,
                'order': 1,
                'presenter_id': 1
            }
            
            # Add agenda item
            agenda_item = add_agenda_item(test_meeting['id'], **agenda_data)
            
            # Verify agenda item
            assert agenda_item is not None
            assert agenda_item.meeting_id == test_meeting['id']
            assert agenda_item.title == agenda_data['title']
            assert agenda_item.duration == agenda_data['duration']
    
    def test_get_meeting_agenda(self, app, db, test_meeting, test_agenda):
        """Test getting a meeting's agenda."""
        with app.app_context():
            from src.services.meeting_service import get_meeting_agenda
            
            # Get agenda
            agenda_items = get_meeting_agenda(test_meeting['id'])
            
            # Verify agenda
            assert agenda_items is not None
            assert len(agenda_items) > 0
            assert any(a.id == test_agenda['id'] for a in agenda_items)
    
    def test_update_participant_status(self, app, db, test_meeting, test_participant):
        """Test updating a participant's status."""
        with app.app_context():
            from src.services.meeting_service import update_participant_status
            
            # Update status
            new_status = 'declined'
            participant = update_participant_status(test_meeting['id'], test_participant['user_id'], new_status)
            
            # Verify update
            assert participant is not None
            assert participant.meeting_id == test_meeting['id']
            assert participant.user_id == test_participant['user_id']
            assert participant.status == new_status 