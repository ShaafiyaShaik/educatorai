#!/usr/bin/env python3
"""
Test student login API directly
"""
import requests
import json

def test_student_login():
    """Test student login with different accounts"""
    
    BASE_URL = "http://localhost:8003"
    LOGIN_URL = f"{BASE_URL}/api/v1/student-auth/login"
    
    # Test accounts
    test_accounts = [
        {"email": "student1@school.com", "password": "student123"},
        {"email": "S101@gmail.com", "password": "password123"}
    ]
    
    print("🧪 Testing Student Login API")
    print("=" * 40)
    
    for i, account in enumerate(test_accounts, 1):
        print(f"\n{i}. Testing {account['email']} / {account['password']}")
        
        try:
            # Try JSON format (what the frontend is using)
            headers = {"Content-Type": "application/json"}
            response = requests.post(LOGIN_URL, json=account, headers=headers)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Token: {data.get('access_token', 'No token')[:50]}...")
                print(f"   Student ID: {data.get('student_id', 'N/A')}")
                print(f"   Name: {data.get('name', 'N/A')}")
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_student_login()