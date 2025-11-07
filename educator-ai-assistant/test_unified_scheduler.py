#!/usr/bin/env python3
"""
Test the unified task/meeting scheduler
"""

import requests
import json
from datetime import datetime, timedelta

def test_task_creation():
    # Login as educator first
    login_data = {
        "username": "ananya.rao@school.com", 
        "password": "Ananya@123"
    }

    print("🔐 Logging in as educator...")
    response = requests.post("http://localhost:8003/api/v1/educators/login", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return False
        
    token_data = response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login successful")
    
    # Test task creation
    future_datetime = datetime.now() + timedelta(hours=2)
    
    task_data = {
        "title": "Math Homework Assignment",
        "description": "Complete chapter 5 exercises 1-10",
        "start_datetime": future_datetime.isoformat(),
        "end_datetime": future_datetime.isoformat(),
        "location": "Online",
        "meeting_type": "section",
        "section_id": 1,  # Mathematics Section A
        "send_immediately": True
    }
    
    print("📋 Creating test task...")
    response = requests.post(
        "http://localhost:8003/api/v1/scheduling/tasks",
        headers=headers,
        json=task_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Task created successfully!")
        print(f"   Task ID: {result['id']}")
        print(f"   Title: {result['title']}")
        print(f"   Type: {result['task_type']}")
        return True
    else:
        print(f"❌ Task creation failed: {response.status_code}")
        print(response.text)
        return False

def test_student_sees_task():
    # Login as Rahul (student in section 1)
    login_data = {
        "email": "rahul.s101@school.com",
        "password": "student123"
    }
    
    print("\n🔐 Logging in as Rahul...")
    response = requests.post("http://localhost:8003/api/v1/student-auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Student login failed: {response.status_code}")
        return False
        
    token_data = response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Student login successful")
    
    # Check scheduled events
    print("📅 Fetching scheduled events...")
    response = requests.get(
        "http://localhost:8003/api/v1/student-dashboard/scheduled-events",
        headers=headers
    )
    
    if response.status_code == 200:
        events = response.json()
        print(f"✅ Found {len(events)} scheduled events")
        
        for event in events:
            print(f"   📋 {event['event_type'].upper()}: {event['title']}")
            print(f"       📅 {event['start_datetime']}")
            print(f"       👨‍🏫 {event['educator_name']}")
        return True
    else:
        print(f"❌ Failed to fetch events: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🧪 Testing unified task/meeting scheduler\n")
    
    success1 = test_task_creation()
    if success1:
        success2 = test_student_sees_task()
        
        if success1 and success2:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed")
    else:
        print("\n❌ Task creation failed, skipping student test")