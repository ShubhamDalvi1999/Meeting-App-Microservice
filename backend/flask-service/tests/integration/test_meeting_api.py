"""
Integration tests for the meeting API endpoints.
"""

import pytest
import json
from datetime import datetime, timedelta

# Add pytest mark for test categories
pytestmark = [pytest.mark.integration, pytest.mark.meetings, pytest.mark.api]


class TestMeetingAPI:
    """Integration tests for the meeting API endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'version' in data
        assert 'timestamp' in data
        assert 'request_id' in data
    
    def test_create_meeting(self, client, db, mock_auth_service, auth_header):
        """Test creating a meeting."""
        # Setup future date for the meeting
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        meeting_data = {
            'title': 'Test Meeting',
            'description': 'This is a test meeting',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'location': 'Conference Room A',
            'meeting_type': 'team',
            'recurring': False
        }
        
        response = client.post(
            '/api/meetings',
            data=json.dumps(meeting_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['title'] == meeting_data['title']
        assert data['description'] == meeting_data['description']
        assert 'id' in data
        assert 'creator_id' in data
        assert 'created_at' in data
        assert 'participants' in data
    
    def test_create_meeting_invalid_data(self, client, db, auth_header):
        """Test creating a meeting with invalid data."""
        # Missing required fields
        meeting_data = {
            'description': 'This is a test meeting',
            # Missing title and start_time
            'end_time': (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
        
        response = client.post(
            '/api/meetings',
            data=json.dumps(meeting_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'validation error' in data['message'].lower()
        
        # End time before start time
        meeting_data = {
            'title': 'Invalid Meeting',
            'description': 'This is a test meeting',
            'start_time': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'location': 'Conference Room A'
        }
        
        response = client.post(
            '/api/meetings',
            data=json.dumps(meeting_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'validation error' in data['message'].lower()
        assert 'end_time' in str(data['details']).lower()
    
    def test_get_meeting(self, client, test_meeting, auth_header):
        """Test getting a specific meeting."""
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == test_meeting['id']
        assert data['title'] == test_meeting['title']
        assert data['description'] == test_meeting['description']
        assert 'creator_id' in data
        assert 'start_time' in data
        assert 'end_time' in data
        assert 'participants' in data
    
    def test_get_nonexistent_meeting(self, client, auth_header):
        """Test getting a meeting that doesn't exist."""
        response = client.get(
            '/api/meetings/999999',
            headers=auth_header
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['message'].lower()
    
    def test_update_meeting(self, client, test_meeting, auth_header):
        """Test updating a meeting."""
        update_data = {
            'title': 'Updated Meeting Title',
            'description': 'Updated meeting description',
            'location': 'Updated Location'
        }
        
        response = client.put(
            f'/api/meetings/{test_meeting["id"]}',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == update_data['title']
        assert data['description'] == update_data['description']
        assert data['location'] == update_data['location']
        
        # Other fields should remain unchanged
        assert data['id'] == test_meeting['id']
        assert data['creator_id'] == test_meeting['creator_id']
        
        # Verify changes were persisted
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}',
            headers=auth_header
        )
        
        data = json.loads(response.data)
        assert data['title'] == update_data['title']
        assert data['description'] == update_data['description']
        assert data['location'] == update_data['location']
    
    def test_update_nonexistent_meeting(self, client, auth_header):
        """Test updating a meeting that doesn't exist."""
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated description'
        }
        
        response = client.put(
            '/api/meetings/999999',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['message'].lower()
    
    def test_delete_meeting(self, client, test_meeting, auth_header):
        """Test deleting a meeting."""
        response = client.delete(
            f'/api/meetings/{test_meeting["id"]}',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'deleted' in data['message'].lower()
        
        # Verify meeting is gone
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}',
            headers=auth_header
        )
        
        assert response.status_code == 404
    
    def test_delete_nonexistent_meeting(self, client, auth_header):
        """Test deleting a meeting that doesn't exist."""
        response = client.delete(
            '/api/meetings/999999',
            headers=auth_header
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['message'].lower()
    
    def test_list_meetings(self, client, test_meeting, auth_header):
        """Test listing all meetings for the current user."""
        response = client.get(
            '/api/meetings',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # The test meeting should be in the list
        meeting_ids = [m['id'] for m in data]
        assert test_meeting['id'] in meeting_ids
    
    def test_add_participant(self, client, test_meeting, auth_header):
        """Test adding a participant to a meeting."""
        participant_data = {
            'email': 'participant@example.com',
            'role': 'attendee'
        }
        
        response = client.post(
            f'/api/meetings/{test_meeting["id"]}/participants',
            data=json.dumps(participant_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['email'] == participant_data['email']
        assert data['role'] == participant_data['role']
        assert data['meeting_id'] == test_meeting['id']
        assert 'id' in data
        assert 'status' in data
        
        # Verify participant was added to the meeting
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}',
            headers=auth_header
        )
        
        data = json.loads(response.data)
        participants = data['participants']
        participant_emails = [p['email'] for p in participants]
        assert participant_data['email'] in participant_emails
    
    def test_add_participant_invalid_data(self, client, test_meeting, auth_header):
        """Test adding a participant with invalid data."""
        # Missing required fields
        participant_data = {
            # Missing email
            'role': 'attendee'
        }
        
        response = client.post(
            f'/api/meetings/{test_meeting["id"]}/participants',
            data=json.dumps(participant_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'validation error' in data['message'].lower()
        
        # Invalid email format
        participant_data = {
            'email': 'not-an-email',
            'role': 'attendee'
        }
        
        response = client.post(
            f'/api/meetings/{test_meeting["id"]}/participants',
            data=json.dumps(participant_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'validation error' in data['message'].lower()
        assert 'email' in str(data['details']).lower()
    
    def test_get_participants(self, client, test_meeting, test_participant, auth_header):
        """Test getting all participants for a meeting."""
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}/participants',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # The test participant should be in the list
        participant_ids = [p['id'] for p in data]
        assert test_participant['id'] in participant_ids
    
    def test_update_participant(self, client, test_meeting, test_participant, auth_header):
        """Test updating a participant."""
        update_data = {
            'role': 'presenter',
            'status': 'confirmed'
        }
        
        response = client.put(
            f'/api/meetings/{test_meeting["id"]}/participants/{test_participant["id"]}',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['role'] == update_data['role']
        assert data['status'] == update_data['status']
        assert data['id'] == test_participant['id']
        assert data['email'] == test_participant['email']
    
    def test_delete_participant(self, client, test_meeting, test_participant, auth_header):
        """Test removing a participant from a meeting."""
        response = client.delete(
            f'/api/meetings/{test_meeting["id"]}/participants/{test_participant["id"]}',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'removed' in data['message'].lower()
        
        # Verify participant is gone
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}/participants',
            headers=auth_header
        )
        
        data = json.loads(response.data)
        participant_ids = [p['id'] for p in data]
        assert test_participant['id'] not in participant_ids
    
    def test_add_agenda_item(self, client, test_meeting, auth_header):
        """Test adding an agenda item to a meeting."""
        agenda_data = {
            'title': 'Test Agenda Item',
            'description': 'This is a test agenda item',
            'duration': 15,
            'order': 1
        }
        
        response = client.post(
            f'/api/meetings/{test_meeting["id"]}/agenda',
            data=json.dumps(agenda_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['title'] == agenda_data['title']
        assert data['description'] == agenda_data['description']
        assert data['duration'] == agenda_data['duration']
        assert data['order'] == agenda_data['order']
        assert data['meeting_id'] == test_meeting['id']
        assert 'id' in data
    
    def test_get_agenda(self, client, test_meeting, test_agenda, auth_header):
        """Test getting the agenda for a meeting."""
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}/agenda',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # The test agenda item should be in the list
        agenda_ids = [a['id'] for a in data]
        assert test_agenda['id'] in agenda_ids
    
    def test_update_agenda_item(self, client, test_meeting, test_agenda, auth_header):
        """Test updating an agenda item."""
        update_data = {
            'title': 'Updated Agenda Title',
            'description': 'Updated agenda description',
            'duration': 30
        }
        
        response = client.put(
            f'/api/meetings/{test_meeting["id"]}/agenda/{test_agenda["id"]}',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == update_data['title']
        assert data['description'] == update_data['description']
        assert data['duration'] == update_data['duration']
        assert data['id'] == test_agenda['id']
        assert data['meeting_id'] == test_meeting['id']
    
    def test_delete_agenda_item(self, client, test_meeting, test_agenda, auth_header):
        """Test deleting an agenda item."""
        response = client.delete(
            f'/api/meetings/{test_meeting["id"]}/agenda/{test_agenda["id"]}',
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'deleted' in data['message'].lower()
        
        # Verify agenda item is gone
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}/agenda',
            headers=auth_header
        )
        
        data = json.loads(response.data)
        agenda_ids = [a['id'] for a in data]
        assert test_agenda['id'] not in agenda_ids
    
    def test_unauthorized_access(self, client, test_meeting):
        """Test accessing protected endpoints without authentication."""
        # Try accessing meeting without token
        response = client.get(f'/api/meetings/{test_meeting["id"]}')
        assert response.status_code == 401
        
        # Try with invalid token
        response = client.get(
            f'/api/meetings/{test_meeting["id"]}',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        assert response.status_code == 401 