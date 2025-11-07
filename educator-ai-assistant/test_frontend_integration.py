"""
Test script to verify frontend integration with existing performance APIs
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
PERFORMANCE_URL = f"{BASE_URL}/performance"

def test_login():
    """Test login functionality"""
    print("🔐 Testing login...")
    login_data = {
        "username": "shaaf@example.com",  # Using existing educator
        "password": "shaaf123"
    }
    
    try:
        response = requests.post(LOGIN_URL, data=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse token from response
            token_data = response.json()
            token = token_data.get('access_token')
            print(f"✅ Login successful, token: {token[:20]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_performance_apis(token):
    """Test performance API endpoints"""
    if not token:
        print("❌ No token available, skipping API tests")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test overview endpoint
    print("\n📊 Testing overview endpoint...")
    try:
        response = requests.get(f"{PERFORMANCE_URL}/overview", headers=headers)
        print(f"Overview status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Overview data keys: {list(data.keys())}")
            print(f"Total sections: {data.get('total_sections', 'N/A')}")
            print(f"Total students: {data.get('total_students', 'N/A')}")
            print(f"Overall average: {data.get('overall_average', 'N/A')}")
            print(f"Sections summary count: {len(data.get('sections_summary', []))}")
            print(f"Subjects summary count: {len(data.get('subjects_summary', []))}")
            
            # Test section endpoint if we have sections
            sections_summary = data.get('sections_summary', [])
            if sections_summary:
                section_id = sections_summary[0]['section_id']
                print(f"\n🏫 Testing section endpoint with ID {section_id}...")
                
                section_response = requests.get(f"{PERFORMANCE_URL}/section/{section_id}", headers=headers)
                print(f"Section status: {section_response.status_code}")
                
                if section_response.status_code == 200:
                    section_data = section_response.json()
                    print(f"✅ Section data keys: {list(section_data.keys())}")
                    print(f"Section name: {section_data.get('section_name', 'N/A')}")
                    print(f"Total students: {section_data.get('total_students', 'N/A')}")
                    print(f"Average score: {section_data.get('average_score', 'N/A')}")
                else:
                    print(f"❌ Section request failed: {section_response.status_code}")
                    print(f"Response: {section_response.text}")
        else:
            print(f"❌ Overview request failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ API test error: {e}")

def main():
    print("🚀 Testing Frontend Integration with Performance APIs")
    print("=" * 60)
    
    # Test login
    token = test_login()
    
    # Test performance APIs
    test_performance_apis(token)
    
    print("\n" + "=" * 60)
    print("✅ Integration test completed!")

if __name__ == "__main__":
    main()