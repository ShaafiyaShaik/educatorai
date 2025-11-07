#!/usr/bin/env python3
"""
Create a comprehensive dataset with 30 students per section
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator
import random
from faker import Faker

fake = Faker()

def create_comprehensive_student_data():
    db = next(get_db())
    
    print("=== Creating Comprehensive Student Dataset ===")
    
    # Clear existing data
    db.query(Grade).delete()
    db.query(Student).delete()
    db.commit()
    
    # Get all sections
    sections = db.query(Section).all()
    print(f"Found {len(sections)} sections")
    
    student_id_counter = 1
    
    for section in sections:
        print(f"\nCreating students for section: {section.name}")
        
        # Get subjects for this section
        subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
        print(f"  Subjects: {[s.name for s in subjects]}")
        
        # Create 30 students per section
        for i in range(30):
            # Generate student data
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Create section-specific student ID
            if "Computer Science" in section.name:
                student_id = f"CS{student_id_counter:03d}"
            elif "Mathematics" in section.name:
                student_id = f"MA{student_id_counter:03d}"
            elif "Physics" in section.name:
                student_id = f"PH{student_id_counter:03d}"
            else:
                student_id = f"ST{student_id_counter:03d}"
            
            email = f"{first_name.lower()}.{last_name.lower()}@student.edu"
            
            student = Student(
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash="$2b$12$dummy_hash",  # Placeholder
                roll_number=i + 1,
                section_id=section.id,
                phone=fake.phone_number()[:15],
                guardian_email=f"{first_name.lower()}.parent@email.com",
                is_active=True
            )
            
            db.add(student)
            db.flush()  # Get the student ID
            
            # Create realistic grades for each subject
            for subject in subjects:
                # Create 2-3 assessments per subject
                num_assessments = random.randint(2, 3)
                
                for assessment in range(num_assessments):
                    # Generate realistic grade distribution
                    # 70% students perform average to good (60-85%)
                    # 20% students perform excellent (85-100%)
                    # 10% students struggle (40-60%)
                    
                    rand = random.random()
                    if rand < 0.1:  # 10% struggling students
                        marks = random.uniform(40, 60)
                    elif rand < 0.8:  # 70% average to good students
                        marks = random.uniform(60, 85)
                    else:  # 20% excellent students
                        marks = random.uniform(85, 100)
                    
                    total_marks = 100.0
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
                    
                    # Determine if passed
                    passing_grade = subject.passing_grade if subject.passing_grade else 60.0
                    is_passed = percentage >= passing_grade
                    
                    # Assessment types
                    assessment_types = ["Quiz", "Midterm", "Final Exam", "Assignment", "Project"]
                    assessment_type = random.choice(assessment_types)
                    
                    grade = Grade(
                        student_id=student.id,
                        subject_id=subject.id,
                        marks_obtained=round(marks, 1),
                        total_marks=total_marks,
                        percentage=round(percentage, 1),
                        grade_letter=grade_letter,
                        is_passed=is_passed,
                        assessment_type=assessment_type,
                        remarks=f"{assessment_type} assessment"
                    )
                    
                    db.add(grade)
            
            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/30 students...")
            
            student_id_counter += 1
    
    # Commit all changes
    db.commit()
    
    # Print summary
    total_students = db.query(Student).count()
    total_grades = db.query(Grade).count()
    
    print(f"\n=== Dataset Summary ===")
    print(f"Total students created: {total_students}")
    print(f"Total grades created: {total_grades}")
    print(f"Average grades per student: {total_grades / total_students:.1f}")
    
    # Show performance by section
    for section in sections:
        students_in_section = db.query(Student).filter(Student.section_id == section.id).count()
        grades_in_section = db.query(Grade).join(Student).filter(Student.section_id == section.id).count()
        
        # Calculate section average
        grades = db.query(Grade).join(Student).filter(Student.section_id == section.id).all()
        if grades:
            avg_percentage = sum(g.percentage for g in grades) / len(grades)
            passed_grades = sum(1 for g in grades if g.is_passed)
            pass_rate = (passed_grades / len(grades)) * 100
            
            print(f"\n{section.name}:")
            print(f"  Students: {students_in_section}")
            print(f"  Grades: {grades_in_section}")
            print(f"  Average: {avg_percentage:.1f}%")
            print(f"  Pass Rate: {pass_rate:.1f}%")
    
    db.close()

if __name__ == "__main__":
    create_comprehensive_student_data()