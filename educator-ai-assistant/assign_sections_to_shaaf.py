#!/usr/bin/env python3
"""
Assign sections to Shaaf and create more realistic data structure
"""

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.student import Section, Student, Subject, Grade
from app.models.educator import Educator

def assign_sections_to_shaaf():
    db = next(get_db())
    
    print("=== Assigning Sections to Shaaf ===")
    
    # Get Shaaf
    shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
    if not shaaf:
        print("Shaaf not found!")
        return
    
    print(f"Found Shaaf: {shaaf.full_name} (ID: {shaaf.id})")
    
    # Get the sections that have students but no proper names
    sections = db.query(Section).all()
    
    # Update sections with better names and assign to Shaaf
    section_names = [
        "Computer Science A",
        "Computer Science B", 
        "Mathematics Advanced",
        "Physics Honors"
    ]
    
    for i, section in enumerate(sections[:4]):  # Update first 4 sections
        section.educator_id = shaaf.id
        section.name = section_names[i] if i < len(section_names) else f"Section {chr(65+i)}"
        section.academic_year = "2024-2025"
        section.semester = "Fall"
        
        print(f"Updated section {section.id}: {section.name}")
        
        # Update subjects for each section
        # Clear existing subjects
        db.query(Subject).filter(Subject.section_id == section.id).delete()
        
        # Add appropriate subjects based on section
        if "Computer Science" in section.name:
            subjects_data = [
                ("CS101", "Programming Fundamentals", 3, 60.0),
                ("CS102", "Data Structures", 4, 60.0),
                ("CS103", "Object-Oriented Programming", 3, 65.0)
            ]
        elif "Mathematics" in section.name:
            subjects_data = [
                ("MATH201", "Calculus I", 4, 65.0),
                ("MATH202", "Linear Algebra", 3, 60.0),
                ("MATH203", "Statistics", 3, 60.0)
            ]
        elif "Physics" in section.name:
            subjects_data = [
                ("PHY101", "Mechanics", 4, 60.0),
                ("PHY102", "Thermodynamics", 3, 65.0),
                ("PHY103", "Quantum Physics", 4, 70.0)
            ]
        else:
            subjects_data = [
                ("GEN101", "General Studies", 3, 60.0),
                ("GEN102", "Communication", 2, 55.0)
            ]
        
        for code, name, credits, passing_grade in subjects_data:
            subject = Subject(
                code=code,
                name=name,
                section_id=section.id,
                credits=credits,
                passing_grade=passing_grade
            )
            db.add(subject)
            print(f"  Added subject: {name}")
    
    db.commit()
    
    # Now create grades for sections that don't have any
    sections_without_grades = db.query(Section).filter(Section.educator_id == shaaf.id).all()
    
    for section in sections_without_grades:
        students = db.query(Student).filter(Student.section_id == section.id).all()
        subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
        
        grades_count = db.query(Grade).join(Student).filter(Student.section_id == section.id).count()
        
        if grades_count == 0 and students and subjects:
            print(f"Creating grades for {section.name} ({len(students)} students, {len(subjects)} subjects)")
            
            import random
            
            for student in students:
                for subject in subjects:
                    # Create 2-3 assessments per subject
                    num_assessments = random.randint(2, 3)
                    
                    for assessment in range(num_assessments):
                        # Generate realistic grade distribution
                        rand = random.random()
                        if rand < 0.1:  # 10% struggling
                            marks = random.uniform(40, 60)
                        elif rand < 0.8:  # 70% average to good
                            marks = random.uniform(60, 85)
                        else:  # 20% excellent
                            marks = random.uniform(85, 100)
                        
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
                        
                        assessment_types = ["Quiz", "Midterm", "Final Exam", "Assignment"]
                        assessment_type = random.choice(assessment_types)
                        
                        grade = Grade(
                            student_id=student.id,
                            subject_id=subject.id,
                            marks_obtained=round(marks, 1),
                            total_marks=100.0,
                            percentage=round(percentage, 1),
                            grade_letter=grade_letter,
                            is_passed=is_passed,
                            assessment_type=assessment_type
                        )
                        
                        db.add(grade)
    
    db.commit()
    
    # Print final summary
    print(f"\n=== Final Summary ===")
    shaaf_sections = db.query(Section).filter(Section.educator_id == shaaf.id).all()
    
    total_students = 0
    total_grades = 0
    
    for section in shaaf_sections:
        student_count = db.query(Student).filter(Student.section_id == section.id).count()
        grade_count = db.query(Grade).join(Student).filter(Student.section_id == section.id).count()
        
        print(f"{section.name}: {student_count} students, {grade_count} grades")
        total_students += student_count
        total_grades += grade_count
    
    print(f"\nShaaf's totals: {total_students} students, {total_grades} grades")
    
    db.close()

if __name__ == "__main__":
    assign_sections_to_shaaf()