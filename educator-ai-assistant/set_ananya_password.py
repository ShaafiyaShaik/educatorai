#!/usr/bin/env python3
"""
Set Ananya's password to 'Ananya@123' specifically, keep all others unchanged
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.educator import Educator
from sqlalchemy.orm import sessionmaker
from app.core.auth import get_password_hash, verify_password

def set_ananya_specific_password():
    """Set Ananya's password to 'Ananya@123' specifically"""
    print("🔐 Setting Ananya's Password to 'Ananya@123'")
    print("=" * 50)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Find Ananya specifically
        ananya = session.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        
        if not ananya:
            print("❌ Ananya not found!")
            return
            
        print(f"✅ Found educator: {ananya.first_name} {ananya.last_name}")
        print(f"📧 Email: {ananya.email}")
        
        # Set her password to 'Ananya@123'
        new_hash = get_password_hash("Ananya@123")
        ananya.hashed_password = new_hash
        
        session.commit()
        
        print(f"✅ Updated Ananya's password to 'Ananya@123'")
        
        # Verify it works
        if verify_password("Ananya@123", ananya.hashed_password):
            print("🎉 Password verification successful!")
        else:
            print("❌ Password verification failed!")
        
        # Check other educators are unchanged
        print("\n🔍 Verifying other educators:")
        other_educators = session.query(Educator).filter(Educator.email != "ananya.rao@school.com").all()
        
        for educator in other_educators:
            if verify_password("password123", educator.hashed_password):
                print(f"   ✅ {educator.email} - password123 still works")
            else:
                print(f"   ❌ {educator.email} - password may have changed")
        
        # Check students are unchanged
        print("\n🎓 Verifying students are unchanged:")
        from app.models.student import Student
        students = session.query(Student).all()
        
        student_count_ok = 0
        for student in students:
            if verify_password("student123", student.password_hash):
                student_count_ok += 1
        
        print(f"   ✅ {student_count_ok}/{len(students)} students still have 'student123'")
        
        print("\n" + "=" * 50)
        print("📝 UPDATED EDUCATOR CREDENTIALS:")
        print("=" * 50)
        print("📧 ananya.rao@school.com | 🔑 Ananya@123")
        print("📧 kiran.verma@school.com | 🔑 password123")
        print("📧 neha.singh@school.com | 🔑 password123")
        print("\n🎓 All 12 students still use: student123")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    set_ananya_specific_password()