#!/usr/bin/env python3
"""
Detailed diagnosis of student authentication
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.student import Student
from sqlalchemy.orm import sessionmaker
from app.core.auth import verify_password

def diagnose_student_auth():
    """Step by step diagnosis of student authentication"""
    print("🔍 Diagnosing Student Authentication")
    print("=" * 50)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Test both accounts
        test_accounts = [
            {"email": "student1@school.com", "password": "student123"},
            {"email": "S101@gmail.com", "password": "password123"}
        ]
        
        for i, account in enumerate(test_accounts, 1):
            print(f"\n{i}. Testing {account['email']}")
            print("-" * 30)
            
            # Step 1: Check if student exists
            student = session.query(Student).filter(Student.email == account['email']).first()
            
            if not student:
                print(f"   ❌ Student not found with email: {account['email']}")
                continue
                
            print(f"   ✅ Student found: {student.first_name} {student.last_name}")
            print(f"   📧 Email: {student.email}")
            print(f"   🆔 Student ID: {student.student_id}")
            print(f"   ✅ Active: {student.is_active}")
            
            # Step 2: Check password hash
            print(f"   🔑 Password Hash: {student.password_hash[:50]}...")
            
            # Step 3: Test password verification
            is_valid = verify_password(account['password'], student.password_hash)
            print(f"   🔐 Password '{account['password']}' verification: {is_valid}")
            
            if not is_valid:
                print(f"   🔧 Trying to fix password...")
                
                # Try to update the password with correct hash
                from app.core.auth import get_password_hash
                new_hash = get_password_hash(account['password'])
                student.password_hash = new_hash
                session.commit()
                
                # Test again
                is_valid_now = verify_password(account['password'], student.password_hash)
                print(f"   🔐 After fix, password verification: {is_valid_now}")
                
        print(f"\n✅ Authentication diagnosis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    diagnose_student_auth()