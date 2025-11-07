#!/usr/bin/env python3
"""
Create a debug endpoint to test student authentication
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, get_db
from app.models.student import Student
from sqlalchemy.orm import sessionmaker
from app.core.auth import verify_password

def debug_authenticate_student(email: str, password: str):
    """Debug version of authenticate_student function"""
    print(f"🔍 Debug authenticate_student called with:")
    print(f"   📧 Email: {email}")
    print(f"   🔑 Password: {password}")
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Find student
        print(f"\n1. Looking for student with email: {email}")
        student = db.query(Student).filter(Student.email == email).first()
        
        if not student:
            print(f"   ❌ No student found with email: {email}")
            return False
            
        print(f"   ✅ Student found: {student.first_name} {student.last_name}")
        print(f"   🆔 Student ID: {student.student_id}")
        print(f"   ✅ Active: {student.is_active}")
        print(f"   🔑 Stored hash: {student.password_hash[:50]}...")
        
        # Step 2: Verify password
        print(f"\n2. Verifying password...")
        print(f"   🔑 Input password: '{password}'")
        
        is_valid = verify_password(password, student.password_hash)
        print(f"   🔐 Password verification result: {is_valid}")
        
        if not is_valid:
            print(f"   ❌ Password verification failed")
            return False
            
        print(f"   ✅ Password verification successful")
        return student
        
    except Exception as e:
        print(f"   ❌ Exception during authentication: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_debug_auth():
    """Test the debug authentication function"""
    test_accounts = [
        {"email": "student1@school.com", "password": "student123"},
        {"email": "S101@gmail.com", "password": "password123"}
    ]
    
    print("🧪 Testing Debug Student Authentication")
    print("=" * 60)
    
    for i, account in enumerate(test_accounts, 1):
        print(f"\nTest {i}: {account['email']} / {account['password']}")
        print("=" * 60)
        
        result = debug_authenticate_student(account['email'], account['password'])
        
        if result:
            print(f"✅ Authentication SUCCESS for {account['email']}")
        else:
            print(f"❌ Authentication FAILED for {account['email']}")

if __name__ == "__main__":
    test_debug_auth()