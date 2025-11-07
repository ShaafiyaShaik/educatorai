#!/usr/bin/env python3
"""
Test login functionality to debug authentication issues
"""

import requests
import json

# Test data
login_data = {
    "username": "ananya.rao@school.com",  # OAuth2 expects 'username' field
    "password": "Ananya@123"
}

try:
    # Test login
    print("Testing educator login...")
    response = requests.post(
        "http://localhost:8003/api/v1/educators/login",
        data=login_data,  # Using form data like the frontend
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success! Token: {result.get('access_token', 'No token')}")
        
        # Test authenticated endpoint
        token = result.get('access_token')
        if token:
            auth_headers = {"Authorization": f"Bearer {token}"}
            profile_response = requests.get(
                "http://localhost:8003/api/v1/educators/profile",
                headers=auth_headers
            )
            print(f"Profile Status: {profile_response.status_code}")
            if profile_response.status_code == 200:
                print(f"Profile: {profile_response.json()}")
    else:
        print(f"Error Response: {response.text}")
        
    # Also test with JSON data format
    print("\nTesting with JSON format...")
    json_response = requests.post(
        "http://localhost:8003/api/v1/educators/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"JSON Status Code: {json_response.status_code}")
    if json_response.status_code != 200:
        print(f"JSON Error: {json_response.text}")
    else:
        print(f"JSON Success: {json_response.json()}")

except Exception as e:
    print(f"Error testing login: {e}")