#!/usr/bin/env python3
"""
Test the performance API endpoints
"""
import requests
import json

def test_performance_apis():
    """Test the new performance API endpoints"""
    
    base_url = "http://localhost:8003"
    
    # First login to get token
    try:
        login_data = {
            "email": "ananya.rao@school.com",
            "password": "Ananya@123"
        }
        
        login_response = requests.post(f"{base_url}/api/v1/educators/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Login successful, testing performance APIs...")
        
        # Test 1: Teacher Performance Summary
        print("\n📊 Testing Teacher Performance Summary...")
        summary_response = requests.get(f"{base_url}/api/v1/performance/teachers/1/performance/summary", headers=headers)
        
        if summary_response.status_code == 200:
            summary_data = summary_response.json()
            print(f"✅ Teacher Summary: {len(summary_data['section_summaries'])} sections, {summary_data['teacher_summary']['total_students']} students")
            print(f"   Overall Average: {summary_data['teacher_summary']['overall_average']}%")
            print(f"   Alerts: {len(summary_data['alerts'])}")
        else:
            print(f"❌ Teacher Summary failed: {summary_response.status_code}")
            print(f"   Response: {summary_response.text}")
        
        # Test 2: Section Performance (assuming section ID 1 exists)
        print("\n🏫 Testing Section Performance...")
        section_response = requests.get(f"{base_url}/api/v1/performance/teachers/1/sections/1/performance", headers=headers)
        
        if section_response.status_code == 200:
            section_data = section_response.json()
            print(f"✅ Section Performance: {section_data['section_info']['name']}")
            print(f"   Students: {len(section_data['students'])}")
            print(f"   Section Average: {section_data['summary_stats']['section_average']}%")
            print(f"   Pass Rate: {section_data['summary_stats']['pass_percentage']}%")
            
            # Show first few students
            print("   First 3 students:")
            for student in section_data['students'][:3]:
                print(f"     - {student['student_name']}: {student['overall_average']}% ({student['status']})")
                
        else:
            print(f"❌ Section Performance failed: {section_response.status_code}")
            print(f"   Response: {section_response.text}")
        
        # Test 3: Individual Student Performance (assuming student ID 1 exists)
        print("\n👤 Testing Individual Student Performance...")
        student_response = requests.get(f"{base_url}/api/v1/performance/students/1/performance", headers=headers)
        
        if student_response.status_code == 200:
            student_data = student_response.json()
            print(f"✅ Student Performance: {student_data['student_info']['name']}")
            print(f"   Current Average: {student_data['current_performance']['overall_average']}%")
            print(f"   Attendance: {student_data['current_performance']['attendance_percentage']}%")
            print(f"   Grade History: {len(student_data['grade_history'])} records")
        else:
            print(f"❌ Student Performance failed: {student_response.status_code}")
            print(f"   Response: {student_response.text}")
        
        # Test 4: Subject Distribution (assuming subject ID 1 exists)
        print("\n📚 Testing Subject Distribution...")
        subject_response = requests.get(f"{base_url}/api/v1/performance/subjects/1/distribution", headers=headers)
        
        if subject_response.status_code == 200:
            subject_data = subject_response.json()
            print(f"✅ Subject Distribution: {subject_data['subject_info']['name']}")
            print(f"   Statistics: Mean {subject_data['statistics']['mean']}%, Std Dev {subject_data['statistics']['std_deviation']}")
            print(f"   Grade Distribution: {subject_data['grade_distribution']}")
        else:
            print(f"❌ Subject Distribution failed: {subject_response.status_code}")
            print(f"   Response: {subject_response.text}")
        
        print("\n🎉 Performance API testing completed!")
        
    except Exception as e:
        print(f"❌ Error testing APIs: {e}")

if __name__ == "__main__":
    print("🚀 Testing Performance API Endpoints...")
    test_performance_apis()