#!/usr/bin/env python3

"""
Script to recreate the database with proper schema and sample data
"""

import sqlite3
from app.core.database import engine, Base
from app.models.educator import Educator
from app.models.compliance import ComplianceReport
from app.models.meeting_request import MeetingRequest
from app.models.record import Record
from app.models.schedule import Schedule
from app.models.student import Student, Section, Subject, Grade  # Add student models
from app.models.communication import Communication  # Add communication model
from app.core.auth import get_password_hash
from sqlalchemy.orm import sessionmaker

def recreate_database():
    """Recreate the database with all tables and sample data"""
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create sample educators
        print("Creating sample educators...")
        
        educators_data = [
            {
                "email": "shaafiya07@gmail.com",
                "first_name": "Shaafiya",
                "last_name": "User",
                "employee_id": "EMP001",
                "department": "Computer Science",
                "title": "Professor",
                "password": "password123"
            },
            {
                "email": "shaaf123@gmail.com", 
                "first_name": "Shaaf",
                "last_name": "Teacher",
                "employee_id": "EMP002",
                "department": "Mathematics",
                "title": "Associate Professor",
                "password": "password123"
            },
            {
                "email": "john.doe@university.edu",
                "first_name": "John",
                "last_name": "Doe",
                "employee_id": "EMP003",
                "department": "Physics",
                "title": "Assistant Professor",
                "password": "password123"
            }
        ]
        
        for educator_data in educators_data:
            # Check if educator already exists
            existing = db.query(Educator).filter(Educator.email == educator_data["email"]).first()
            if not existing:
                hashed_password = get_password_hash(educator_data["password"])
                educator = Educator(
                    email=educator_data["email"],
                    first_name=educator_data["first_name"],
                    last_name=educator_data["last_name"],
                    employee_id=educator_data["employee_id"],
                    department=educator_data["department"],
                    title=educator_data["title"],
                    hashed_password=hashed_password
                )
                db.add(educator)
                print(f"Created educator: {educator_data['email']}")
        
        # Commit educators first
        db.commit()
        
        # Create communications table manually (since it's not in models)
        print("Creating communications table...")
        from sqlalchemy import text
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_email VARCHAR(255) NOT NULL,
                recipient_email VARCHAR(255) NOT NULL,
                subject VARCHAR(500),
                content TEXT,
                status VARCHAR(50) DEFAULT 'sent',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Insert sample communications
        print("Adding sample communications...")
        sample_communications = [
            ("shaafiya07@gmail.com", "shaaf123@gmail.com", "Meeting Request", "Hi Shaaf, could we schedule a meeting to discuss the new curriculum?", "sent"),
            ("shaaf123@gmail.com", "shaafiya07@gmail.com", "Re: Meeting Request", "Sure! How about tomorrow at 2 PM?", "sent"),
            ("shaafiya07@gmail.com", "john.doe@university.edu", "Research Collaboration", "Hi John, I'd like to discuss potential collaboration on the AI project.", "sent"),
            ("john.doe@university.edu", "shaafiya07@gmail.com", "Re: Research Collaboration", "That sounds great! Let's set up a call.", "sent"),
            ("shaaf123@gmail.com", "john.doe@university.edu", "Conference Planning", "Hi John, are you attending the upcoming conference?", "sent"),
        ]
        
        for sender, recipient, subject, content, status in sample_communications:
            db.execute(text("""
                INSERT INTO communications (sender_email, recipient_email, subject, content, status)
                VALUES (:sender, :recipient, :subject, :content, :status)
            """), {
                "sender": sender,
                "recipient": recipient, 
                "subject": subject,
                "content": content,
                "status": status
            })
        
        db.commit()
        print("Database recreated successfully!")
        
        # Show what was created
        educator_count = db.query(Educator).count()
        print(f"Total educators: {educator_count}")
        
        communications_count = db.execute(text("SELECT COUNT(*) FROM communications")).fetchone()[0]
        print(f"Total communications: {communications_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    recreate_database()