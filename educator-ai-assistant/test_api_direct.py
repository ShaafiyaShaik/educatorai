#!/usr/bin/env python3
"""
Direct API test to verify what data is being returned by the meetings API
"""

import requests
import json

# Login as educator to get token
login_data = {
    "username": "ananya.rao@school.com",
    "password": "Ananya@123"
}

print("🔐 Logging in as educator...")
response = requests.post("http://localhost:8003/api/v1/educators/login", data=login_data)

if response.status_code == 200:
    token_data = response.json()
    token = token_data["access_token"]
    print(f"✅ Login successful, got token")
    
    # Test my-sections API with authentication
    headers = {"Authorization": f"Bearer {token}"}
    sections_response = requests.get("http://localhost:8003/api/v1/meetings/my-sections", headers=headers)
    
    if sections_response.status_code == 200:
        sections_data = sections_response.json()
        print("✅ Sections API Response:")
        print(json.dumps(sections_data, indent=2))
        
        print(f"\n📊 Summary:")
        print(f"   - Found {len(sections_data)} sections")
        for section in sections_data:
            students_count = len(section.get('students', []))
            print(f"   - Section '{section['name']}': {students_count} students")
            if students_count > 0:
                for student in section['students']:
                    print(f"     * {student['first_name']} {student['last_name']} ({student['student_id']})")
    else:
        print(f"❌ Sections API failed: {sections_response.status_code}")
        print(sections_response.text)
        
else:
    print(f"❌ Login failed: {response.status_code}")
    print(response.text)