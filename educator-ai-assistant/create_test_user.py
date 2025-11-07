#!/usr/bin/env python3

"""
Create a test user account for shaaf@gmail.com
"""

from app.core.database import engine, Base
from app.models.educator import Educator
from app.core.auth import get_password_hash
from sqlalchemy.orm import sessionmaker

# Import all models to ensure they're registered
import app.models.educator
import app.models.student

def create_test_user():
    """Create the shaaf@gmail.com user"""
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        
        if not existing_user:
            hashed_password = get_password_hash("password123")
            user = Educator(
                email="shaaf@gmail.com",
                first_name="Shaaf",
                last_name="User",
                employee_id=None,  # Allow null to avoid unique constraint
                department="Computer Science",
                title="Professor",
                hashed_password=hashed_password
            )
            db.add(user)
            db.commit()
            print(f"Created user: shaaf@gmail.com with password: password123")
        else:
            print(f"User shaaf@gmail.com already exists (ID: {existing_user.id})")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()