"""
Test the get_current_educator function
"""

import requests

def test_current_educator():
    base_url = "http://127.0.0.1:8001"
    
    # Login first
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    
    login_response = requests.post(f"{base_url}/api/v1/educators/login", data=login_data)
    if login_response.status_code == 200:
        token_data = login_response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test educator profile endpoint to see current educator
        profile_response = requests.get(f"{base_url}/api/v1/educators/profile", headers=headers)
        print(f"Profile status: {profile_response.status_code}")
        print(f"Profile data: {profile_response.text}")
        
    else:
        print(f"Login failed: {login_response.text}")

if __name__ == "__main__":
    test_current_educator()