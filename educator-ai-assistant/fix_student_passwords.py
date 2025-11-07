#!/usr/bin/env python3
"""
Fix student password hashes - replace dummy hashes with proper bcrypt hashes
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.auth import get_password_hash
from app.models.student import Student

# Database setup
DATABASE_URL = "sqlite:///./educator_db.sqlite"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_student_passwords():
    """Fix all student password hashes"""
    
    print("🔧 Fixing Student Password Hashes")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Get all students with dummy hashes
        students = db.query(Student).filter(
            Student.password_hash.like('%dummy_hash%')
        ).all()
        
        print(f"📊 Found {len(students)} students with dummy password hashes")
        
        if not students:
            print("✅ No students need password fixes!")
            return
        
        # The standard password for all students is "student123"
        correct_password = "student123"
        correct_hash = get_password_hash(correct_password)
        
        print(f"🔑 Generated proper hash for password: {correct_password}")
        print(f"🔐 Hash: {correct_hash}")
        
        updated_count = 0
        
        for student in students:
            old_hash = student.password_hash
            student.password_hash = correct_hash
            updated_count += 1
            
            if updated_count <= 5:  # Show first 5 as examples
                print(f"\n{updated_count}. 🎓 {student.first_name} {student.last_name}")
                print(f"   📧 Email: {student.email}")
                print(f"   🆔 ID: {student.student_id}")
                print(f"   ❌ Old: {old_hash}")
                print(f"   ✅ New: {correct_hash[:50]}...")
        
        if updated_count > 5:
            print(f"\n... and {updated_count - 5} more students")
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Successfully updated {updated_count} student password hashes!")
        
        # Verify the fix worked
        print(f"\n🔍 Verification:")
        test_student = db.query(Student).filter(
            Student.email == "jennifer.colon@student.edu"
        ).first()
        
        if test_student:
            print(f"📧 Test student: {test_student.first_name} {test_student.last_name}")
            print(f"🔐 Hash starts with: {test_student.password_hash[:20]}...")
            
            # Test password verification
            from app.core.auth import verify_password
            is_valid = verify_password("student123", test_student.password_hash)
            print(f"🧪 Password verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    print(f"\n{'='*50}")
    print("🏁 Student Password Fix Complete!")

if __name__ == "__main__":
    fix_student_passwords()