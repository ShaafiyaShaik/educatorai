"""
Test the bulk communication API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_login():
    """Login to get authentication token"""
    login_data = {
        "username": "shaaf@gmail.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/educators/login", data=login_data)
    print("Login Response:", response.status_code)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    else:
        print("Login failed:", response.text)
        return None

def test_get_sections(headers):
    """Test getting sections"""
    response = requests.get(f"{BASE_URL}/api/v1/bulk-communication/sections", headers=headers)
    print(f"Get Sections: {response.status_code}")
    if response.status_code == 200:
        sections = response.json()
        print("Sections:", json.dumps(sections, indent=2))
        return sections
    else:
        print("Error:", response.text)
        return None

def test_get_students(headers, section_id=None):
    """Test getting students"""
    params = {"section_id": section_id} if section_id else {}
    response = requests.get(f"{BASE_URL}/api/v1/bulk-communication/students", 
                          headers=headers, params=params)
    print(f"Get Students: {response.status_code}")
    if response.status_code == 200:
        students = response.json()
        print("Students:", json.dumps(students, indent=2))
        return students
    else:
        print("Error:", response.text)
        return None

def test_get_templates(headers):
    """Test getting email templates"""
    response = requests.get(f"{BASE_URL}/api/v1/bulk-communication/email-templates", headers=headers)
    print(f"Get Templates: {response.status_code}")
    if response.status_code == 200:
        templates = response.json()
        print("Templates:", json.dumps(templates, indent=2))
        return templates
    else:
        print("Error:", response.text)
        return None

def test_send_bulk_email(headers):
    """Test sending bulk email"""
    bulk_email_data = {
        "target_type": "section",
        "sections": ["Section A"],
        "message_template": """Dear {student_name},

Your recent academic performance:
• Mathematics: {math_marks}%
• Science: {science_marks}%  
• English: {english_marks}%

Your average score is {average_score}% → Status: {status}
Grade: {grade_letter}

{status_message}

Best regards,
Your Teacher

Student ID: {roll_no} | Section: {section}""",
        "subject": "Academic Performance Report - {section}",
        "send_email": True,
        "create_notifications": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/bulk-communication/bulk-email", 
                           headers=headers, json=bulk_email_data)
    print(f"Send Bulk Email: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Bulk Email Result:", json.dumps(result, indent=2))
        return result
    else:
        print("Error:", response.text)
        return None

def main():
    print("🧪 Testing Bulk Communication API")
    print("=" * 50)
    
    # Login first
    headers = test_login()
    if not headers:
        print("❌ Authentication failed, cannot continue")
        return
    
    print("\n📋 Testing Sections...")
    sections = test_get_sections(headers)
    
    print("\n👥 Testing Students...")
    students = test_get_students(headers)
    
    print("\n📧 Testing Email Templates...")
    templates = test_get_templates(headers)
    
    print("\n📤 Testing Bulk Email Send...")
    bulk_result = test_send_bulk_email(headers)
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    main()