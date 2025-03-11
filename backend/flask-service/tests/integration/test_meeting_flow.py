"""
Integration tests for the meeting flow.
Tests the complete meeting flow including creation, updates, and notifications.
"""

import json
import os
from datetime import datetime, timedelta
from .base import IntegrationTestBase
import responses
import pytest

class TestMeetingFlow(IntegrationTestBase):
    """Test the complete meeting flow."""
    
    def create_app(self):
        """Create the Flask application for testing."""
        # Import here to avoid circular imports
        import sys
        import os
        
        # Add the src directory to the path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
        
        # Import the create_app function
        from app import create_app
        
        # Create the app with test configuration
        app = create_app('testing')
        
        # Override any config settings
        app.config.update(self.TEST_CONFIG)
        
        return app
    
    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        
        # Set up the database
        from src.models import db
        with self.app.app_context():
            db.create_all()
            
        # Mock the auth service for all tests
        self.mock_auth_token(user_id=1, email='test@example.com', name='Test User')
        
        # Mock the websocket service for notifications
        self.mock_service_response(
            service='websocket',
            endpoint='/api/notify',
            method='POST',
            status=200,
            json_data={'success': True}
        )
    
    def tearDown(self):
        """Clean up the test environment."""
        # Clean up the database
        from src.models import db
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        super().tearDown()
    
    def test_create_meeting_flow(self):
        """Test the complete meeting creation flow."""
        # 1. Create a meeting
        tomorrow = datetime.now() + timedelta(days=1)
        meeting_data = {
            'title': 'Test Meeting',
            'description': 'This is a test meeting',
            'start_time': tomorrow.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': (tomorrow + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
            'location': 'Conference Room A',
            'participants': ['test2@example.com', 'test3@example.com']
        }
        
        response = self.authenticated_request(
            'POST',
            '/api/meetings',
            json_data=meeting_data
        )
        
        self.assert_response_status(response, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertEqual(data['title'], meeting_data['title'])
        
        meeting_id = data['id']
        
        # 2. Get the meeting details
        response = self.authenticated_request(
            'GET',
            f'/api/meetings/{meeting_id}'
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['id'], meeting_id)
        self.assertEqual(data['title'], meeting_data['title'])
        self.assertEqual(data['description'], meeting_data['description'])
        self.assertEqual(data['location'], meeting_data['location'])
        self.assertEqual(len(data['participants']), len(meeting_data['participants']) + 1)  # +1 for the creator
        
        # 3. Update the meeting
        update_data = {
            'title': 'Updated Test Meeting',
            'location': 'Conference Room B'
        }
        
        response = self.authenticated_request(
            'PUT',
            f'/api/meetings/{meeting_id}',
            json_data=update_data
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['title'], update_data['title'])
        self.assertEqual(data['location'], update_data['location'])
        
        # 4. Get all meetings
        response = self.authenticated_request(
            'GET',
            '/api/meetings'
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # 5. Delete the meeting
        response = self.authenticated_request(
            'DELETE',
            f'/api/meetings/{meeting_id}'
        )
        
        self.assert_response_status(response, 200)
        
        # 6. Verify the meeting is deleted
        response = self.authenticated_request(
            'GET',
            f'/api/meetings/{meeting_id}'
        )
        
        self.assert_response_status(response, 404)
    
    def test_meeting_participant_flow(self):
        """Test the meeting participant flow."""
        # 1. Create a meeting
        tomorrow = datetime.now() + timedelta(days=1)
        meeting_data = {
            'title': 'Participant Test Meeting',
            'description': 'This is a test meeting for participants',
            'start_time': tomorrow.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': (tomorrow + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
            'location': 'Conference Room A',
            'participants': ['test2@example.com']
        }
        
        response = self.authenticated_request(
            'POST',
            '/api/meetings',
            json_data=meeting_data
        )
        
        self.assert_response_status(response, 201)
        data = json.loads(response.data.decode('utf-8'))
        meeting_id = data['id']
        
        # 2. Add a participant
        response = self.authenticated_request(
            'POST',
            f'/api/meetings/{meeting_id}/participants',
            json_data={'email': 'test3@example.com'}
        )
        
        self.assert_response_status(response, 200)
        
        # 3. Get participants
        response = self.authenticated_request(
            'GET',
            f'/api/meetings/{meeting_id}/participants'
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)  # Creator + 2 participants
        
        # 4. Remove a participant
        response = self.authenticated_request(
            'DELETE',
            f'/api/meetings/{meeting_id}/participants/test2@example.com'
        )
        
        self.assert_response_status(response, 200)
        
        # 5. Verify participant is removed
        response = self.authenticated_request(
            'GET',
            f'/api/meetings/{meeting_id}/participants'
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(data), 2)  # Creator + 1 participant
    
    def test_meeting_search(self):
        """Test meeting search functionality."""
        # 1. Create multiple meetings
        tomorrow = datetime.now() + timedelta(days=1)
        
        # Meeting 1
        meeting1_data = {
            'title': 'Project Alpha Kickoff',
            'description': 'Kickoff meeting for Project Alpha',
            'start_time': tomorrow.strftime('%Y-%m-%dT10:00:00'),
            'end_time': tomorrow.strftime('%Y-%m-%dT11:00:00'),
            'location': 'Conference Room A',
            'participants': ['test2@example.com']
        }
        
        response = self.authenticated_request(
            'POST',
            '/api/meetings',
            json_data=meeting1_data
        )
        
        self.assert_response_status(response, 201)
        
        # Meeting 2
        meeting2_data = {
            'title': 'Project Beta Planning',
            'description': 'Planning session for Project Beta',
            'start_time': tomorrow.strftime('%Y-%m-%dT14:00:00'),
            'end_time': tomorrow.strftime('%Y-%m-%dT15:00:00'),
            'location': 'Conference Room B',
            'participants': ['test3@example.com']
        }
        
        response = self.authenticated_request(
            'POST',
            '/api/meetings',
            json_data=meeting2_data
        )
        
        self.assert_response_status(response, 201)
        
        # Meeting 3
        meeting3_data = {
            'title': 'Project Alpha Review',
            'description': 'Review session for Project Alpha',
            'start_time': (tomorrow + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00'),
            'end_time': (tomorrow + timedelta(days=1)).strftime('%Y-%m-%dT11:00:00'),
            'location': 'Conference Room A',
            'participants': ['test2@example.com', 'test3@example.com']
        }
        
        response = self.authenticated_request(
            'POST',
            '/api/meetings',
            json_data=meeting3_data
        )
        
        self.assert_response_status(response, 201)
        
        # 2. Search by title
        response = self.authenticated_request(
            'GET',
            '/api/meetings/search?query=Alpha'
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(data), 2)  # Should find both Alpha meetings
        
        # 3. Search by date
        response = self.authenticated_request(
            'GET',
            f'/api/meetings/search?date={tomorrow.strftime("%Y-%m-%d")}'
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(data), 2)  # Should find both meetings on tomorrow
        
        # 4. Search by participant
        response = self.authenticated_request(
            'GET',
            '/api/meetings/search?participant=test3@example.com'
        )
        
        self.assert_response_status(response, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(data), 2)  # Should find both meetings with test3@example.com 

def test_complete_meeting_flow(client, auth_header):
    """Test complete meeting creation and management flow."""
    # Create a meeting
    meeting_data = {
        'title': 'Integration Test Meeting',
        'description': 'Testing full meeting workflow',
        'start_time': (datetime.utcnow() + timedelta(days=1)).isoformat(),
        'end_time': (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        'location': 'Conference Room A',
        'meeting_type': 'team'
    }
    
    response = client.post('/api/meetings', 
                         json=meeting_data,
                         headers=auth_header)
    assert response.status_code == 201
    meeting_id = response.json['id']
    
    # Add participants
    participants = [
        {'user_id': 2, 'role': 'attendee'},
        {'user_id': 3, 'role': 'presenter'}
    ]
    response = client.post(f'/api/meetings/{meeting_id}/participants',
                         json=participants,
                         headers=auth_header)
    assert response.status_code == 201
    
    # Add agenda items
    agenda_items = [
        {
            'title': 'Introduction',
            'description': 'Project overview',
            'duration': 15,
            'order': 1
        },
        {
            'title': 'Technical Discussion',
            'description': 'Architecture review',
            'duration': 30,
            'order': 2
        }
    ]
    response = client.post(f'/api/meetings/{meeting_id}/agenda',
                         json=agenda_items,
                         headers=auth_header)
    assert response.status_code == 201
    
    # Verify meeting details
    response = client.get(f'/api/meetings/{meeting_id}',
                        headers=auth_header)
    assert response.status_code == 200
    meeting = response.json
    
    assert meeting['title'] == meeting_data['title']
    assert len(meeting['participants']) == 2
    assert len(meeting['agenda_items']) == 2
    
    # Update meeting
    update_data = {
        'title': 'Updated Meeting Title',
        'description': 'Updated description'
    }
    response = client.put(f'/api/meetings/{meeting_id}',
                        json=update_data,
                        headers=auth_header)
    assert response.status_code == 200
    
    # Verify update
    response = client.get(f'/api/meetings/{meeting_id}',
                        headers=auth_header)
    assert response.status_code == 200
    assert response.json['title'] == update_data['title']
    
    # Delete meeting
    response = client.delete(f'/api/meetings/{meeting_id}',
                          headers=auth_header)
    assert response.status_code == 204
    
    # Verify deletion
    response = client.get(f'/api/meetings/{meeting_id}',
                        headers=auth_header)
    assert response.status_code == 404 