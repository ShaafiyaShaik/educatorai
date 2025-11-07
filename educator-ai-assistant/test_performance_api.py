#!/usr/bin/env python3
"""
Test the performance analytics endpoints
"""
import requests
import json

def test_performance_endpoints():
    # First, login to get token
    login_url = "http://localhost:8001/api/v1/educators/login"
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    
    try:
        print("Logging in...")
        login_response = requests.post(login_url, data=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test performance overview
            print("\n=== Testing Performance Overview ===")
            overview_url = "http://localhost:8001/api/v1/performance/overview"
            overview_response = requests.get(overview_url, headers=headers)
            print(f"Overview status: {overview_response.status_code}")
            
            if overview_response.status_code == 200:
                overview = overview_response.json()
                print(f"Response keys: {list(overview.keys())}")
                print(f"Overall average: {overview.get('overall_average')}%")
                print(f"Total students: {overview.get('total_students')}")
                print(f"Total sections: {overview.get('total_sections')}")
                print(f"Pass rate: {overview.get('overall_pass_rate')}%")
            else:
                print(f"Overview error: {overview_response.text}")
                
            # Test filtered analysis (POST request)
            print("\n=== Testing Filtered Analysis ===")
            filtered_url = "http://localhost:8001/api/v1/performance/filtered"
            filter_data = {
                "section_filter": None,
                "subject_filter": None,
                "grade_range": None,
                "pass_status": None
            }
            filtered_response = requests.post(filtered_url, json=filter_data, headers=headers)
            print(f"Filtered status: {filtered_response.status_code}")
            
            if filtered_response.status_code == 200:
                filtered = filtered_response.json()
                print(f"Found {len(filtered.get('students', []))} students in analysis")
                if filtered.get('students'):
                    print(f"First student: {filtered['students'][0]['name']} - {filtered['students'][0]['average_score']}%")
            else:
                print(f"Filtered error: {filtered_response.text}")
                
        else:
            print(f"Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_performance_endpoints()