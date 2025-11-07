import requests
import json

# Test the performance endpoints
BASE_URL = "http://localhost:8001"

# First, we need to authenticate to get a token
# This is just for testing - in real usage, use proper login
headers = {
    "Authorization": "Bearer your_token_here"  # Replace with actual token
}

def test_endpoint(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, json=data)
        
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        if response.status_code < 300:
            print("✅ Success")
        else:
            print("❌ Failed")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("Testing Performance API Endpoints...")
    
    # Test main performance endpoints
    test_endpoint("/api/v1/performance/overview")
    test_endpoint("/api/v1/performance/sent-reports")
    test_endpoint("/api/v1/students/sections")
    
    print("\n" + "="*50)
    print("Note: These tests will fail without proper authentication.")
    print("Use the frontend to test with proper login tokens.")