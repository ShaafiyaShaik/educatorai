#!/usr/bin/env python3
"""
Check current database state and start the FastAPI server
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Section, Student, Grade
from app.models.educator import Educator

def check_database_state():
    db = next(get_db())
    
    print("=== Current Database State ===")
    
    # Check educators
    educators = db.query(Educator).all()
    print(f"Educators: {len(educators)}")
    for educator in educators:
        print(f"  {educator.id}: {educator.full_name} ({educator.email})")
    
    # Check sections
    sections = db.query(Section).all()
    print(f"\nSections: {len(sections)}")
    for section in sections:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        grade_count = db.query(Grade).join(Student).filter(Student.section_id == section.id).count()
        print(f"  {section.id}: {section.name} (Educator {section.educator_id}) - {student_count} students, {grade_count} grades")
    
    # Check total counts
    total_students = db.query(Student).count()
    total_grades = db.query(Grade).count()
    
    print(f"\nTotals:")
    print(f"  Students: {total_students}")
    print(f"  Grades: {total_grades}")
    
    # Check specific educator's data (shaaf)
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    if shaaf:
        shaaf_sections = db.query(Section).filter(Section.educator_id == shaaf.id).all()
        print(f"\nShaaf's sections: {len(shaaf_sections)}")
        for section in shaaf_sections:
            student_count = db.query(Student).filter(Student.section_id == section.id).count()
            print(f"  {section.name}: {student_count} students")
    
    db.close()

if __name__ == "__main__":
    check_database_state()
    
    # Start the server
    print("\n=== Starting FastAPI Server ===")
    from app.main import app
    import uvicorn
    
    try:
        uvicorn.run(app, host="localhost", port=8001, log_level="info")
    except Exception as e:
        print(f"Server startup error: {e}")