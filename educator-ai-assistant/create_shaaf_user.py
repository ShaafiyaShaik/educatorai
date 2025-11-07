#!/usr/bin/env python3

"""
Create a user with shaaf@gmail.com email
"""

import sqlite3
from app.core.auth import get_password_hash
from app.core.database import engine
from app.models.educator import Educator
from sqlalchemy.orm import sessionmaker

def create_shaaf_user():
    """Create a user with shaaf@gmail.com"""
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        if existing:
            print("User shaaf@gmail.com already exists!")
            print(f"Password: password123")
            return
        
        # Create the user
        hashed_password = get_password_hash("password123")
        educator = Educator(
            email="shaaf@gmail.com",
            first_name="Shaaf",
            last_name="User",
            employee_id="EMP004",
            department="Computer Science",
            title="Lecturer",
            hashed_password=hashed_password
        )
        
        db.add(educator)
        db.commit()
        
        print("✅ Created user: shaaf@gmail.com")
        print("📧 Email: shaaf@gmail.com")
        print("🔑 Password: password123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_shaaf_user()