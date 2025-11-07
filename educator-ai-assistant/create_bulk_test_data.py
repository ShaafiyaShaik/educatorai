"""
Create proper student accounts with grades for bulk communication testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.student import Student, Grade, Subject, Section
from app.models.educator import Educator
import random
from datetime import datetime

def create_test_data():
    """Create test data for bulk communication"""
    db = SessionLocal()
    
    try:
        # Check if we have educators first
        educators = db.query(Educator).all()
        if not educators:
            print("No educators found. Please create educators first.")
            return
        
        # Create sections if they don't exist
        section_names = ["Section A", "Section B", "Section C"]
        sections = {}
        
        for section_name in section_names:
            section = db.query(Section).filter(Section.name == section_name).first()
            if not section:
                section = Section(
                    name=section_name,
                    description=f"Students in {section_name}",
                    capacity=30,
                    academic_year="2025-2026"
                )
                db.add(section)
                db.commit()
                db.refresh(section)
            sections[section_name] = section
        
        # Create subjects if they don't exist  
        subject_data = [
            {"name": "Mathematics", "code": "MATH101"},
            {"name": "Science", "code": "SCI101"}, 
            {"name": "English", "code": "ENG101"},
            {"name": "Programming Fundamentals", "code": "CS101"},
            {"name": "Data Structures", "code": "CS201"},
            {"name": "Web Development", "code": "CS301"}
        ]
        subjects = {}
        
        for subject_info in subject_data:
            subject = db.query(Subject).filter(Subject.name == subject_info["name"]).first()
            if not subject:
                # Assign to first section for now
                section_a = sections["Section A"]
                subject = Subject(
                    name=subject_info["name"],
                    code=subject_info["code"],
                    section_id=section_a.id,
                    credits=3,
                    passing_grade=50.0
                )
                db.add(subject)
                db.commit()
                db.refresh(subject)
            subjects[subject_info["name"]] = subject
        
        # Sample student data
        sample_students = [
            {
                "first_name": "Ahmed", "last_name": "Al-Rashid", "email": "ahmed.rashid@student.edu",
                "section": "Section A", "roll_number": 1, "student_id": "SA001",
                "grades": {"Mathematics": 85, "Science": 78, "English": 82}
            },
            {
                "first_name": "Fatima", "last_name": "Hassan", "email": "fatima.hassan@student.edu", 
                "section": "Section A", "roll_number": 2, "student_id": "SA002",
                "grades": {"Mathematics": 92, "Science": 88, "English": 90}
            },
            {
                "first_name": "Omar", "last_name": "Khan", "email": "omar.khan@student.edu",
                "section": "Section A", "roll_number": 3, "student_id": "SA003", 
                "grades": {"Mathematics": 76, "Science": 82, "English": 79}
            },
            {
                "first_name": "Aisha", "last_name": "Malik", "email": "aisha.malik@student.edu",
                "section": "Section B", "roll_number": 1, "student_id": "SB001",
                "grades": {"Mathematics": 88, "Science": 85, "English": 91}
            },
            {
                "first_name": "Hassan", "last_name": "Ali", "email": "hassan.ali@student.edu",
                "section": "Section B", "roll_number": 2, "student_id": "SB002", 
                "grades": {"Mathematics": 72, "Science": 75, "English": 68}
            },
            {
                "first_name": "Zara", "last_name": "Ahmed", "email": "zara.ahmed@student.edu",
                "section": "Section B", "roll_number": 3, "student_id": "SB003",
                "grades": {"Mathematics": 95, "Science": 92, "English": 94}
            },
            {
                "first_name": "Khalid", "last_name": "Sheikh", "email": "khalid.sheikh@student.edu",
                "section": "Section C", "roll_number": 1, "student_id": "SC001",
                "grades": {"Mathematics": 65, "Science": 70, "English": 73}
            },
            {
                "first_name": "Mariam", "last_name": "Ibrahim", "email": "mariam.ibrahim@student.edu",
                "section": "Section C", "roll_number": 2, "student_id": "SC002",
                "grades": {"Mathematics": 89, "Science": 86, "English": 87}
            },
            {
                "first_name": "Yusuf", "last_name": "Mohammad", "email": "yusuf.mohammad@student.edu",
                "section": "Section C", "roll_number": 3, "student_id": "SC003",
                "grades": {"Mathematics": 58, "Science": 62, "English": 55}
            },
            {
                "first_name": "Noor", "last_name": "Saleh", "email": "noor.saleh@student.edu",
                "section": "Section A", "roll_number": 4, "student_id": "SA004", 
                "grades": {"Mathematics": 91, "Science": 89, "English": 93}
            }
        ]
        
        created_count = 0
        for student_data in sample_students:
            # Check if student already exists
            existing_student = db.query(Student).filter(Student.email == student_data["email"]).first()
            if existing_student:
                print(f"Student {student_data['email']} already exists, skipping...")
                continue
            
            # Create student
            student = Student(
                student_id=student_data["student_id"],
                first_name=student_data["first_name"],
                last_name=student_data["last_name"],
                email=student_data["email"],
                password_hash="hashed_password_placeholder",  # You'd want to hash this properly
                roll_number=student_data["roll_number"],
                section_id=sections[student_data["section"]].id,
                is_active=True
            )
            
            db.add(student)
            db.commit()
            db.refresh(student)
            created_count += 1
            
            # Create grades for each subject
            for subject_name, marks in student_data["grades"].items():
                if subject_name in subjects:
                    grade = Grade(
                        student_id=student.id,
                        subject_id=subjects[subject_name].id,
                        marks_obtained=marks,
                        total_marks=100.0,
                        assessment_type="Final Exam",
                        assessment_date=datetime.now()
                    )
                    
                    # Calculate percentage and grade
                    grade.percentage = (marks / 100.0) * 100
                    
                    # Calculate grade letter
                    if grade.percentage >= 90:
                        grade.grade_letter = "A+"
                    elif grade.percentage >= 80:
                        grade.grade_letter = "A"
                    elif grade.percentage >= 70:
                        grade.grade_letter = "B"
                    elif grade.percentage >= 60:
                        grade.grade_letter = "C"
                    elif grade.percentage >= 50:
                        grade.grade_letter = "D"
                    else:
                        grade.grade_letter = "F"
                    
                    grade.is_passed = grade.percentage >= subjects[subject_name].passing_grade
                    
                    db.add(grade)
            
            print(f"✅ Created student: {student.first_name} {student.last_name} ({student.email})")
        
        db.commit()
        
        print(f"\n🎉 Successfully created {created_count} new students!")
        
        # Print summary
        print("\n📋 Student Summary by Section:")
        print("=" * 60)
        
        for section_name in section_names:
            section = sections[section_name]
            student_count = db.query(Student).filter(Student.section_id == section.id).count()
            print(f"{section_name}: {student_count} students")
        
        print("\n📚 Available Subjects:")
        for subject_name in subjects:
            subject = subjects[subject_name]
            grade_count = db.query(Grade).filter(Grade.subject_id == subject.id).count()
            print(f"- {subject_name}: {grade_count} grades recorded")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🏗️ Creating test data for bulk communication...")
    create_test_data()
    print("✅ Done!")