#!/usr/bin/env python3
"""
Test the new enhanced performance views endpoints
"""
import requests
import json

def test_performance_endpoints():
    """Test the performance views endpoints"""
    base_url = "http://127.0.0.1:8001"
    
    # Test login first
    login_data = {
        "username": "shaaf@gmail.com",  # Updated email
        "password": "password123"
    }
    
    print("🔐 Testing login...")
    response = requests.post(f"{base_url}/api/v1/educators/login", data=login_data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
        # Test performance overview endpoint
        print("\n📊 Testing performance overview endpoint...")
        response = requests.get(f"{base_url}/api/v1/performance/overview", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Performance overview endpoint working!")
            print(f"   Total Sections: {data.get('total_sections', 0)}")
            print(f"   Total Students: {data.get('total_students', 0)}")
            print(f"   Overall Pass Rate: {data.get('overall_pass_rate', 0)}%")
            print(f"   Overall Average: {data.get('overall_average', 0)}%")
        else:
            print(f"❌ Performance overview failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test filtered performance endpoint
        print("\n🔍 Testing filtered performance endpoint...")
        filter_data = {
            "view_type": "overall",
            "sort_by": "average",
            "sort_order": "desc",
            "include_top_performers": True,
            "include_low_performers": True
        }
        
        response = requests.post(f"{base_url}/api/v1/performance/filtered", 
                               headers=headers, json=filter_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Filtered performance endpoint working!")
            print(f"   Total Count: {data.get('total_count', 0)}")
            if 'top_performers' in data:
                print(f"   Top Performers: {len(data['top_performers'])}")
            if 'low_performers' in data:
                print(f"   Low Performers: {len(data['low_performers'])}")
        else:
            print(f"❌ Filtered performance failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
        # Test API docs
        print("\n📚 Testing API documentation...")
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ API documentation accessible at http://127.0.0.1:8001/docs")
        else:
            print("❌ API documentation not accessible")
            
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    print("🚀 Testing Enhanced Performance Views...")
    test_performance_endpoints()
    print("\n✨ Test completed!")