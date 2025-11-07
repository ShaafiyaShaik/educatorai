#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.database import SessionLocal
    from app.models.educator import Educator
    from app.models.student import Student
    from app.core.auth import verify_password
    
    print("🔍 Quick Database Check")
    print("=" * 50)
    
    db = SessionLocal()
    
    # Check educators
    educators = db.query(Educator).all()
    print(f"📚 Found {len(educators)} educators:")
    for edu in educators:
        print(f"  - {edu.email} | {edu.full_name} | Active: {edu.is_active}")
        if edu.email == "ananya.rao@school.com":
            print(f"    Password check: {verify_password('Ananya@123', edu.hashed_password)}")
    
    print()
    
    # Check students  
    students = db.query(Student).all()
    print(f"🎓 Found {len(students)} students:")
    for student in students[:5]:  # Show first 5
        print(f"  - {student.email} | {student.full_name} | Active: {student.is_active}")
        if student.email == "rahul.s101@school.com":
            print(f"    Password check: {verify_password('student123', student.password_hash)}")
    
    if len(students) > 5:
        print(f"  ... and {len(students) - 5} more")
    
    db.close()
    print("\n✅ Database check completed successfully!")
    
except Exception as e:
    print(f"❌ Database check failed: {str(e)}")
    import traceback
    traceback.print_exc()