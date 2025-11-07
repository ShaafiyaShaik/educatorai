#!/usr/bin/env python3
"""
Simple HTTP test - just test the endpoint that frontend calls
"""

import requests
import json

def test_performance_endpoint():
    print("🌐 Testing Performance Endpoint (Frontend simulation)")
    print("=" * 55)
    
    try:
        # Login
        login_data = {
            'username': 'shaaf@gmail.com',
            'password': 'password123'
        }
        
        print("1. Logging in...")
        response = requests.post('http://localhost:8001/api/v1/users/login', data=login_data)
        
        if response.status_code == 200:
            token = response.json()['access_token']
            print(f"   ✅ Login successful")
            
            # Test performance endpoint
            print("2. Calling performance/overview...")
            headers = {'Authorization': f'Bearer {token}'}
            perf_response = requests.get('http://localhost:8001/api/v1/performance/overview', headers=headers)
            
            print(f"   📊 Status Code: {perf_response.status_code}")
            
            if perf_response.status_code == 200:
                data = perf_response.json()
                print(f"   ✅ SUCCESS! Performance Data:")
                print(f"      - Total Students: {data.get('total_students', 'N/A')}")
                print(f"      - Overall Average: {data.get('overall_average', 'N/A')}%")
                print(f"      - Pass Rate: {data.get('overall_pass_rate', 'N/A')}%")
                print(f"      - Total Sections: {data.get('total_sections', 'N/A')}")
                
                # Check for grade level stats
                grade_stats = data.get('grade_level_stats', {})
                if grade_stats:
                    print(f"      - Grade Stats: {grade_stats}")
                
                print(f"\n✅ CONCLUSION: API is working! Data is being returned correctly.")
                print(f"   If frontend shows 0.0%, the issue is in React component logic.")
                
            else:
                print(f"   ❌ Performance API Error: {perf_response.status_code}")
                print(f"      Response: {perf_response.text}")
                
        else:
            print(f"   ❌ Login Error: {response.status_code}")
            print(f"      Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print(f"   Make sure server is running on localhost:8001")

if __name__ == "__main__":
    test_performance_endpoint()