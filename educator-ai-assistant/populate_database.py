"""
Database Population Script for Teacher Portal
Loads mock student data into the SQLite database.
"""

import json
import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db, engine
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade

def load_mock_data(filename: str = "mock_student_data.json"):
    """Load mock data from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please run generate_mock_data.py first.")
        return None

def get_or_create_educator(db: Session, email: str) -> Educator:
    """Get existing educator or create a new one"""
    educator = db.query(Educator).filter(Educator.email == email).first()
    
    if not educator:
        # Create a new educator if not exists
        from app.core.auth import get_password_hash
        
        educator = Educator(
            email=email,
            first_name="Test",
            last_name="Teacher",
            hashed_password=get_password_hash("password123"),
            department="Computer Science",
            title="Professor",
            is_active=True
        )
        db.add(educator)
        db.commit()
        db.refresh(educator)
        print(f"Created new educator: {email}")
    
    return educator

def create_section(db: Session, educator_id: int, section_name: str) -> Section:
    """Create a new section"""
    section = Section(
        name=section_name,
        educator_id=educator_id,
        academic_year="2024-2025",
        semester="Fall"
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section

def create_subjects_for_section(db: Session, section_id: int) -> dict:
    """Create subjects for a section and return subject mapping"""
    subjects_data = [
        {"name": "Mathematics", "code": "MATH101"},
        {"name": "Science", "code": "SCI101"},
        {"name": "English", "code": "ENG101"}
    ]
    
    subject_mapping = {}
    
    for subject_data in subjects_data:
        subject = Subject(
            name=subject_data["name"],
            code=subject_data["code"],
            section_id=section_id,
            credits=3,
            passing_grade=40.0
        )
        db.add(subject)
        db.commit()
        db.refresh(subject)
        
        # Map the mock data subject names to database subjects
        if subject_data["name"] == "Mathematics":
            subject_mapping["Math"] = subject
        elif subject_data["name"] == "Science":
            subject_mapping["Science"] = subject
        elif subject_data["name"] == "English":
            subject_mapping["English"] = subject
    
    return subject_mapping

def create_student(db: Session, section_id: int, student_data: dict) -> Student:
    """Create a new student"""
    student = Student(
        student_id=student_data["roll_no"],
        first_name=student_data["name"].split()[0],
        last_name=" ".join(student_data["name"].split()[1:]) if len(student_data["name"].split()) > 1 else "",
        email=student_data["email"],
        section_id=section_id,
        is_active=True
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

def create_grades_for_student(db: Session, student_id: int, marks_data: dict, subject_mapping: dict):
    """Create grades for a student"""
    for subject_name, marks in marks_data.items():
        if subject_name in subject_mapping:
            subject = subject_mapping[subject_name]
            
            grade = Grade(
                student_id=student_id,
                subject_id=subject.id,
                marks_obtained=float(marks),
                total_marks=100.0,
                assessment_type="Final Exam",
                assessment_date=datetime.now()
            )
            
            # Calculate percentage and grade letter
            grade.calculate_percentage()
            grade.calculate_grade_letter()
            grade.is_passed = marks >= 40
            
            db.add(grade)
    
    db.commit()

def clear_existing_data(db: Session):
    """Clear existing student data (optional - for fresh start)"""
    print("Clearing existing student data...")
    
    # Delete in proper order to avoid foreign key constraints
    db.query(Grade).delete()
    db.query(Student).delete()
    db.query(Subject).delete()
    db.query(Section).delete()
    
    db.commit()
    print("Existing data cleared.")

def populate_database(mock_data: dict, clear_data: bool = False):
    """Populate database with mock data"""
    db = next(get_db())
    
    try:
        if clear_data:
            clear_existing_data(db)
        
        print("Starting database population...")
        
        total_students = 0
        total_sections = 0
        
        for teacher_email, teacher_data in mock_data.items():
            print(f"\nProcessing teacher: {teacher_email}")
            
            # Get or create educator
            educator = get_or_create_educator(db, teacher_email)
            
            # Process each section
            for section_name, section_data in teacher_data["sections"].items():
                print(f"  Creating {section_name}...")
                
                # Create section
                section = create_section(db, educator.id, section_name)
                total_sections += 1
                
                # Create subjects for this section
                subject_mapping = create_subjects_for_section(db, section.id)
                
                # Create students and their grades
                students_data = section_data["students"]
                for student_data in students_data:
                    # Create student
                    student = create_student(db, section.id, student_data)
                    
                    # Create grades for student
                    create_grades_for_student(db, student.id, student_data["marks"], subject_mapping)
                    
                    total_students += 1
                
                print(f"    Created {len(students_data)} students")
        
        print(f"\nDatabase population completed!")
        print(f"Total educators processed: {len(mock_data)}")
        print(f"Total sections created: {total_sections}")
        print(f"Total students created: {total_students}")
        print(f"Total subjects created: {total_sections * 3}")
        print(f"Total grades created: {total_students * 3}")
        
    except Exception as e:
        print(f"Error during database population: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_data(db: Session):
    """Verify the populated data"""
    educators_count = db.query(Educator).count()
    sections_count = db.query(Section).count()
    students_count = db.query(Student).count()
    subjects_count = db.query(Subject).count()
    grades_count = db.query(Grade).count()
    
    print(f"\nData Verification:")
    print(f"Educators: {educators_count}")
    print(f"Sections: {sections_count}")
    print(f"Students: {students_count}")
    print(f"Subjects: {subjects_count}")
    print(f"Grades: {grades_count}")
    
    # Show some sample data
    print(f"\nSample educator:")
    educator = db.query(Educator).first()
    if educator:
        print(f"  {educator.email} - {educator.full_name}")
        
        # Show their sections
        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        print(f"  Sections: {[s.name for s in sections]}")
        
        if sections:
            section = sections[0]
            students_count = db.query(Student).filter(Student.section_id == section.id).count()
            print(f"  {section.name} has {students_count} students")

if __name__ == "__main__":
    print("Teacher Portal Database Population Script")
    print("=" * 50)
    
    # Load mock data
    mock_data = load_mock_data()
    if not mock_data:
        sys.exit(1)
    
    # Ask user if they want to clear existing data
    response = input("\nDo you want to clear existing student data before populating? (y/N): ").strip().lower()
    clear_data = response in ['y', 'yes']
    
    if clear_data:
        confirm = input("Are you sure? This will delete all existing students, sections, subjects, and grades! (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)
    
    # Populate database
    try:
        populate_database(mock_data, clear_data)
        
        # Verify data
        db = next(get_db())
        verify_data(db)
        db.close()
        
        print("\n✅ Database population successful!")
        print("You can now test the teacher portal with realistic data.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)