import requests
import json

# Test both issues are fixed
base_url = "http://localhost:8003/api/v1"

# First, login to get a token
login_data = {
    "username": "ananya.rao@school.com",
    "password": "Ananya@123"
}

print("🔐 Testing login...")
login_response = requests.post(f"{base_url}/educators/login", data=login_data)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Test 1: Check profile data (should show name now)
    print("\n👤 Testing profile data...")
    try:
        # We need to find the profile endpoint - let's check sections first
        sections_response = requests.get(f"{base_url}/students/sections", headers=headers)
        print(f"Sections API Status: {sections_response.status_code}")
        
        if sections_response.status_code == 200:
            sections = sections_response.json()
            print(f"✅ Found {len(sections)} sections")
            for section in sections:
                print(f"  - {section['name']} ({section['student_count']} students)")
            
            # Test 2: Check students in first section
            if sections:
                section_id = sections[0]['id']
                print(f"\n👨‍🎓 Testing students in section {section_id}...")
                
                students_response = requests.get(
                    f"{base_url}/students/sections/{section_id}/students/filtered", 
                    headers=headers
                )
                print(f"Students API Status: {students_response.status_code}")
                
                if students_response.status_code == 200:
                    students = students_response.json()
                    print(f"✅ Found {len(students)} students with grades!")
                    for student in students[:3]:  # Show first 3
                        print(f"  - {student['student_name']} (Passed: {student['passed_subjects']}/{student['total_subjects']})")
                        for grade in student['grades'][:2]:  # Show first 2 grades
                            print(f"    {grade['subject_name']}: {grade['marks_obtained']}/{grade['total_marks']} ({grade['grade_letter']})")
                else:
                    print(f"❌ Students API failed: {students_response.text}")
        else:
            print(f"❌ Sections API failed: {sections_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
    except Exception as e:
        print(f"❌ Error: {e}")
        
else:
    print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")