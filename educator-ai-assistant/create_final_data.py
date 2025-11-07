#!/usr/bin/env python3
"""
FINAL FIX: Properly create 120 students with 30 per section for Shaaf
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator
import random

def create_proper_data():
    db = next(get_db())
    
    print("=== FINAL DATABASE FIX ===")
    
    # Get Shaaf
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    print(f"Shaaf ID: {shaaf.id}")
    
    # Delete ALL existing students and grades to start fresh
    print("🗑️ Clearing existing data...")
    db.query(Grade).delete()
    db.query(Student).delete()
    db.query(Subject).delete()
    db.query(Section).filter(Section.educator_id == shaaf.id).delete()
    db.commit()
    
    # Create 4 new sections for Shaaf
    print("📚 Creating 4 new sections...")
    sections_data = [
        ("Computer Science A", "CS-A"),
        ("Computer Science B", "CS-B"), 
        ("Mathematics Advanced", "MATH-ADV"),
        ("Physics Honors", "PHY-HON")
    ]
    
    created_sections = []
    for section_name, section_code in sections_data:
        section = Section(
            name=section_name,
            educator_id=shaaf.id,
            academic_year="2024-2025",
            semester="Fall"
        )
        db.add(section)
        db.flush()  # Get the ID
        created_sections.append(section)
        print(f"  ✅ Created section {section.id}: {section_name}")
    
    # Create subjects for each section
    print("📖 Creating subjects...")
    subjects_by_section = {
        "Computer Science A": [
            ("CS101", "Programming Fundamentals", 3, 60.0),
            ("CS102", "Data Structures", 4, 60.0),
            ("CS103", "Web Development", 3, 65.0)
        ],
        "Computer Science B": [
            ("CS201", "Advanced Programming", 4, 65.0),
            ("CS202", "Database Systems", 3, 60.0),
            ("CS203", "Software Engineering", 4, 70.0)
        ],
        "Mathematics Advanced": [
            ("MATH301", "Calculus III", 4, 65.0),
            ("MATH302", "Linear Algebra", 3, 60.0),
            ("MATH303", "Statistics", 3, 60.0)
        ],
        "Physics Honors": [
            ("PHY401", "Quantum Mechanics", 4, 70.0),
            ("PHY402", "Thermodynamics", 3, 65.0),
            ("PHY403", "Electromagnetism", 4, 65.0)
        ]
    }
    
    section_subjects = {}
    for section in created_sections:
        subjects_data = subjects_by_section[section.name]
        section_subjects[section.id] = []
        
        for code, name, credits, passing_grade in subjects_data:
            subject = Subject(
                code=code,
                name=name,
                section_id=section.id,
                credits=credits,
                passing_grade=passing_grade
            )
            db.add(subject)
            db.flush()
            section_subjects[section.id].append(subject)
            print(f"    Added subject: {name} to {section.name}")
    
    db.commit()
    
    # Create 30 students per section (120 total)
    print("👥 Creating 120 students (30 per section)...")
    
    # Student names for variety
    first_names = [
        "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah",
        "Ian", "Julia", "Kevin", "Lisa", "Michael", "Nina", "Oscar", "Paula",
        "Quinn", "Rachel", "Samuel", "Tina", "Ulrich", "Victoria", "William", "Xara",
        "Yuki", "Zoe", "Aaron", "Bella", "Carlos", "Delia"
    ]
    
    last_names = [
        "Anderson", "Brown", "Clark", "Davis", "Evans", "Fisher", "Garcia", "Harris",
        "Jackson", "Johnson", "King", "Lee", "Miller", "Nelson", "Parker", "Quinn",
        "Roberts", "Smith", "Taylor", "Wilson", "Adams", "Baker", "Cooper", "Edwards",
        "Foster", "Green", "Hall", "Young", "White", "Moore"
    ]
    
    student_counter = 1
    
    for section in created_sections:
        print(f"\n📝 Creating students for {section.name}...")
        
        # Get section prefix
        if "Computer Science A" in section.name:
            prefix = "CSA"
        elif "Computer Science B" in section.name:
            prefix = "CSB"
        elif "Mathematics" in section.name:
            prefix = "MAT"
        else:
            prefix = "PHY"
        
        # Create 30 students
        for i in range(30):
            first_name = first_names[i]
            last_name = last_names[i]
            
            student = Student(
                student_id=f"{prefix}{i+1:03d}",  # CSA001, CSA002, etc.
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}.{prefix.lower()}{i+1:03d}@student.edu",
                password_hash="$2b$12$dummy_hash",
                roll_number=i + 1,
                section_id=section.id,
                phone=f"555-{random.randint(1000,9999)}",
                guardian_email=f"{first_name.lower()}.{last_name.lower()}.parent@email.com",
                is_active=True
            )
            
            db.add(student)
            db.flush()  # Get the student ID
            
            # Create grades for each subject in this section
            subjects = section_subjects[section.id]
            
            for subject in subjects:
                # Create 2-3 grade records per subject per student
                num_assessments = random.randint(2, 3)
                
                for assessment_num in range(num_assessments):
                    # Realistic grade distribution
                    rand = random.random()
                    if rand < 0.15:  # 15% excellent students
                        marks = random.uniform(85, 100)
                    elif rand < 0.70:  # 55% good to average students  
                        marks = random.uniform(60, 85)
                    else:  # 30% struggling students
                        marks = random.uniform(40, 60)
                    
                    percentage = marks
                    
                    # Calculate grade letter
                    if percentage >= 95:
                        grade_letter = "A+"
                    elif percentage >= 90:
                        grade_letter = "A"
                    elif percentage >= 85:
                        grade_letter = "B+"
                    elif percentage >= 80:
                        grade_letter = "B"
                    elif percentage >= 75:
                        grade_letter = "C+"
                    elif percentage >= 70:
                        grade_letter = "C"
                    elif percentage >= 65:
                        grade_letter = "D+"
                    elif percentage >= 60:
                        grade_letter = "D"
                    else:
                        grade_letter = "F"
                    
                    is_passed = percentage >= subject.passing_grade
                    
                    assessment_types = ["Quiz", "Assignment", "Midterm", "Final Exam"]
                    
                    grade = Grade(
                        student_id=student.id,
                        subject_id=subject.id,
                        marks_obtained=round(marks, 1),
                        total_marks=100.0,
                        percentage=round(percentage, 1),
                        grade_letter=grade_letter,
                        is_passed=is_passed,
                        assessment_type=random.choice(assessment_types)
                    )
                    
                    db.add(grade)
            
            student_counter += 1
            
            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/30 students...")
    
    # Commit all changes
    db.commit()
    print("\n✅ COMMITTING ALL DATA TO DATABASE...")
    
    # Final verification
    print("\n=== FINAL VERIFICATION ===")
    final_sections = db.query(Section).filter(Section.educator_id == shaaf.id).all()
    total_students = 0
    total_grades = 0
    
    for section in final_sections:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        grade_count = db.query(Grade).join(Student).filter(Student.section_id == section.id).count()
        total_students += student_count
        total_grades += grade_count
        print(f"  ✅ {section.name}: {student_count} students, {grade_count} grades")
    
    print(f"\n🎯 FINAL TOTALS:")
    print(f"  📊 Total Students: {total_students}")
    print(f"  📈 Total Grades: {total_grades}")
    print(f"  📚 Total Sections: {len(final_sections)}")
    
    if total_students == 120:
        print("\n🎉 SUCCESS! 120 students created successfully!")
    else:
        print(f"\n❌ ERROR: Expected 120 students, got {total_students}")
    
    db.close()

if __name__ == "__main__":
    create_proper_data()