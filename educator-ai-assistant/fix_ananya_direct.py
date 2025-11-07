#!/usr/bin/env python3
"""
Direct password hash update using raw bcrypt
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.educator import Educator
from sqlalchemy.orm import sessionmaker
import bcrypt

def hash_password_direct(password: str) -> str:
    """Hash password using bcrypt directly"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password_direct(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def fix_ananya_password():
    """Set Ananya's password to 'Ananya@123' using direct bcrypt"""
    print("🔐 Setting Ananya's Password (Direct Method)")
    print("=" * 50)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Find Ananya
        ananya = session.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        
        if not ananya:
            print("❌ Ananya not found!")
            return
            
        print(f"✅ Found: {ananya.first_name} {ananya.last_name}")
        
        # Hash the password 'Ananya@123' directly
        new_hash = hash_password_direct("Ananya@123")
        ananya.hashed_password = new_hash
        
        session.commit()
        
        print("✅ Password hash updated")
        
        # Verify it works
        if verify_password_direct("Ananya@123", ananya.hashed_password):
            print("🎉 Password 'Ananya@123' verified!")
        else:
            print("❌ Verification failed")
            
        print("\n📝 CREDENTIAL UPDATE:")
        print("📧 ananya.rao@school.com")
        print("🔑 Ananya@123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fix_ananya_password()