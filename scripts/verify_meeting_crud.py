#!/usr/bin/env python
"""
Meeting CRUD verification script.
Tests the complete meeting management workflow.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import time

# Default URLs (can be overridden with environment variables)
BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:5000/api")
AUTH_URL = os.environ.get("AUTH_URL", "http://localhost:5001/api/auth")

# Test credentials (should be updated with valid credentials)
TEST_EMAIL = os.environ.get("TEST_EMAIL", "admin@example.com")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "admin123")

def log_response(response, operation):
    """Log API response details."""
    print(f"\n--- {operation} Response ---")
    print(f"Status: {response.status_code}")
    print(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
    
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body: {response.text[:200]}...")

def verify_meeting_crud():
    """Test the complete meeting CRUD workflow."""
    print("\n=== Starting Meeting CRUD Verification ===")
    
    # 1. Get auth token
    print("\nStep 1: Authenticating...")
    auth_response = requests.post(f"{AUTH_URL}/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if auth_response.status_code != 200:
        log_response(auth_response, "Authentication")
        print("❌ Authentication failed")
        return False
    
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # 2. Create meeting
    print("\nStep 2: Creating meeting...")
    meeting_data = {
        "title": "Test Meeting",
        "description": "Testing CRUD operations",
        "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        "location": "Conference Room A",
        "meeting_type": "team"
    }
    
    create_response = requests.post(f"{BASE_URL}/meetings", 
                                  json=meeting_data,
                                  headers=headers)
    
    if create_response.status_code != 201:
        log_response(create_response, "Create Meeting")
        print("❌ Meeting creation failed")
        return False
    
    meeting_id = create_response.json().get("id")
    print(f"✅ Created meeting with ID: {meeting_id}")
    
    # 3. Read meeting
    print("\nStep 3: Reading meeting...")
    read_response = requests.get(f"{BASE_URL}/meetings/{meeting_id}", headers=headers)
    if read_response.status_code != 200:
        log_response(read_response, "Read Meeting")
        print("❌ Meeting read failed")
        return False
    
    print("✅ Meeting read successful")
    
    # 4. Add participants
    print("\nStep 4: Adding participants...")
    participants = [
        {"user_id": 2, "role": "attendee"},
        {"user_id": 3, "role": "presenter"}
    ]
    
    participants_response = requests.post(
        f"{BASE_URL}/meetings/{meeting_id}/participants",
        json=participants,
        headers=headers
    )
    
    if participants_response.status_code not in [200, 201]:
        log_response(participants_response, "Add Participants")
        print("⚠️ Adding participants failed (continuing test)")
    else:
        print("✅ Participants added successfully")
    
    # 5. Update meeting
    print("\nStep 5: Updating meeting...")
    update_data = {"title": "Updated Test Meeting"}
    update_response = requests.put(f"{BASE_URL}/meetings/{meeting_id}", 
                                 json=update_data,
                                 headers=headers)
    
    if update_response.status_code != 200:
        log_response(update_response, "Update Meeting")
        print("❌ Meeting update failed")
        return False
    
    print("✅ Meeting update successful")
    
    # 6. Delete meeting
    print("\nStep 6: Deleting meeting...")
    delete_response = requests.delete(f"{BASE_URL}/meetings/{meeting_id}", headers=headers)
    if delete_response.status_code != 204:
        log_response(delete_response, "Delete Meeting")
        print("❌ Meeting deletion failed")
        return False
    
    print("✅ Meeting deletion successful")
    
    # 7. Verify deletion
    print("\nStep 7: Verifying deletion...")
    verify_response = requests.get(f"{BASE_URL}/meetings/{meeting_id}", headers=headers)
    if verify_response.status_code != 404:
        log_response(verify_response, "Verify Deletion")
        print("❌ Deletion verification failed")
        return False
        
    print("✅ Deletion verification successful")
    print("\n=== Meeting CRUD verification completed successfully! ===")
    return True

if __name__ == "__main__":
    try:
        if verify_meeting_crud():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during verification: {str(e)}")
        sys.exit(1) 