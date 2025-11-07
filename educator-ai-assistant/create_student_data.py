#!/usr/bin/env python3

"""
Script to create comprehensive mock student data with sections, subjects, and grades
"""

import random
import sqlite3
from datetime import datetime, timedelta
from app.core.database import engine, Base
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Import all models to ensure they're registered
import app.models.educator
import app.models.student

# Mock data for generating realistic student names
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
    "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle",
    "Kenneth", "Laura", "Kevin", "Sarah", "Brian", "Kimberly", "George", "Deborah",
    "Edward", "Dorothy", "Ronald", "Lisa", "Timothy", "Nancy", "Jason", "Karen",
    "Jeffrey", "Betty", "Ryan", "Helen", "Jacob", "Sandra", "Gary", "Donna",
    "Nicholas", "Carol", "Eric", "Ruth", "Jonathan", "Sharon", "Stephen", "Michelle",
    "Larry", "Laura", "Justin", "Sarah", "Scott", "Kimberly", "Brandon", "Deborah",
    "Benjamin", "Dorothy", "Samuel", "Amy", "Gregory", "Angela", "Alexander", "Helen",
    "Patrick", "Brenda", "Jack", "Emma", "Dennis", "Olivia", "Jerry", "Cynthia"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson"
]

def create_mock_student_data():
    """Create comprehensive mock student data"""
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get or create the educator (assuming shaaf123@gmail.com exists)
        educator = db.query(Educator).filter(Educator.email == "shaaf123@gmail.com").first()
        if not educator:
            print("Creating educator first...")
            from app.core.auth import get_password_hash
            educator = Educator(
                email="shaaf123@gmail.com",
                first_name="Shaaf",
                last_name="Teacher",
                employee_id="EMP002",
                department="Computer Science",
                title="Professor",
                hashed_password=get_password_hash("password123")
            )
            db.add(educator)
            db.commit()
            db.refresh(educator)
        
        print(f"Using educator: {educator.full_name} (ID: {educator.id})")
        
        # Create 3 sections
        sections_data = [
            {"name": "Section A - Morning", "academic_year": "2024-2025", "semester": "Fall"},
            {"name": "Section B - Afternoon", "academic_year": "2024-2025", "semester": "Fall"},
            {"name": "Section C - Evening", "academic_year": "2024-2025", "semester": "Fall"}
        ]
        
        sections = []
        for section_data in sections_data:
            # Check if section already exists
            existing_section = db.query(Section).filter(
                Section.name == section_data["name"],
                Section.educator_id == educator.id
            ).first()
            
            if not existing_section:
                section = Section(
                    name=section_data["name"],
                    educator_id=educator.id,
                    academic_year=section_data["academic_year"],
                    semester=section_data["semester"]
                )
                db.add(section)
                sections.append(section)
                print(f"Created section: {section_data['name']}")
            else:
                sections.append(existing_section)
                print(f"Using existing section: {section_data['name']}")
        
        db.commit()
        
        # Create 3 subjects for each section
        subjects_data = [
            {"name": "Mathematics", "code": "MATH101", "credits": 4, "passing_grade": 60.0},
            {"name": "Physics", "code": "PHYS201", "credits": 3, "passing_grade": 55.0},
            {"name": "Computer Science", "code": "CS301", "credits": 4, "passing_grade": 65.0}
        ]
        
        all_subjects = []
        for section in sections:
            section_subjects = []
            for subject_data in subjects_data:
                # Check if subject already exists
                existing_subject = db.query(Subject).filter(
                    Subject.code == subject_data["code"],
                    Subject.section_id == section.id
                ).first()
                
                if not existing_subject:
                    subject = Subject(
                        name=subject_data["name"],
                        code=subject_data["code"],
                        section_id=section.id,
                        credits=subject_data["credits"],
                        passing_grade=subject_data["passing_grade"]
                    )
                    db.add(subject)
                    section_subjects.append(subject)
                    print(f"Created subject: {subject_data['code']} for {section.name}")
                else:
                    section_subjects.append(existing_subject)
                    print(f"Using existing subject: {subject_data['code']} for {section.name}")
            
            all_subjects.extend(section_subjects)
        
        db.commit()
        
        # Create 50 students per section (150 total)
        all_students = []
        student_counter = 1
        
        for section in sections:
            section_students = []
            for i in range(50):
                # Generate unique student data
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)
                student_id = f"STU{student_counter:03d}"
                email = f"{first_name.lower()}.{last_name.lower()}{student_counter}@student.university.edu"
                
                # Check if student already exists
                existing_student = db.query(Student).filter(Student.student_id == student_id).first()
                
                if not existing_student:
                    # Generate random birth date (18-22 years old)
                    birth_year = random.randint(2002, 2006)
                    birth_month = random.randint(1, 12)
                    birth_day = random.randint(1, 28)
                    date_of_birth = datetime(birth_year, birth_month, birth_day)
                    
                    student = Student(
                        student_id=student_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        section_id=section.id,
                        phone=f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        date_of_birth=date_of_birth,
                        guardian_email=f"parent.{last_name.lower()}@gmail.com"
                    )
                    db.add(student)
                    section_students.append(student)
                    student_counter += 1
                else:
                    section_students.append(existing_student)
                    student_counter += 1
            
            all_students.extend(section_students)
            print(f"Created {len(section_students)} students for {section.name}")
        
        db.commit()
        
        # Create grades for each student in each subject
        print("Generating grades...")
        grades_created = 0
        
        for section in sections:
            # Get students and subjects for this section
            section_students = [s for s in all_students if s.section_id == section.id]
            section_subjects = [s for s in all_subjects if s.section_id == section.id]
            
            for student in section_students:
                for subject in section_subjects:
                    # Check if grade already exists
                    existing_grade = db.query(Grade).filter(
                        Grade.student_id == student.id,
                        Grade.subject_id == subject.id
                    ).first()
                    
                    if not existing_grade:
                        # Generate realistic grade distribution
                        # 70% students pass, 30% fail
                        if random.random() < 0.7:  # Pass
                            marks_obtained = random.uniform(subject.passing_grade, 100)
                        else:  # Fail
                            marks_obtained = random.uniform(30, subject.passing_grade - 1)
                        
                        grade = Grade(
                            student_id=student.id,
                            subject_id=subject.id,
                            marks_obtained=round(marks_obtained, 1),
                            total_marks=100.0,
                            assessment_type="Final Exam",
                            assessment_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                            remarks="Regular assessment" if marks_obtained >= subject.passing_grade else "Needs improvement"
                        )
                        
                        # Calculate derived fields
                        grade.calculate_percentage()
                        grade.calculate_grade_letter()
                        grade.is_passed = grade.marks_obtained >= subject.passing_grade
                        
                        db.add(grade)
                        grades_created += 1
        
        db.commit()
        print(f"Created {grades_created} grade records")
        
        # Generate summary statistics
        print("\n=== MOCK DATA SUMMARY ===")
        total_sections = db.query(Section).filter(Section.educator_id == educator.id).count()
        total_students = db.query(Student).join(Section).filter(Section.educator_id == educator.id).count()
        total_subjects = db.query(Subject).join(Section).filter(Section.educator_id == educator.id).count()
        total_grades = db.query(Grade).join(Student).join(Section).filter(Section.educator_id == educator.id).count()
        
        print(f"Educator: {educator.full_name}")
        print(f"Sections: {total_sections}")
        print(f"Students: {total_students}")
        print(f"Subjects: {total_subjects}")
        print(f"Grade Records: {total_grades}")
        
        # Show section-wise statistics
        for section in sections:
            section_student_count = len([s for s in all_students if s.section_id == section.id])
            section_subjects = [s for s in all_subjects if s.section_id == section.id]
            
            print(f"\n{section.name}:")
            print(f"  Students: {section_student_count}")
            print(f"  Subjects: {len(section_subjects)}")
            
            for subject in section_subjects:
                passed = db.query(Grade).filter(
                    Grade.subject_id == subject.id,
                    Grade.is_passed == True
                ).count()
                failed = db.query(Grade).filter(
                    Grade.subject_id == subject.id,
                    Grade.is_passed == False
                ).count()
                avg_marks = db.execute(text(
                    "SELECT AVG(marks_obtained) FROM grades WHERE subject_id = :subject_id"
                ), {"subject_id": subject.id}).fetchone()[0]
                
                print(f"    {subject.name} ({subject.code}): {passed} passed, {failed} failed, avg: {avg_marks:.1f}")
        
        print("\nMock data created successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_mock_student_data()