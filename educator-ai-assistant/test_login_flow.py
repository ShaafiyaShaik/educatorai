#!/usr/bin/env python3
"""
Test login and dashboard flow
"""
import requests
import json

def test_login_and_dashboard():
    base_url = "http://localhost:8001"
    
    # Test login
    login_data = {
        "username": "shaaf123@gmail.com",
        "password": "password123"
    }
    
    print("Testing login...")
    response = requests.post(
        f"{base_url}/api/v1/educators/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Login status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"Got token: {token[:20]}..." if token else "No token received")
        
        # Test dashboard with token
        print("\nTesting dashboard...")
        dashboard_response = requests.get(
            f"{base_url}/api/v1/dashboard/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Dashboard status: {dashboard_response.status_code}")
        if dashboard_response.status_code == 200:
            print("Dashboard data received successfully!")
            data = dashboard_response.json()
            print(f"Total students: {data.get('overall_stats', {}).get('total_students', 'N/A')}")
        else:
            print(f"Dashboard error: {dashboard_response.text}")
    else:
        print(f"Login failed: {response.text}")

if __name__ == "__main__":
    test_login_and_dashboard()