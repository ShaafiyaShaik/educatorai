#!/usr/bin/env python3
"""
Test script to verify dashboard API endpoints work
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_dashboard_endpoint():
    """Test if dashboard endpoint is registered"""
    
    print("Testing API endpoints...")
    
    # Test root endpoint
    response = client.get("/")
    print(f"Root endpoint: {response.status_code}")
    
    # Test docs endpoint  
    response = client.get("/docs")
    print(f"Docs endpoint: {response.status_code}")
    
    # Test dashboard endpoint (should be 401 without auth)
    response = client.get("/api/v1/dashboard/dashboard")
    print(f"Dashboard endpoint (no auth): {response.status_code} - {response.json()}")
    
    # Test login first
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    response = client.post("/api/v1/educators/login", data=login_data)
    print(f"Login endpoint: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test dashboard with auth
        response = client.get("/api/v1/dashboard/dashboard", headers=headers)
        print(f"Dashboard endpoint (with auth): {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.json()}")
        else:
            print("Dashboard endpoint working correctly!")
    else:
        print(f"Login failed: {response.json()}")

if __name__ == "__main__":
    test_dashboard_endpoint()