#!/usr/bin/env python3
"""
Test the students API endpoint directly to see what's causing the 500 error
"""
import requests
import json

def test_students_endpoint():
    # First, login to get token
    login_url = "http://localhost:8001/api/v1/educators/login"
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    
    try:
        print("Logging in...")
        login_response = requests.post(login_url, data=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test the sections endpoint first
            sections_url = "http://localhost:8001/api/v1/students/sections"
            print("\nFetching sections...")
            sections_response = requests.get(sections_url, headers=headers)
            print(f"Sections status: {sections_response.status_code}")
            
            if sections_response.status_code == 200:
                sections = sections_response.json()
                print(f"Found {len(sections)} sections")
                
                if sections:
                    section_id = sections[0]["id"]
                    print(f"Testing section {section_id}")
                    
                    # Test the problematic endpoint
                    students_url = f"http://localhost:8001/api/v1/students/sections/{section_id}/students/filtered"
                    print(f"\nFetching students from: {students_url}")
                    
                    students_response = requests.get(students_url, headers=headers)
                    print(f"Students status: {students_response.status_code}")
                    
                    if students_response.status_code == 200:
                        students = students_response.json()
                        print(f"Found {len(students)} students")
                        if students:
                            print(f"First student: {json.dumps(students[0], indent=2)}")
                    else:
                        print(f"Students error: {students_response.text}")
                        
            else:
                print(f"Sections error: {sections_response.text}")
        else:
            print(f"Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_students_endpoint()