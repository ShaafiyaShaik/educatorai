#!/usr/bin/env python3
"""
Simple database initialization script for testing meeting scheduler
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, init_db
from app.models.educator import Educator
from app.models.student import Section, Student, Grade, Subject
from sqlalchemy.orm import sessionmaker
from app.core.auth import get_password_hash
from datetime import datetime

def create_basic_data():
    """Create basic data for testing"""
    print("🔄 Initializing database...")
    
    # Initialize database
    init_db()
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Check if data already exists
        existing_educators = session.query(Educator).count()
        if existing_educators > 0:
            print(f"✅ Database already has {existing_educators} educators")
            return
        
        print("👨‍🏫 Creating educators...")
        educators_data = [
            {
                "email": "ananya.rao@school.com",
                "password": "password123",
                "first_name": "Ananya",
                "last_name": "Rao"
            },
            {
                "email": "kiran.verma@school.com", 
                "password": "password123",
                "first_name": "Kiran",
                "last_name": "Verma"
            }
        ]
        
        educators = []
        for data in educators_data:
            educator = Educator(
                email=data["email"],
                hashed_password=get_password_hash(data["password"]),
                first_name=data["first_name"],
                last_name=data["last_name"],
                is_active=True
            )
            educators.append(educator)
            session.add(educator)
        
        session.flush()  # Get educator IDs
        
        print("🏫 Creating sections...")
        sections_data = [
            {"name": "Mathematics Section A", "educator_idx": 0},
            {"name": "Science Section A", "educator_idx": 1}
        ]
        
        sections = []
        for data in sections_data:
            section = Section(
                name=data["name"],
                educator_id=educators[data["educator_idx"]].id
            )
            sections.append(section)
            session.add(section)
        
        session.flush()  # Get section IDs
        
        print("🎓 Creating students...")
        students_data = [
            {"email": "student1@school.com", "name": "Arjun Patel", "section_idx": 0},
            {"email": "student2@school.com", "name": "Priya Sharma", "section_idx": 0},
            {"email": "student3@school.com", "name": "Rahul Kumar", "section_idx": 1},
            {"email": "student4@school.com", "name": "Sneha Gupta", "section_idx": 1}
        ]
        
        students = []
        for i, data in enumerate(students_data):
            first_name, last_name = data["name"].split(" ", 1)
            student = Student(
                student_id=f"STU{i+1:03d}",  # STU001, STU002, etc.
                email=data["email"],
                password_hash=get_password_hash("student123"),
                first_name=first_name,
                last_name=last_name,
                roll_number=i+1,
                section_id=sections[data["section_idx"]].id,
                is_active=True
            )
            students.append(student)
            session.add(student)
        
        # Commit all changes
        session.commit()
        
        print("✅ Basic data created successfully!")
        print(f"   👨‍🏫 {len(educators)} educators") 
        print(f"   🏫 {len(sections)} sections")
        print(f"   🎓 {len(students)} students")
        
        print("\n🔐 Login credentials:")
        for educator in educators:
            print(f"   📧 {educator.email} / password123")
            
    except Exception as e:
        print(f"❌ Error creating data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_basic_data()