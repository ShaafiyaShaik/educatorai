#!/usr/bin/env python3
"""
Check all student accounts in database including demo ones
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.student import Student
from sqlalchemy.orm import sessionmaker
from app.core.auth import verify_password

def check_all_students():
    """Check all student accounts in database"""
    print("🎓 All Student Accounts in Database")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get all students
        students = session.query(Student).all()
        print(f"Total students found: {len(students)}")
        print()
        
        demo_emails = ["S101@gmail.com", "S102@gmail.com", "S201@gmail.com"]
        
        for student in students:
            print(f"🎓 {student.first_name} {student.last_name}")
            print(f"   📧 Email: {student.email}")
            print(f"   🆔 Student ID: {student.student_id}")
            print(f"   📋 Roll Number: {student.roll_number}")
            print(f"   ✅ Active: {student.is_active}")
            print(f"   🔑 Password Hash: {student.password_hash[:30]}...")
            
            # Test password verification
            test_password = "student123"
            is_valid = verify_password(test_password, student.password_hash)
            print(f"   🔐 Password 'student123' valid: {is_valid}")
            
            # Also test with password123
            is_valid2 = verify_password("password123", student.password_hash)
            print(f"   🔐 Password 'password123' valid: {is_valid2}")
            print()
        
        print("🔍 Checking for demo accounts...")
        for email in demo_emails:
            student = session.query(Student).filter(Student.email == email).first()
            if student:
                print(f"✅ Found demo account: {email}")
            else:
                print(f"❌ Demo account not found: {email}")
        
        print("\n📝 Creating missing demo accounts...")
        
        # Create demo accounts if they don't exist
        demo_accounts = [
            {"email": "S101@gmail.com", "first_name": "Demo", "last_name": "Student1", "student_id": "S101"},
            {"email": "S102@gmail.com", "first_name": "Demo", "last_name": "Student2", "student_id": "S102"},
            {"email": "S201@gmail.com", "first_name": "Demo", "last_name": "Student3", "student_id": "S201"}
        ]
        
        from app.core.auth import get_password_hash
        
        created_count = 0
        for account in demo_accounts:
            existing = session.query(Student).filter(Student.email == account["email"]).first()
            if not existing:
                # Create the account
                new_student = Student(
                    email=account["email"],
                    password_hash=get_password_hash("password123"),
                    first_name=account["first_name"],
                    last_name=account["last_name"],
                    student_id=account["student_id"],
                    roll_number=int(account["student_id"][1:]),  # Extract number from S101 -> 101
                    section_id=1,  # Assign to first section
                    is_active=True
                )
                session.add(new_student)
                created_count += 1
                print(f"   ➕ Created: {account['email']} / password123")
        
        if created_count > 0:
            session.commit()
            print(f"✅ Created {created_count} demo accounts")
        else:
            print("ℹ️  All demo accounts already exist")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    check_all_students()