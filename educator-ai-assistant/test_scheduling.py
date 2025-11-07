#!/usr/bin/env python3
"""
Test script to verify scheduling functionality
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8001"

def test_register_and_login():
    """Register a test user and login to get token"""
    # Try login first (user might already exist)
    login_data = {
        "username": "test@example.com",
        "password": "test123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/educators/login", data=login_data)
    print(f"Login response: {response.status_code}")
    
    if response.status_code == 200:
        return response.json().get("access_token")
    
    # If login fails, try to register
    register_data = {
        "first_name": "Test",
        "last_name": "Educator", 
        "email": "test@example.com",
        "password": "test123",
        "department": "Computer Science",
        "employee_id": "TEST001",
        "phone": "1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/educators/register", json=register_data)
    print(f"Register response: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Register error: {response.text}")
    
    # Try login again
    response = requests.post(f"{BASE_URL}/api/v1/educators/login", data=login_data)
    print(f"Login after register response: {response.status_code}")
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Login error: {response.text}")
    
    return None

def test_scheduling(token):
    """Test scheduling functionality"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a schedule event
    now = datetime.now()
    start_time = now + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    
    schedule_data = {
        "title": "Test Meeting",
        "description": "A test meeting",
        "event_type": "meeting",
        "start_datetime": start_time.isoformat(),
        "end_datetime": end_time.isoformat(),
        "location": "Conference Room A",
        "virtual_meeting_link": "https://zoom.us/j/123456789",
        "course_code": "CS101",
        "is_recurring": False,
        "recurrence_pattern": None
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/scheduling/", json=schedule_data, headers=headers)
    print(f"Create schedule response: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        schedule_id = response.json().get("id")
        print(f"Created schedule with ID: {schedule_id}")
        
        # Get schedules
        response = requests.get(f"{BASE_URL}/api/v1/scheduling/", headers=headers)
        print(f"Get schedules response: {response.status_code}")
        print(f"Schedules: {len(response.json()) if response.status_code == 200 else 0}")
        
        return True
    return False

def main():
    print("Testing scheduling functionality...")
    
    # Test registration and login
    token = test_register_and_login()
    if not token:
        print("Failed to get auth token")
        return
    
    print(f"Got auth token: {token[:20]}...")
    
    # Test scheduling
    success = test_scheduling(token)
    if success:
        print("✅ Scheduling test passed!")
    else:
        print("❌ Scheduling test failed!")

if __name__ == "__main__":
    main()