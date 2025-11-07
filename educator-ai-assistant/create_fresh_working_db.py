#!/usr/bin/env python3
"""Create a working database with proper performance data for the frontend"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
import random

# Import models
from app.models.educator import Educator
from app.models.student import Student, Section, Subject, Grade
from app.models.performance import Exam, Attendance
from app.core.database import Base

def create_working_database():
    """Create a completely fresh working database"""
    
    print("🚀 Creating Fresh Working Database")
    print("="*40)
    
    # Create database engine
    engine = create_engine("sqlite:///educator_ai.db", echo=False)
    
    # Drop and recreate all tables
    print("🗑️ Dropping existing tables...")
    Base.metadata.drop_all(engine)
    
    print("🏗️ Creating fresh tables...")
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. Create the main educator (Ananya Rao)
        print("👩‍🏫 Creating educator...")
        educator = Educator(
            email="ananya@email.com",
            first_name="Ananya", 
            last_name="Rao",
            employee_id="EDU001",
            department="Mathematics",
            title="Senior Teacher",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LQ1Gau.Z5rElYkQjjb9wHXlFbkgGmQxnQl7QG",  # password123
            is_active=True,
            is_admin=True
        )
        db.add(educator)
        db.commit()
        db.refresh(educator)
        print(f"✅ Created educator: {educator.first_name} {educator.last_name} (ID: {educator.id})")
        
        # 2. Create section first (needed for subjects)
        print("🏫 Creating section...")
        section = Section(
            name="Class 10-A",
            educator_id=educator.id,
            academic_year="2024-25",
            semester="Fall"
        )
        db.add(section)
        db.commit()
        db.refresh(section)
        print(f"✅ Created section: {section.name} (ID: {section.id})")
        
        # 3. Create subjects
        print("📚 Creating subjects...")
        subjects = [
            Subject(name="Mathematics", code="MATH101", section_id=section.id, credits=5),
            Subject(name="Science", code="SCI101", section_id=section.id, credits=4),
            Subject(name="English", code="ENG101", section_id=section.id, credits=3)
        ]
        db.add_all(subjects)
        db.commit()
        print(f"✅ Created {len(subjects)} subjects")
        
        # 4. Create students
        print("👥 Creating students...")
        student_names = [
            ("Arjun", "Sharma"),
            ("Priya", "Patel"),
            ("Rohit", "Kumar"),
            ("Sneha", "Singh")
        ]
        
        students = []
        for i, (first_name, last_name) in enumerate(student_names, 1):
            student = Student(
                first_name=first_name,
                last_name=last_name,
                student_id=f"STU{i:03d}",
                email=f"{first_name.lower()}.{last_name.lower()}@student.edu",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LQ1Gau.Z5rElYkQjjb9wHXlFbkgGmQxnQl7QG",  # password123
                roll_number=i,
                section_id=section.id,
                phone="9876543210",
                date_of_birth=datetime(2008, random.randint(1, 12), random.randint(1, 28)),
                address="Student Address",
                guardian_email=f"{first_name.lower()}.parent@email.com",
                is_active=True
            )
            students.append(student)
            db.add(student)
            
        db.commit()
        
        # Refresh students to get their IDs
        for student in students:
            db.refresh(student)
            
        print(f"✅ Created {len(students)} students")
        
        # 5. Create exams
        print("📝 Creating exams...")
        exams = []
        for i, subject in enumerate(subjects, 1):
            exam = Exam(
                name=f"{subject.name} Mid-term",
                code=f"MT{subject.code}",
                exam_date=date.today() - timedelta(days=30-i*5),
                term="Fall 2024",
                academic_year="2024-2025",
                total_marks=100.0,
                passing_marks=60.0,
                duration_minutes=180
            )
            exams.append(exam)
            db.add(exam)
            
        db.commit()
        
        for exam in exams:
            db.refresh(exam)
            
        print(f"✅ Created {len(exams)} exams")
        
        # 6. Create grades
        print("📊 Creating grades...")
        grade_count = 0
        
        for student in students:
            for i, (exam, subject) in enumerate(zip(exams, subjects)):
                # Generate realistic grades (60-95%)
                marks_obtained = random.uniform(60.0, 95.0)
                percentage = (marks_obtained / exam.total_marks) * 100
                
                grade = Grade(
                    student_id=student.id,
                    subject_id=subject.id,
                    exam_id=exam.id,
                    marks_obtained=marks_obtained,
                    total_marks=exam.total_marks,
                    percentage=percentage,
                    grade_letter="A" if percentage >= 90 else "B" if percentage >= 75 else "C",
                    is_passed=percentage >= 60,
                    assessment_type="midterm",
                    assessment_date=exam.exam_date
                )
                db.add(grade)
                grade_count += 1
                
        db.commit()
        print(f"✅ Created {grade_count} grade records")
        
        # 7. Create attendance records
        print("📅 Creating attendance...")
        attendance_count = 0
        
        # Create 30 days of attendance for each student and subject
        for days_back in range(30):
            attendance_date = date.today() - timedelta(days=days_back)
            
            # Skip weekends
            if attendance_date.weekday() >= 5:
                continue
                
            for student in students:
                for subject in subjects:
                    # 90% attendance rate
                    is_present = random.random() < 0.9
                    
                    attendance = Attendance(
                        student_id=student.id,
                        subject_id=subject.id,
                        date=attendance_date,
                        present=is_present,
                        period=random.randint(1, 6),
                        remarks="Present" if is_present else "Absent"
                    )
                    db.add(attendance)
                    attendance_count += 1
                    
        db.commit()
        print(f"✅ Created {attendance_count} attendance records")
        
        # 8. Verify the data
        print("\n📋 Verification:")
        total_students = db.query(Student).count()
        total_grades = db.query(Grade).count() 
        total_exams = db.query(Exam).count()
        total_attendance = db.query(Attendance).count()
        
        print(f"   • Students: {total_students}")
        print(f"   • Grades: {total_grades}")
        print(f"   • Exams: {total_exams}")
        print(f"   • Attendance: {total_attendance}")
        
        # Test login credentials
        print(f"\n🔑 Login Credentials:")
        print(f"   • Email: ananya@email.com")
        print(f"   • Password: password123")
        print(f"   • Educator ID: {educator.id}")
        
        db.close()
        
        print("\n🎉 Database created successfully!")
        print("🚀 Ready to test frontend with authentication!")
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        db.rollback()
        db.close()
        return False
        
    return True

if __name__ == "__main__":
    create_working_database()