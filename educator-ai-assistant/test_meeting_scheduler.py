#!/usr/bin/env python3
"""
Test script for Meeting Scheduler API endpoints
"""
import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8003"
LOGIN_URL = f"{BASE_URL}/api/v1/educators/login"
MEETINGS_URL = f"{BASE_URL}/api/v1/meetings"

def test_login():
    """Test login and get authentication token"""
    print("🔐 Testing login...")
    
    # Test with the educator we know exists (Ananya Rao)
    login_data = {
        "username": "ananya.rao@school.com",
        "password": "password123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(LOGIN_URL, data=login_data, headers=headers)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login successful! Token: {token_data.get('access_token', 'No token')[:50]}...")
            return token_data.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_meetings_endpoints(token):
    """Test meeting scheduler API endpoints"""
    if not token:
        print("❌ No token available, skipping meetings tests")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n📅 Testing meeting creation...")
    
    # Test meeting creation
    meeting_data = {
        "title": "Test Parent Meeting",
        "description": "Discussion about student progress",
        "meeting_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "meeting_type": "section",
        "recipient_type": "section",
        "section_id": 1,  # Mathematics Section A
        "allow_rsvp": True,
        "send_reminders": True,
        "created_via": "dashboard"
    }
    
    try:
        # Create meeting
        response = requests.post(MEETINGS_URL, json=meeting_data, headers=headers)
        print(f"Create meeting status: {response.status_code}")
        
        if response.status_code == 200:
            meeting_result = response.json()
            print(f"✅ Meeting created successfully!")
            print(f"   Meeting ID: {meeting_result.get('meeting_id')}")
            print(f"   Recipients: {len(meeting_result.get('recipients', []))}")
            
            meeting_id = meeting_result.get('meeting_id')
            
            # Test getting meetings list
            print("\n📋 Testing meetings list...")
            response = requests.get(MEETINGS_URL, headers=headers)
            if response.status_code == 200:
                meetings = response.json()
                print(f"✅ Retrieved {len(meetings)} meetings")
                for meeting in meetings:
                    print(f"   - {meeting.get('title')} ({meeting.get('status')})")
            
            # Test getting meeting recipients
            if meeting_id:
                print(f"\n👥 Testing meeting recipients for meeting {meeting_id}...")
                recipients_url = f"{MEETINGS_URL}/{meeting_id}/recipients"
                response = requests.get(recipients_url, headers=headers)
                if response.status_code == 200:
                    recipients = response.json()
                    print(f"✅ Retrieved {len(recipients)} recipients")
                    for recipient in recipients:
                        print(f"   - {recipient.get('recipient_name')} ({recipient.get('rsvp_status')})")
        else:
            print(f"❌ Meeting creation failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Meetings API error: {e}")

def main():
    """Main test function"""
    print("🧪 Testing Meeting Scheduler API")
    print("=" * 50)
    
    # Test login
    token = test_login()
    
    # Test meetings API
    test_meetings_endpoints(token)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()