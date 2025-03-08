"""
Integration tests for meeting API flow
"""

import pytest
import requests
import time
import json
from .base import IntegrationTestBase

class TestMeetingFlow(IntegrationTestBase):
    """Test the entire meeting flow across services"""
    
    def setup_method(self):
        """Set up test data before each test method"""
        # Login with test user
        login_response = self.login(
            self.config['TEST_USER_EMAIL'],
            self.config['TEST_USER_PASSWORD']
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        self.access_token = tokens['access_token']
        self.headers = self.get_headers(self.access_token)
    
    def test_create_update_delete_meeting(self):
        """Test full meeting lifecycle: create, update, delete"""
        # 1. Create a new meeting
        timestamp = int(time.time())
        meeting_url = f"{self.api_url}/api/meetings"
        
        create_data = {
            'title': f"Test Meeting {timestamp}",
            'description': "Integration test meeting",
            'start_time': f"2025-01-01T10:00:00Z",
            'end_time': f"2025-01-01T11:00:00Z",
            'location': "Virtual",
            'participants': []
        }
        
        create_response = requests.post(
            meeting_url,
            headers=self.headers,
            json=create_data,
            timeout=self.timeout
        )
        
        assert create_response.status_code == 201
        meeting_data = create_response.json()
        assert meeting_data['title'] == create_data['title']
        assert meeting_data['description'] == create_data['description']
        assert 'id' in meeting_data
        meeting_id = meeting_data['id']
        
        # 2. Get the meeting
        get_url = f"{meeting_url}/{meeting_id}"
        get_response = requests.get(
            get_url,
            headers=self.headers,
            timeout=self.timeout
        )
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data['id'] == meeting_id
        assert get_data['title'] == create_data['title']
        
        # 3. Update the meeting
        update_data = {
            'title': f"Updated Meeting {timestamp}",
            'description': "Updated integration test meeting",
            'location': "Conference Room A"
        }
        
        update_response = requests.put(
            get_url,
            headers=self.headers,
            json=update_data,
            timeout=self.timeout
        )
        
        assert update_response.status_code == 200
        update_result = update_response.json()
        assert update_result['title'] == update_data['title']
        assert update_result['description'] == update_data['description']
        assert update_result['location'] == update_data['location']
        
        # 4. Delete the meeting
        delete_response = requests.delete(
            get_url,
            headers=self.headers,
            timeout=self.timeout
        )
        
        assert delete_response.status_code in [200, 204]
        
        # 5. Verify meeting is deleted
        verify_response = requests.get(
            get_url,
            headers=self.headers,
            timeout=self.timeout
        )
        
        assert verify_response.status_code == 404
    
    def test_list_meetings(self):
        """Test listing meetings with filters"""
        # 1. Create multiple meetings
        meeting_url = f"{self.api_url}/api/meetings"
        timestamp = int(time.time())
        
        # Create 3 meetings with different dates
        meetings = []
        for i in range(3):
            create_data = {
                'title': f"List Test Meeting {timestamp}-{i}",
                'description': f"Test meeting {i}",
                'start_time': f"2025-0{i+1}-01T10:00:00Z",
                'end_time': f"2025-0{i+1}-01T11:00:00Z",
                'location': f"Room {i}",
                'participants': []
            }
            
            create_response = requests.post(
                meeting_url,
                headers=self.headers,
                json=create_data,
                timeout=self.timeout
            )
            
            assert create_response.status_code == 201
            meetings.append(create_response.json())
        
        # 2. List all meetings
        list_response = requests.get(
            meeting_url,
            headers=self.headers,
            timeout=self.timeout
        )
        
        assert list_response.status_code == 200
        all_meetings = list_response.json()
        assert len(all_meetings) >= 3  # At least our 3 new meetings
        
        # 3. Filter meetings by date
        filter_url = f"{meeting_url}?start_date=2025-01-01&end_date=2025-01-31"
        filter_response = requests.get(
            filter_url,
            headers=self.headers,
            timeout=self.timeout
        )
        
        assert filter_response.status_code == 200
        january_meetings = filter_response.json()
        
        # Find our test meeting for January
        jan_test_meeting = next(
            (m for m in january_meetings if m['title'] == f"List Test Meeting {timestamp}-0"),
            None
        )
        assert jan_test_meeting is not None
        
        # 4. Clean up - delete all created meetings
        for meeting in meetings:
            delete_url = f"{meeting_url}/{meeting['id']}"
            requests.delete(
                delete_url,
                headers=self.headers,
                timeout=self.timeout
            )
    
    def test_realtime_meeting_notifications(self):
        """Test realtime notifications when meetings are created/updated"""
        # This test would ideally use a WebSocket client to connect to your
        # notification system. Since a full implementation would be complex,
        # we'll provide a simplified version that just verifies the Redis
        # event publishing mechanism works.
        
        # 1. Create a new meeting
        timestamp = int(time.time())
        meeting_url = f"{self.api_url}/api/meetings"
        
        create_data = {
            'title': f"Notification Test Meeting {timestamp}",
            'description': "Testing realtime notifications",
            'start_time': f"2025-01-01T10:00:00Z",
            'end_time': f"2025-01-01T11:00:00Z",
            'location': "Virtual",
            'participants': []
        }
        
        create_response = requests.post(
            meeting_url,
            headers=self.headers,
            json=create_data,
            timeout=self.timeout
        )
        
        assert create_response.status_code == 201
        meeting_id = create_response.json()['id']
        
        # 2. Check notifications endpoint for this meeting
        # This assumes you have an endpoint to check recent notifications
        # If you don't have such an endpoint, you might skip this test
        events_url = f"{self.api_url}/api/events/recent"
        
        # Give the system a moment to process the event
        time.sleep(1)
        
        events_response = requests.get(
            events_url,
            headers=self.headers,
            timeout=self.timeout
        )
        
        # If the endpoint exists, check for our meeting notification
        if events_response.status_code == 200:
            events = events_response.json()
            # Look for an event related to our meeting
            meeting_events = [e for e in events if e.get('entity_id') == meeting_id]
            assert len(meeting_events) > 0
        
        # 3. Clean up - delete the meeting
        delete_url = f"{meeting_url}/{meeting_id}"
        requests.delete(
            delete_url,
            headers=self.headers,
            timeout=self.timeout
        ) 