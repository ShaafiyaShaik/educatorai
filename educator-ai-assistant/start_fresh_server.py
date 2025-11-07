#!/usr/bin/env python3
"""
Start server on a different port to avoid conflicts
"""
import os
import sys
import time

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Fresh Server on Port 8002...")
    
    # Check database status first
    from app.core.database import get_db
    from app.models.student import Student, Section, Grade
    from app.models.educator import Educator
    
    db = next(get_db())
    
    # Check Shaaf's sections specifically
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    if shaaf:
        sections = db.query(Section).filter(Section.educator_id == shaaf.id).all()
        total_students = 0
        
        print(f"📊 Shaaf's Data Check:")
        print(f"   Educator ID: {shaaf.id}")
        print(f"   Sections: {len(sections)}")
        
        for section in sections:
            student_count = db.query(Student).filter(Student.section_id == section.id).count()
            total_students += student_count
            print(f"   - {section.name}: {student_count} students")
        
        print(f"   Total Students: {total_students}")
    
    db.close()
    
    # Start server on port 8002
    uvicorn.run(app, host="localhost", port=8002, log_level="info")