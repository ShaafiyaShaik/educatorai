#!/usr/bin/env python3
"""
Quick test for student login functionality
"""
import requests
import json

def test_student_login():
    """Test student login with sample credentials"""
    
    # Test credentials from the database
    test_students = [
        {
            "email": "jennifer.colon@student.edu",
            "password": "student123",
            "name": "Jennifer Colon",
            "student_id": "MA001"
        },
        {
            "email": "kristen.sanchez@student.edu", 
            "password": "student123",
            "name": "Kristen Sanchez",
            "student_id": "ST121"
        }
    ]
    
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/v1/student-auth/login"
    
    print("🧪 Testing Student Login System")
    print("=" * 50)
    
    for i, student in enumerate(test_students, 1):
        print(f"\n{i}. Testing login for {student['name']} ({student['student_id']})")
        print(f"   📧 Email: {student['email']}")
        print(f"   🔑 Password: {student['password']}")
        
        login_data = {
            "email": student["email"],
            "password": student["password"]
        }
        
        try:
            response = requests.post(login_url, json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ LOGIN SUCCESS!")
                print(f"   🎯 Token: {result.get('access_token', 'N/A')[:50]}...")
                print(f"   👤 User: {result.get('user', {}).get('name', 'N/A')}")
                print(f"   📚 Section: {result.get('user', {}).get('section_name', 'N/A')}")
                print(f"   👨‍🏫 Teacher: {result.get('user', {}).get('educator_name', 'N/A')}")
            else:
                print(f"   ❌ LOGIN FAILED!")
                print(f"   📄 Status: {response.status_code}")
                print(f"   💬 Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   🔌 CONNECTION ERROR - Server not running?")
        except Exception as e:
            print(f"   ⚠️  ERROR: {str(e)}")
    
    print(f"\n{'='*50}")
    print("🏁 Student Login Test Complete!")

if __name__ == "__main__":
    test_student_login()