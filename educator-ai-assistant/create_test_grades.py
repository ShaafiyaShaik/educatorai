#!/usr/bin/env python3
"""
Create test grades for students to show real performance data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.student import Student, Subject, Grade
from datetime import datetime, timedelta
import random

def create_test_grades():
    """Create test grades for all students"""
    db: Session = SessionLocal()
    
    try:
        # Get all students
        students = db.query(Student).all()
        print(f"Found {len(students)} students")
        
        # Get all subjects
        subjects = db.query(Subject).all()
        print(f"Found {len(subjects)} subjects")
        
        if not subjects:
            print("No subjects found. Creating default subjects...")
            # Create default subjects for each section
            sections = db.query(Student.section_id).distinct().all()
            for section_tuple in sections:
                section_id = section_tuple[0]
                
                # Create Math, Science, English subjects
                math_subject = Subject(
                    name="Mathematics",
                    code="MATH",
                    section_id=section_id,
                    educator_id=1  # Assuming Ananya is educator 1
                )
                science_subject = Subject(
                    name="Science",
                    code="SCI",
                    section_id=section_id,
                    educator_id=1
                )
                english_subject = Subject(
                    name="English",
                    code="ENG",
                    section_id=section_id,
                    educator_id=1
                )
                
                db.add(math_subject)
                db.add(science_subject)
                db.add(english_subject)
            
            db.commit()
            subjects = db.query(Subject).all()
            print(f"Created {len(subjects)} subjects")
        
        # Create grades for each student
        for student in students:
            print(f"Creating grades for {student.first_name} {student.last_name}")
            
            # Get subjects for this student's section
            student_subjects = db.query(Subject).filter(Subject.section_id == student.section_id).all()
            
            for subject in student_subjects:
                # Check if grade already exists
                existing_grade = db.query(Grade).filter(
                    Grade.student_id == student.id,
                    Grade.subject_id == subject.id
                ).first()
                
                if not existing_grade:
                    # Generate random but realistic grades
                    if subject.name == "Mathematics":
                        marks = random.randint(60, 95)  # Math tends to be higher
                    elif subject.name == "Science":
                        marks = random.randint(55, 90)  # Science moderate
                    else:  # English
                        marks = random.randint(65, 85)  # English consistent
                    
                    grade = Grade(
                        student_id=student.id,
                        subject_id=subject.id,
                        marks_obtained=marks,
                        total_marks=100,
                        percentage=float(marks),
                        grade_letter="A" if marks >= 80 else "B" if marks >= 70 else "C" if marks >= 60 else "D",
                        assessment_type="Final Exam",
                        assessment_date=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.add(grade)
                    print(f"  {subject.name}: {marks}%")
        
        db.commit()
        print("✅ Test grades created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating test grades: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_grades()