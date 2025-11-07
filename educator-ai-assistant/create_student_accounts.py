"""
Create static student accounts for testing
This script creates 10 student accounts across 3 sections as specified:
- Section A: S101-S105 (5 students)
- Section B: S201-S203 (3 students) 
- Section C: S301-S302 (2 students)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db, init_db
from app.models.student import Student, Section, Subject, Grade
from app.models.educator import Educator
from app.core.auth import get_password_hash
from datetime import datetime
import random

def create_static_student_accounts():
    """Create 10 static student accounts for testing"""
    
    # Initialize database
    init_db()
    db = next(get_db())
    
    try:
        # First, let's create sections if they don't exist
        sections_data = [
            {"name": "Section A", "id_prefix": "10"},
            {"name": "Section B", "id_prefix": "20"}, 
            {"name": "Section C", "id_prefix": "30"}
        ]
        
        # Get or create an educator for the sections
        educator = db.query(Educator).first()
        if not educator:
            print("❌ No educator found. Please create an educator first.")
            return
        
        # Create sections
        for section_data in sections_data:
            existing_section = db.query(Section).filter(Section.name == section_data["name"]).first()
            if not existing_section:
                section = Section(
                    name=section_data["name"],
                    educator_id=educator.id,
                    academic_year="2025-2026",
                    semester="Fall"
                )
                db.add(section)
                print(f"✅ Created {section_data['name']}")
        
        db.commit()
        
        # Student accounts data
        students_data = [
            # Section A (5 students)
            {"email": "S101@gmail.com", "section": "Section A", "roll": 1, "first_name": "Alice", "last_name": "Anderson", "student_id": "S101"},
            {"email": "S102@gmail.com", "section": "Section A", "roll": 2, "first_name": "Bob", "last_name": "Brown", "student_id": "S102"},
            {"email": "S103@gmail.com", "section": "Section A", "roll": 3, "first_name": "Charlie", "last_name": "Clark", "student_id": "S103"},
            {"email": "S104@gmail.com", "section": "Section A", "roll": 4, "first_name": "Diana", "last_name": "Davis", "student_id": "S104"},
            {"email": "S105@gmail.com", "section": "Section A", "roll": 5, "first_name": "Edward", "last_name": "Evans", "student_id": "S105"},
            
            # Section B (3 students)
            {"email": "S201@gmail.com", "section": "Section B", "roll": 1, "first_name": "Fiona", "last_name": "Foster", "student_id": "S201"},
            {"email": "S202@gmail.com", "section": "Section B", "roll": 2, "first_name": "George", "last_name": "Green", "student_id": "S202"},
            {"email": "S203@gmail.com", "section": "Section B", "roll": 3, "first_name": "Hannah", "last_name": "Hall", "student_id": "S203"},
            
            # Section C (2 students)
            {"email": "S301@gmail.com", "section": "Section C", "roll": 1, "first_name": "Ian", "last_name": "Irving", "student_id": "S301"},
            {"email": "S302@gmail.com", "section": "Section C", "roll": 2, "first_name": "Julia", "last_name": "Johnson", "student_id": "S302"},
        ]
        
        # Create students
        created_count = 0
        for student_data in students_data:
            # Check if student already exists
            existing_student = db.query(Student).filter(Student.email == student_data["email"]).first()
            if existing_student:
                print(f"⚠️  Student {student_data['email']} already exists, skipping...")
                continue
            
            # Get section
            section = db.query(Section).filter(Section.name == student_data["section"]).first()
            if not section:
                print(f"❌ Section {student_data['section']} not found for {student_data['email']}")
                continue
            
            # Create student
            student = Student(
                student_id=student_data["student_id"],
                first_name=student_data["first_name"],
                last_name=student_data["last_name"],
                email=student_data["email"],
                password_hash=get_password_hash("password123"),  # Static password for all
                roll_number=student_data["roll"],
                section_id=section.id,
                phone=f"555-{student_data['student_id'][-3:]}",  # Generate phone number
                guardian_email=f"parent_{student_data['student_id'].lower()}@gmail.com",
                is_active=True
            )
            
            db.add(student)
            created_count += 1
            print(f"✅ Created student: {student_data['email']} ({student_data['first_name']} {student_data['last_name']}) - {student_data['section']}, Roll {student_data['roll']}")
        
        db.commit()
        
        # Create subjects for each section
        subjects_data = [
            {"name": "Mathematics", "code": "MATH101"},
            {"name": "Science", "code": "SCI101"},
            {"name": "English", "code": "ENG101"},
        ]
        
        sections = db.query(Section).all()
        for section in sections:
            for subject_data in subjects_data:
                existing_subject = db.query(Subject).filter(
                    Subject.code == subject_data["code"],
                    Subject.section_id == section.id
                ).first()
                
                if not existing_subject:
                    subject = Subject(
                        name=subject_data["name"],
                        code=f"{subject_data['code']}_{section.name.replace(' ', '_')}",
                        section_id=section.id,
                        credits=3,
                        passing_grade=60.0
                    )
                    db.add(subject)
                    print(f"✅ Created subject: {subject_data['name']} for {section.name}")
        
        db.commit()
        
        # Create sample grades for all students
        students = db.query(Student).all()
        for student in students:
            subjects = db.query(Subject).filter(Subject.section_id == student.section_id).all()
            
            for subject in subjects:
                # Check if grade already exists
                existing_grade = db.query(Grade).filter(
                    Grade.student_id == student.id,
                    Grade.subject_id == subject.id
                ).first()
                
                if not existing_grade:
                    # Generate random marks (60-100 for variety)
                    marks = random.randint(60, 100)
                    grade = Grade(
                        student_id=student.id,
                        subject_id=subject.id,
                        marks_obtained=marks,
                        total_marks=100.0,
                        assessment_type="Final Exam",
                        assessment_date=datetime.now()
                    )
                    
                    # Calculate percentage and grade
                    grade.calculate_percentage()
                    grade.calculate_grade_letter()
                    grade.is_passed = grade.percentage >= subject.passing_grade
                    
                    db.add(grade)
            
            print(f"✅ Created grades for student: {student.email}")
        
        db.commit()
        
        print(f"\n🎉 Successfully created {created_count} student accounts!")
        print("\n📋 Student Account Summary:")
        print("=" * 60)
        
        sections = db.query(Section).all()
        for section in sections:
            print(f"\n{section.name}:")
            section_students = db.query(Student).filter(Student.section_id == section.id).order_by(Student.roll_number).all()
            for student in section_students:
                print(f"  • {student.email} - {student.full_name} (Roll {student.roll_number})")
        
        print(f"\n🔑 Login credentials:")
        print("Username: Any of the emails above")
        print("Password: password123")
        
    except Exception as e:
        print(f"❌ Error creating student accounts: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_static_student_accounts()