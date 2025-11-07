#!/usr/bin/env python3
"""
Test database connection and verify accounts exist
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import get_db, SessionLocal
from app.models.educator import Educator
from app.core.config import settings

print("🔍 Testing database connection...")
print(f"Database URL: {settings.DATABASE_URL}")

# Test direct database connection
db = SessionLocal()
try:
    # Query for educators
    educators = db.query(Educator).all()
    print(f"\n📊 Found {len(educators)} educators in database:")
    
    for educator in educators:
        print(f"  📧 {educator.email} - {educator.first_name} {educator.last_name}")
        print(f"      Employee ID: {educator.employee_id}")
        print(f"      Active: {educator.is_active}")
        print(f"      Hash starts: {educator.hashed_password[:20]}...")
        print()
        
    # Test specific login
    target_email = "ananya.rao@school.com"
    educator = db.query(Educator).filter(Educator.email == target_email).first()
    
    if educator:
        print(f"✅ Found {target_email}")
        print(f"   Name: {educator.first_name} {educator.last_name}")
        print(f"   Active: {educator.is_active}")
        
        # Test password verification
        from app.core.auth import verify_password
        test_password = "Ananya@123"
        is_valid = verify_password(test_password, educator.hashed_password)
        print(f"   Password '{test_password}' valid: {is_valid}")
        
    else:
        print(f"❌ {target_email} not found in database!")
        
except Exception as e:
    print(f"❌ Database error: {e}")
finally:
    db.close()