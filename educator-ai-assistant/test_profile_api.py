import requests
import json

# Test the profile API endpoint specifically
base_url = "http://localhost:8003/api/v1"

# Login to get a token
login_data = {
    "username": "ananya.rao@school.com",
    "password": "Ananya@123"
}

print("🔐 Testing profile API endpoint...")
try:
    login_response = requests.post(f"{base_url}/educators/login", data=login_data)
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
        # Test the profile endpoint
        print("\n👤 Testing /api/v1/educators/me endpoint...")
        profile_response = requests.get(f"{base_url}/educators/me", headers=headers)
        
        print(f"Status Code: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("✅ Profile API working!")
            print("Profile data:")
            for key, value in profile_data.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Profile API failed: {profile_response.text}")
            
    else:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server - make sure it's running on port 8003")
except Exception as e:
    print(f"❌ Unexpected error: {e}")