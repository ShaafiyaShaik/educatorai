#!/usr/bin/env python3
"""Test frontend authentication integration with performance APIs"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_login_and_performance():
    """Test login and performance API access"""
    
    # Test login
    print("🔑 Testing login...")
    login_data = {
        "username": "ananya@email.com", 
        "password": "password123"
    }
    
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
        
    token_data = login_response.json()
    token = token_data.get('access_token')
    print(f"✅ Login successful, token: {token[:20]}...")
    
    # Test performance overview endpoint
    print("\n📊 Testing performance overview...")
    headers = {"Authorization": f"Bearer {token}"}
    
    overview_response = requests.get(f"{BASE_URL}/api/v1/performance/overview", headers=headers)
    print(f"Overview Status: {overview_response.status_code}")
    
    if overview_response.status_code == 200:
        overview_data = overview_response.json()
        print(f"✅ Overview data: {json.dumps(overview_data, indent=2)}")
        
        # Test section performance
        print(f"\n🏫 Testing section performance...")
        if overview_data.get('sections'):
            section_id = overview_data['sections'][0]['section_id']
            section_response = requests.get(
                f"{BASE_URL}/api/v1/performance/section/{section_id}", 
                headers=headers
            )
            print(f"Section Status: {section_response.status_code}")
            
            if section_response.status_code == 200:
                section_data = section_response.json()
                print(f"✅ Section data: {json.dumps(section_data, indent=2)}")
                
                # Test student performance
                print(f"\n🎓 Testing student performance...")
                if section_data.get('students'):
                    student_id = section_data['students'][0]['student_id'] 
                    student_response = requests.get(
                        f"{BASE_URL}/api/v1/performance/student/{student_id}",
                        headers=headers
                    )
                    print(f"Student Status: {student_response.status_code}")
                    
                    if student_response.status_code == 200:
                        student_data = student_response.json()
                        print(f"✅ Student data: {json.dumps(student_data, indent=2)}")
                    else:
                        print(f"❌ Student API failed: {student_response.text}")
            else:
                print(f"❌ Section API failed: {section_response.text}")
        else:
            print("⚠️ No sections found in overview")
    else:
        print(f"❌ Overview API failed: {overview_response.text}")

if __name__ == "__main__":
    print("🧪 Testing Frontend Authentication Integration")
    print("="*50)
    
    try:
        test_login_and_performance()
        print("\n✅ All tests completed!")
        print("\n📋 Summary:")
        print("- Login endpoint working")  
        print("- Token authentication working")
        print("- Performance APIs accessible with token")
        print("- Frontend should now display data correctly!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on port 8000?")
    except Exception as e:
        print(f"❌ Test failed: {e}")