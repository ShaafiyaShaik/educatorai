#!/usr/bin/env python3
"""
Test exact endpoint frontend calls
"""

import requests
import json

def test_frontend_api():
    print("🌐 Testing exact frontend API endpoint...")
    
    # Login first
    login_data = {
        "username": "shaaf@gmail.com", 
        "password": "password123"
    }
    
    try:
        # Login
        login_response = requests.post(
            "http://127.0.0.1:8001/api/v1/users/login",
            data=login_data
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return
        
        token = login_response.json()["access_token"]
        print(f"✅ Login successful, token: {token[:20]}...")
        
        # Test performance overview - exact frontend call
        headers = {"Authorization": f"Bearer {token}"}
        
        performance_response = requests.get(
            "http://127.0.0.1:8001/api/v1/performance/overview",
            headers=headers
        )
        
        print(f"📊 Performance API Status: {performance_response.status_code}")
        
        if performance_response.status_code == 200:
            data = performance_response.json()
            print(f"✅ API Working! Data preview:")
            print(f"  Total Students: {data.get('total_students', 'N/A')}")
            print(f"  Overall Average: {data.get('overall_average', 'N/A')}%")
            print(f"  Pass Rate: {data.get('overall_pass_rate', 'N/A')}%")
            print(f"  Sections: {data.get('total_sections', 'N/A')}")
            
            # Check grade level stats
            stats = data.get('grade_level_stats', {})
            print(f"  Grade Stats: {stats}")
            
        else:
            print(f"❌ API Error: {performance_response.status_code}")
            print(performance_response.text)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_frontend_api()