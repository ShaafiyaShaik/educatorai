"""
Simple API test to verify login and performance endpoints
"""
import requests
import time

def test_server():
    print("🔍 Testing API endpoints...")
    
    base_url = "http://localhost:8003"
    
    # Test server is running
    print("1. Checking if server is running...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test different login endpoints
    login_endpoints = [
        "/api/v1/educators/login",
        "/api/v1/auth/login",
        "/auth/login", 
        "/login",
        "/api/auth/login"
    ]
    
    login_data = {
        "username": "ananya.rao@school.com",  # Ananya has the actual performance data
        "password": "Ananya@123"
    }
    
    print("\n2. Testing login endpoints...")
    for endpoint in login_endpoints:
        try:
            print(f"   Trying: {endpoint}")
            response = requests.post(f"{base_url}{endpoint}", data=login_data, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Login successful at {endpoint}")
                token = response.json().get('access_token')
                if token:
                    print(f"   Token: {token[:20]}...")
                    test_performance_api(base_url, token)
                    return
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found: {endpoint}")
            else:
                print(f"   ❌ Login failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ No working login endpoint found")

def test_performance_api(base_url, token):
    """Test performance API with valid token"""
    print("\n3. Testing performance API...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{base_url}/api/v1/performance/overview", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Performance API Response:")
            print(f"   Total Students: {data.get('total_students', 'N/A')}")
            print(f"   Overall Average: {data.get('overall_average', 'N/A')}")
            print(f"   Overall Pass Rate: {data.get('overall_pass_rate', 'N/A')}")
            print(f"   Sections Count: {len(data.get('sections_summary', []))}")
            print(f"   Subjects Count: {len(data.get('subjects_summary', []))}")
            
            # Show first section data
            sections = data.get('sections_summary', [])
            if sections:
                section = sections[0] 
                print(f"   First Section: {section.get('section_name')} - Avg: {section.get('average_score')}%")
            
        else:
            print(f"❌ Performance API failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API error: {e}")

if __name__ == "__main__":
    test_server()