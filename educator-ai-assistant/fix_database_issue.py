#!/usr/bin/env python3
"""
Check and fix the actual database issue
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator

def check_and_fix_database():
    db = next(get_db())
    
    print("=== CURRENT DATABASE INVESTIGATION ===")
    
    # Check what sections exist
    sections = db.query(Section).all()
    print(f"All sections in database:")
    for section in sections:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        print(f"  ID {section.id}: {section.name} (Educator {section.educator_id}) - {student_count} students")
    
    # Check Shaaf specifically
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    print(f"\nShaaf's educator ID: {shaaf.id}")
    
    # Check which sections belong to Shaaf
    shaaf_sections = db.query(Section).filter(Section.educator_id == shaaf.id).all()
    print(f"Shaaf's sections:")
    for section in shaaf_sections:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        print(f"  ID {section.id}: {section.name} - {student_count} students")
    
    # The problem: Section 6 and 7 are returning 7 and 0 students
    # Let's check section 6 specifically
    section_6 = db.query(Section).filter(Section.id == 6).first()
    if section_6:
        students_in_6 = db.query(Student).filter(Student.section_id == 6).all()
        print(f"\nSection 6 ({section_6.name}) detailed check:")
        print(f"  Belongs to educator: {section_6.educator_id}")
        print(f"  Students: {len(students_in_6)}")
        if students_in_6:
            print("  Sample students:")
            for student in students_in_6[:3]:
                print(f"    {student.student_id}: {student.full_name}")
    
    # Check if there are other sections with students
    print(f"\nAll students by section:")
    for i in range(1, 10):
        count = db.query(Student).filter(Student.section_id == i).count()
        if count > 0:
            section = db.query(Section).filter(Section.id == i).first()
            section_name = section.name if section else "Unknown"
            print(f"  Section {i} ({section_name}): {count} students")
    
    # Now let's see if there are sections with 30 students each
    print(f"\n=== THE REAL ISSUE ===")
    print("We need to check what sections have 30 students as we created...")
    
    sections_with_30 = []
    for section in sections:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        if student_count == 30:
            sections_with_30.append(section)
    
    print(f"Sections with 30 students: {len(sections_with_30)}")
    for section in sections_with_30:
        print(f"  ID {section.id}: {section.name} (Educator {section.educator_id})")
    
    # The fix: Make sure Shaaf owns the sections with students
    if sections_with_30:
        print(f"\n=== FIXING THE ASSIGNMENT ===")
        for section in sections_with_30:
            if section.educator_id != shaaf.id:
                print(f"Reassigning section {section.id} ({section.name}) to Shaaf")
                section.educator_id = shaaf.id
        
        db.commit()
        print("✅ Fixed section assignments")
    
    # Verify the fix
    print(f"\n=== VERIFICATION ===")
    shaaf_sections_after = db.query(Section).filter(Section.educator_id == shaaf.id).all()
    total_students = 0
    for section in shaaf_sections_after:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        total_students += student_count
        print(f"  {section.name}: {student_count} students")
    
    print(f"Total students under Shaaf: {total_students}")
    
    db.close()

if __name__ == "__main__":
    check_and_fix_database()