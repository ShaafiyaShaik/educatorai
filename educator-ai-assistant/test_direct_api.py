#!/usr/bin/env python3
"""
Direct API test without using requests - simulate FastAPI directly
"""

import asyncio
import sys
import os

# Add the app directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_direct():
    """Test login using FastAPI TestClient"""
    
    print("Testing login with TestClient...")
    
    # Test with form data exactly as expected by OAuth2PasswordRequestForm
    login_data = {
        "username": "ananya.rao@school.com",
        "password": "Ananya@123"
    }
    
    response = client.post("/api/v1/educators/login", data=login_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Login successful!")
        print(f"Token: {token_data.get('access_token', 'No token')}")
        return True
    else:
        print(f"❌ Login failed")
        return False

if __name__ == "__main__":
    success = test_login_direct()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")