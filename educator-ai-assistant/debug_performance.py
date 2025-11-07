#!/usr/bin/env python3
"""
Debug the performance calculation
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.models.student import Section, Student, Grade, Subject
from app.api.performance_views import calculate_student_performance_detailed, get_section_performance
from sqlalchemy.orm import joinedload

def debug_performance():
    db = next(get_db())
    
    # Get shaaf's first section
    educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    section = db.query(Section).filter(Section.educator_id == educator.id).first()
    
    print(f"Testing section {section.id}: {section.name}")
    
    # Get students in this section
    students = db.query(Student).filter(Student.section_id == section.id).all()
    print(f"Students in section: {len(students)}")
    
    if students:
        student = students[0]
        print(f"\nTesting student: {student.full_name}")
        
        # Get raw grades
        grades = db.query(Grade).options(joinedload(Grade.subject)).filter(
            Grade.student_id == student.id
        ).all()
        
        print(f"Raw grades: {len(grades)}")
        for grade in grades:
            print(f"  {grade.subject.name}: {grade.marks_obtained}/{grade.total_marks} = {grade.percentage}%")
        
        # Test the performance calculation
        perf = calculate_student_performance_detailed(student, db)
        print(f"\nCalculated performance:")
        print(f"  Average: {perf.average_score}%")
        print(f"  Status: {perf.status}")
        print(f"  Passed subjects: {perf.passed_subjects}")
        print(f"  Failed subjects: {perf.failed_subjects}")
    
    # Test section performance
    print(f"\n=== Section Performance ===")
    section_perf = get_section_performance(section.id, db, educator.id)
    print(f"Total students: {section_perf.total_students}")
    print(f"Average score: {section_perf.average_score}")
    print(f"Pass rate: {section_perf.pass_rate}%")
    print(f"Subject averages: {section_perf.subject_averages}")
    
    db.close()

if __name__ == "__main__":
    debug_performance()