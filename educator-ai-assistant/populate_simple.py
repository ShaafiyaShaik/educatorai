#!/usr/bin/env python3
"""
Simple Database Population Script for Teacher Portal
"""

import json
import sys
import os
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        # Initialize database first
        print("🔧 Initializing database...")
        from app.core.database import init_db, get_db
        init_db()
        
        # Import models after database initialization
        from app.models.educator import Educator
        from app.models.student import Section, Student, Subject, Grade
        from app.core.auth import get_password_hash
        
        print("✅ Database initialized successfully")
        
        # Load mock data
        print("📁 Loading mock data...")
        with open("mock_student_data.json", "r", encoding="utf-8") as f:
            mock_data = json.load(f)
        
        db = next(get_db())
        
        # Create teachers
        teacher_mapping = {}
        teachers = [
            ("teacher1@example.com", "John", "Smith", "Mathematics"),
            ("teacher2@example.com", "Sarah", "Johnson", "Science"), 
            ("shaaf@gmail.com", "Shaafiya", "Ahmed", "Computer Science"),
            ("demo.teacher@edu.com", "Demo", "Teacher", "English")
        ]
        
        print("👨‍🏫 Creating teachers...")
        for email, first_name, last_name, department in teachers:
            existing = db.query(Educator).filter(Educator.email == email).first()
            if not existing:
                teacher = Educator(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    department=department,
                    hashed_password=get_password_hash("password123"),
                    is_active=True
                )
                db.add(teacher)
                db.commit()
                db.refresh(teacher)
                teacher_mapping[email] = teacher
                print(f"  ✅ Created: {email}")
            else:
                teacher_mapping[email] = existing
                print(f"  📝 Exists: {email}")
        
        # Process mock data
        print("📚 Processing sections and students...")
        total_students = 0
        total_sections = 0
        
        for teacher_email, teacher_data in mock_data.items():
            if teacher_email not in teacher_mapping:
                continue
                
            teacher = teacher_mapping[teacher_email]
            print(f"\n  Processing {teacher_email}...")
            
            for section_name, section_data in teacher_data["sections"].items():
                # Create section
                existing_section = db.query(Section).filter(
                    Section.name == section_name,
                    Section.educator_id == teacher.id
                ).first()
                
                if not existing_section:
                    section = Section(
                        name=section_name,
                        educator_id=teacher.id
                    )
                    db.add(section)
                    db.commit()
                    db.refresh(section)
                    total_sections += 1
                else:
                    section = existing_section
                
                # Create subjects
                subjects = {}
                for subject_name in ["Math", "Science", "English"]:
                    existing_subject = db.query(Subject).filter(
                        Subject.name == subject_name,
                        Subject.section_id == section.id
                    ).first()
                    
                    if not existing_subject:
                        subject = Subject(
                            name=subject_name,
                            code=f"{subject_name.upper()[:4]}101",
                            section_id=section.id
                        )
                        db.add(subject)
                        db.commit()
                        db.refresh(subject)
                        subjects[subject_name] = subject
                    else:
                        subjects[subject_name] = existing_subject
                
                # Create students and grades
                students_data = section_data["students"]
                for student_data in students_data:
                    existing_student = db.query(Student).filter(
                        Student.student_id == student_data["roll_no"]
                    ).first()
                    
                    if not existing_student:
                        name_parts = student_data["name"].split(" ", 1)
                        student = Student(
                            student_id=student_data["roll_no"],
                            first_name=name_parts[0],
                            last_name=name_parts[1] if len(name_parts) > 1 else "",
                            email=student_data["email"],
                            section_id=section.id
                        )
                        db.add(student)
                        db.commit()
                        db.refresh(student)
                        total_students += 1
                        
                        # Create grades
                        for subject_name, marks in student_data["marks"].items():
                            subject = subjects[subject_name]
                            grade = Grade(
                                student_id=student.id,
                                subject_id=subject.id,
                                marks_obtained=marks,
                                total_marks=100.0,
                                percentage=marks,
                                is_passed=marks >= 40
                            )
                            db.add(grade)
                        
                        db.commit()
                
                print(f"    ✅ {section_name}: {len(students_data)} students")
        
        print(f"\n✅ Population completed!")
        print(f"📊 Created {total_sections} sections and {total_students} students")
        print(f"🔑 Teacher credentials: password123")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()