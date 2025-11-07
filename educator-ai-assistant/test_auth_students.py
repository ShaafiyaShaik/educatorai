"""
Test authentication and API calls
"""

import requests
import json

def test_authentication_and_students():
    base_url = "http://127.0.0.1:8002"
    
    # Test login with our test user
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    
    try:
        print("1. Testing login...")
        login_response = requests.post(f"{base_url}/api/v1/educators/login", data=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data["access_token"]
            print(f"Login successful! Token: {token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n2. Testing sections endpoint...")
            sections_response = requests.get(f"{base_url}/api/v1/students/sections", headers=headers)
            print(f"Sections status: {sections_response.status_code}")
            print(f"Sections data: {sections_response.text[:200]}...")
            
            if sections_response.status_code == 200:
                sections = sections_response.json()
                print(f"Number of sections: {len(sections)}")
                
                if sections:
                    for i, section in enumerate(sections[:3]):  # Show first 3 sections
                        print(f"Section {i+1}: ID={section['id']}, Name={section['name']}")
                    
                    section_id = sections[0]["id"]
                    print(f"\n3. Testing students for section {section_id}...")
                    students_response = requests.get(
                        f"{base_url}/api/v1/students/sections/{section_id}/students/filtered",
                        headers=headers
                    )
                    print(f"Students status: {students_response.status_code}")
                    print(f"Students data: {students_response.text[:300]}...")
                else:
                    print("No sections found")
            else:
                print(f"Sections error: {sections_response.text}")
                
        else:
            print(f"Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_authentication_and_students()