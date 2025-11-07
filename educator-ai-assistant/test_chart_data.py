#!/usr/bin/env python3
"""
Test the chart data in performance endpoint
"""
import requests
import json

def test_chart_data():
    """Test if chart data is populated"""
    base_url = "http://127.0.0.1:8001"
    
    # Login
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    
    print("🔐 Logging in...")
    response = requests.post(f"{base_url}/api/v1/educators/login", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
        
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Get performance data
    print("\n📊 Getting performance data...")
    response = requests.get(f"{base_url}/api/v1/performance/overview", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get performance data: {response.status_code}")
        return
        
    data = response.json()
    print("✅ Performance data received")
    
    # Check chart data fields
    print(f"\n📈 Chart Data Analysis:")
    print(f"   Grade Distribution: {len(data.get('grade_distribution', {})) if data.get('grade_distribution') else 0} grades")
    if data.get('grade_distribution'):
        for grade, count in data['grade_distribution'].items():
            print(f"      {grade}: {count} students")
    
    print(f"   Subject Performance Chart: {len(data.get('subject_performance_chart', []))} subjects")
    if data.get('subject_performance_chart'):
        for subject in data['subject_performance_chart']:
            print(f"      {subject.get('subject_name', 'Unknown')}: {subject.get('average_score', 0):.1f}% avg")
    
    print(f"   Section Performance Chart: {len(data.get('sections_performance_chart', []))} sections")
    if data.get('sections_performance_chart'):
        for section in data['sections_performance_chart']:
            print(f"      {section.get('section_name', 'Unknown')}: {section.get('average_score', 0):.1f}% avg")
    
    print(f"   Monthly Trends: {len(data.get('monthly_trends', []))} data points")
    print(f"   Attendance Stats: {'Available' if data.get('attendance_stats') else 'Not Available'}")
    
    # Full data dump for debugging
    print(f"\n🔍 Full Response Keys: {list(data.keys())}")

if __name__ == "__main__":
    print("🚀 Testing Chart Data...")
    test_chart_data()
    print("✨ Test completed!")