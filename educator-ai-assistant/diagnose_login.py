#!/usr/bin/env python3
"""
Diagnose login issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.educator import Educator
from sqlalchemy.orm import sessionmaker
from app.core.auth import verify_password

def diagnose_login():
    """Check user and password verification"""
    print("🔍 Diagnosing login issues...")
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Check if user exists
        email = "ananya.rao@school.com"
        password = "password123"
        
        educator = session.query(Educator).filter(Educator.email == email).first()
        
        if not educator:
            print(f"❌ No educator found with email: {email}")
            return
            
        print(f"✅ Found educator: {educator.first_name} {educator.last_name}")
        print(f"   Email: {educator.email}")
        print(f"   Active: {educator.is_active}")
        print(f"   Password hash: {educator.hashed_password[:50]}...")
        
        # Test password verification
        is_valid = verify_password(password, educator.hashed_password)
        print(f"   Password valid: {is_valid}")
        
        if not is_valid:
            # Try manual check
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            manual_check = pwd_context.verify(password, educator.hashed_password)
            print(f"   Manual check: {manual_check}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    diagnose_login()