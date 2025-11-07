#!/usr/bin/env python3
"""
Update passwords in the database to use the correct bcrypt hashes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.educator import Educator
from app.models.student import Student
from sqlalchemy.orm import sessionmaker
from app.core.auth import get_password_hash

def update_passwords():
    """Update all passwords to use proper bcrypt hashes"""
    print("🔐 Updating passwords with correct bcrypt hashes...")
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Update educator passwords
        educators = session.query(Educator).all()
        print(f"Found {len(educators)} educators")
        
        for educator in educators:
            # Set password to "password123" for all educators
            new_hash = get_password_hash("password123")
            educator.hashed_password = new_hash
            print(f"  Updated password for {educator.email}")
        
        # Update student passwords  
        students = session.query(Student).all()
        print(f"Found {len(students)} students")
        
        for student in students:
            # Set password to "student123" for all students
            new_hash = get_password_hash("student123")
            student.password_hash = new_hash
            print(f"  Updated password for {student.email}")
        
        session.commit()
        print("✅ All passwords updated successfully!")
        
        print("\n🔐 Login credentials:")
        for educator in educators:
            print(f"   📧 {educator.email} / password123")
        
    except Exception as e:
        print(f"❌ Error updating passwords: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    update_passwords()