#!/usr/bin/env python3
"""
Test login with curl-like request to debug the issue
"""
import requests
import urllib.parse

def test_login_detailed():
    """Test login with detailed debugging"""
    
    BASE_URL = "http://localhost:8003"
    LOGIN_URL = f"{BASE_URL}/api/v1/educators/login"
    
    # Try different request formats
    
    print("🔐 Testing different login request formats...")
    
    # Format 1: Standard form data
    print("\n1. Testing with form data...")
    login_data = {
        "username": "ananya.rao@school.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(LOGIN_URL, data=login_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Format 2: URL encoded explicitly  
    print("\n2. Testing with explicit URL encoding...")
    encoded_data = urllib.parse.urlencode(login_data)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(LOGIN_URL, data=encoded_data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
        
    # Format 3: JSON data (shouldn't work but let's test)
    print("\n3. Testing with JSON data...")
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(LOGIN_URL, json=login_data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Format 4: Try different user
    print("\n4. Testing with second educator...")
    login_data2 = {
        "username": "kiran.verma@school.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(LOGIN_URL, data=login_data2)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_login_detailed()