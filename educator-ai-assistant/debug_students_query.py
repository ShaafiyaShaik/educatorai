#!/usr/bin/env python3
"""
Debug the specific students endpoint with detailed error information
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator
from sqlalchemy.orm import joinedload

def debug_students_query():
    db = next(get_db())
    
    print("=== Database Debug ===")
    
    # Check if we have the required data
    print(f"Total educators: {db.query(Educator).count()}")
    print(f"Total sections: {db.query(Section).count()}")
    print(f"Total students: {db.query(Student).count()}")
    print(f"Total subjects: {db.query(Subject).count()}")
    print(f"Total grades: {db.query(Grade).count()}")
    
    # Find shaaf's ID
    educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    if educator:
        print(f"\nEducator shaaf ID: {educator.id}")
        
        # Check their sections
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f"Sections for shaaf: {[s.id for s in sections]}")
        
        if sections:
            section = sections[0]
            print(f"Testing section {section.id}: {section.name}")
            
            # Get students in this section
            students = db.query(Student).filter(Student.section_id == section.id).all()
            print(f"Students in section: {len(students)}")
            
            if students:
                student = students[0]
                print(f"Testing student {student.id}: {student.full_name}")
                
                # Try the problematic query
                try:
                    grades = db.query(Grade).join(Subject).filter(
                        Grade.student_id == student.id
                    ).options(joinedload(Grade.subject)).all()
                    print(f"Grades found: {len(grades)}")
                    
                    for grade in grades:
                        print(f"  Grade: {grade.percentage}% in {grade.subject.name}")
                        
                except Exception as e:
                    print(f"ERROR in grades query: {e}")
                    print(f"Exception type: {type(e)}")
                    
                    # Try without joinedload
                    try:
                        grades = db.query(Grade).join(Subject).filter(
                            Grade.student_id == student.id
                        ).all()
                        print(f"Grades without joinedload: {len(grades)}")
                    except Exception as e2:
                        print(f"ERROR even without joinedload: {e2}")
    
    db.close()

if __name__ == "__main__":
    debug_students_query()