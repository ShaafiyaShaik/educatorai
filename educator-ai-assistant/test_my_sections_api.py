#!/usr/bin/env python3
"""
Test the meetings/my-sections API to see what data is being returned
"""
import requests
import json

def test_my_sections_api():
    """Test the my-sections API endpoint"""
    print("🧪 Testing /api/v1/meetings/my-sections API")
    print("=" * 50)
    
    # First login to get token
    login_url = "http://localhost:8003/api/v1/educators/login"
    login_data = {
        "username": "ananya.rao@school.com",
        "password": "Ananya@123"
    }
    
    try:
        login_response = requests.post(login_url, data=login_data)
        print(f"🔑 Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test the my-sections endpoint
            sections_url = "http://localhost:8003/api/v1/meetings/my-sections"
            
            print(f"\n📋 Calling: {sections_url}")
            sections_response = requests.get(sections_url, headers=headers)
            
            print(f"📊 Status Code: {sections_response.status_code}")
            
            if sections_response.status_code == 200:
                sections_data = sections_response.json()
                print(f"✅ Response received!")
                print(f"📝 Response Data:")
                print(json.dumps(sections_data, indent=2))
                
                # Analyze the data structure
                print(f"\n🔍 Data Analysis:")
                print(f"   Sections Count: {len(sections_data)}")
                
                for i, section in enumerate(sections_data):
                    print(f"\n   Section {i+1}:")
                    print(f"     Name: {section.get('name')}")
                    print(f"     ID: {section.get('id')}")
                    print(f"     Student Count: {section.get('student_count')}")
                    
                    if 'students' in section:
                        students = section['students']
                        print(f"     Students Array: {len(students)} items")
                        if students:
                            print(f"     First Student: {students[0]}")
                    else:
                        print(f"     ❌ No 'students' key found!")
                        
            else:
                print(f"❌ API Error: {sections_response.text}")
                
        else:
            print(f"❌ Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_my_sections_api()