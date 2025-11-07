#!/usr/bin/env python3
"""
Test educator login with correct credentials
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests

def test_educator_login():
    """Test educator login with Ananya's credentials"""
    print("🧪 Testing Educator Login")
    print("=" * 40)
    
    # Test with correct credentials
    url = "http://localhost:8003/api/v1/educators/login"
    
    # OAuth2PasswordRequestForm expects form data, not JSON
    form_data = {
        "username": "ananya.rao@school.com",
        "password": "Ananya@123"
    }
    
    try:
        print(f"📧 Testing: {form_data['username']}")
        print(f"🔑 Password: {form_data['password']}")
        
        response = requests.post(url, data=form_data)  # Use data, not json
        
        print(f"🌐 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ LOGIN SUCCESS!")
            print(f"🎫 Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"👤 User ID: {data.get('user_id', 'N/A')}")
            print(f"📝 Token Type: {data.get('token_type', 'N/A')}")
        else:
            print("❌ LOGIN FAILED!")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Is server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_educator_login()