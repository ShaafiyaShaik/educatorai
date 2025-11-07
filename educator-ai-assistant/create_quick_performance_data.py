#!/usr/bin/env python3
"""
Create performance data for shaaf@gmail.com educator
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.database import get_db
from app.models.student import Student, Grade
from app.models.educator import Educator
from app.models.student import Section, Subject
import random

def create_performance_data():
    """Create sample performance data"""
    db = next(get_db())
    
    try:
        # Get shaaf educator
        educator = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        if not educator:
            print("❌ Educator shaaf@gmail.com not found")
            return
            
        print(f"✅ Found educator: {educator.first_name} {educator.last_name} (ID: {educator.id})")
        
        # Get sections for this educator
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f"📚 Found {len(sections)} sections")
        
        for section in sections:
            print(f"  - {section.name}")
            
            # Get students in this section
            students = db.query(Student).filter(Student.section_id == section.id).all()
            print(f"    Students: {len(students)}")
            
            if students:
                # Get subjects for this section
                subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
                print(f"    Subjects: {len(subjects)}")
                
                # Create grades for each student in each subject
                grades_created = 0
                for student in students:
                    for subject in subjects:
                        # Check if grade already exists
                        existing_grade = db.query(Grade).filter(
                            Grade.student_id == student.id,
                            Grade.subject_id == subject.id
                        ).first()
                        
                        if not existing_grade:
                            # Create a random grade (60-95 range for realistic distribution)
                            score = random.randint(60, 95)
                            grade = Grade(
                                student_id=student.id,
                                subject_id=subject.id,
                                score=score,
                                total_score=100,
                                grade_type="midterm"
                            )
                            db.add(grade)
                            grades_created += 1
                
                print(f"    Created {grades_created} new grades")
        
        db.commit()
        print("✅ Performance data created successfully!")
        
        # Verify data
        total_grades = db.query(Grade).count()
        print(f"📊 Total grades in database: {total_grades}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 Creating performance data for shaaf@gmail.com...")
    create_performance_data()
    print("✨ Data creation completed!")