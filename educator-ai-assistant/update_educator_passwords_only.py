#!/usr/bin/env python3
"""
Update ONLY educator passwords without touching student accounts
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.educator import Educator
from sqlalchemy.orm import sessionmaker
from app.core.auth import get_password_hash, verify_password

def update_educator_passwords_only():
    """Update only educator passwords, leave students untouched"""
    print("🔐 Updating ONLY Educator Passwords (Students Unchanged)")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get all educators
        educators = session.query(Educator).all()
        print(f"Found {len(educators)} educators")
        print()
        
        # Test current passwords first
        print("🔍 Testing current educator passwords:")
        for educator in educators:
            print(f"📧 {educator.email}")
            
            # Test common passwords
            test_passwords = ["password123", "Ananya@123", "ananya123", "admin123"]
            current_valid = None
            
            for pwd in test_passwords:
                if verify_password(pwd, educator.hashed_password):
                    current_valid = pwd
                    break
            
            if current_valid:
                print(f"   ✅ Current password: {current_valid}")
            else:
                print(f"   ❓ Current password: Unknown")
        
        print("\n🔧 Updating educator passwords to 'password123'...")
        
        # Update educator passwords specifically
        for educator in educators:
            # Set password to "password123" for all educators
            new_hash = get_password_hash("password123")
            educator.hashed_password = new_hash
            print(f"   ✅ Updated password for {educator.email}")
        
        # Commit only educator changes
        session.commit()
        
        print("\n✅ Educator passwords updated successfully!")
        print("\n🔐 Updated Login Credentials for EDUCATORS:")
        print("=" * 50)
        for educator in educators:
            print(f"   📧 {educator.email} | 🔑 password123")
        
        # Verify students are unchanged
        print("\n🎓 Verifying student accounts are unchanged...")
        from app.models.student import Student
        students = session.query(Student).all()
        
        student_passwords_ok = 0
        for student in students:
            if verify_password("student123", student.password_hash):
                student_passwords_ok += 1
        
        print(f"   ✅ {student_passwords_ok}/{len(students)} students still have correct 'student123' password")
        
        if student_passwords_ok == len(students):
            print("   🎉 All student accounts preserved successfully!")
        else:
            print("   ⚠️ Some student passwords may have been affected")
            
    except Exception as e:
        print(f"❌ Error updating educator passwords: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    update_educator_passwords_only()