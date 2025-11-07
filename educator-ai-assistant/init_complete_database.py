#!/usr/bin/env python3
"""
Initialize database with sample data for testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, init_db
from app.models.educator import Educator
from app.models.student import Section, Student, Grade, Subject
from app.models.meeting_schedule import Meeting, MeetingRecipient
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_sample_data():
    """Create sample data for testing"""
    print("🔄 Initializing database and creating sample data...")
    
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
        
        print("�‍🏫 Creating educators...")
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
            },
            {
                "email": "neha.singh@school.com",
                "password": "password123", 
                "first_name": "Neha",
                "last_name": "Singh"
            }
        ]
        
        educators = []
        for data in educators_data:
            educator = Educator(
                email=data["email"],
                hashed_password=generate_password_hash(data["password"]),
                first_name=data["first_name"],
                last_name=data["last_name"],
                is_active=True
            )
            educators.append(educator)
            session.add(educator)
        
        session.flush()  # Get educator IDs
        
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
            },
            {
                "email": "neha.singh@school.com",
                "password": "password123", 
                "first_name": "Neha",
                "last_name": "Singh"
            }
        ]
        
        educators = []
        for data in educators_data:
            educator = Educator(
                email=data["email"],
                hashed_password=generate_password_hash(data["password"]),
                first_name=data["first_name"],
                last_name=data["last_name"],
                is_active=True
            )
            educators.append(educator)
            session.add(educator)
        
        session.flush()  # Get educator IDs
        
        print("🏫 Creating sections...")
        sections_data = [
            {"name": "Mathematics Section A", "educator_idx": 0, "subject_idx": 0},
            {"name": "Mathematics Section B", "educator_idx": 0, "subject_idx": 0},
            {"name": "Science Section A", "educator_idx": 1, "subject_idx": 1},
            {"name": "Science Section B", "educator_idx": 1, "subject_idx": 1},
            {"name": "English Section A", "educator_idx": 2, "subject_idx": 2},
            {"name": "English Section B", "educator_idx": 2, "subject_idx": 2}
        ]
        
        sections = []
        for data in sections_data:
            section = Section(
                name=data["name"],
                educator_id=educators[data["educator_idx"]].id,
                subject_id=subjects[data["subject_idx"]].id
            )
            sections.append(section)
            session.add(section)
        
        session.flush()  # Get section IDs
        
        print("🎓 Creating students...")
        students_data = [
            {"email": "student1@school.com", "name": "Arjun Patel", "section_idx": 0},
            {"email": "student2@school.com", "name": "Priya Sharma", "section_idx": 0},
            {"email": "student3@school.com", "name": "Rahul Kumar", "section_idx": 1},
            {"email": "student4@school.com", "name": "Sneha Gupta", "section_idx": 1},
            {"email": "student5@school.com", "name": "Vikram Singh", "section_idx": 2},
            {"email": "student6@school.com", "name": "Anjali Mehta", "section_idx": 2},
            {"email": "student7@school.com", "name": "Rohan Joshi", "section_idx": 3},
            {"email": "student8@school.com", "name": "Kavya Reddy", "section_idx": 3},
            {"email": "student9@school.com", "name": "Aditya Nair", "section_idx": 4},
            {"email": "student10@school.com", "name": "Isha Desai", "section_idx": 4},
            {"email": "student11@school.com", "name": "Manish Agarwal", "section_idx": 5},
            {"email": "student12@school.com", "name": "Divya Iyer", "section_idx": 5}
        ]
        
        students = []
        for data in students_data:
            first_name, last_name = data["name"].split(" ", 1)
            student = Student(
                email=data["email"],
                hashed_password=generate_password_hash("student123"),
                first_name=first_name,
                last_name=last_name,
                section_id=sections[data["section_idx"]].id,
                is_active=True
            )
            students.append(student)
            session.add(student)
        
        session.flush()
        
        print("📊 Creating sample grades...")
        # Create some sample grades for the first section
        for i in range(4):
            grade = Grade(
                student_id=students[i % 2].id,  # First two students
                subject_id=subjects[0].id,  # Mathematics
                assignment_name=f"Test {i + 1}",
                score=85 + (i * 5),
                max_score=100,
                date_recorded=datetime.utcnow()
            )
            session.add(grade)
        
        # Commit all changes
        session.commit()
        
        print("✅ Sample data created successfully!")
        print(f"   📚 {len(subjects)} subjects")
        print(f"   👨‍🏫 {len(educators)} educators") 
        print(f"   🏫 {len(sections)} sections")
        print(f"   🎓 {len(students)} students")
        print(f"   📊 4 sample grades")
        
        print("\n🔐 Login credentials:")
        for educator in educators:
            print(f"   📧 {educator.email} / password123")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_sample_data()