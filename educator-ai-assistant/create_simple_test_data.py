#!/usr/bin/env python3
"""
Create simple test data for performance views testing
"""

from app.core.database import SessionLocal
from app.models.student import Student, Section, Grade, Subject
from app.models.educator import Educator
from app.core.auth import get_password_hash
import random

def create_test_data():
    """Create test sections, students, subjects and grades"""
    
    db = SessionLocal()
    
    try:
        # Get the test educator
        educator = db.query(Educator).filter(Educator.email == 'shaaf@gmail.com').first()
        if not educator:
            print("❌ Test educator not found")
            return
            
        print(f"📚 Creating test data for {educator.email}")
        
        # Create sections
        sections_data = [
            {"name": "Computer Science A"},
            {"name": "Mathematics B"},
            {"name": "Physics C"}
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
                    educator_id=educator.id
                )
                db.add(section)
                db.flush()
                sections.append(section)
                print(f"  ✅ Created section: {section.name}")
            else:
                sections.append(existing_section)
                print(f"  📝 Using existing section: {existing_section.name}")
        
        # Create subjects for each section
        subjects_data = [
            {"name": "Programming Fundamentals", "code": "CS101"},
            {"name": "Data Structures", "code": "CS102"},
            {"name": "Calculus I", "code": "MATH101"},
            {"name": "Linear Algebra", "code": "MATH102"},
            {"name": "Classical Mechanics", "code": "PHY101"},
            {"name": "Electromagnetism", "code": "PHY102"}
        ]
        
        all_subjects = []
        for i, section in enumerate(sections):
            # Each section gets 2 subjects
            section_subjects = subjects_data[i*2:(i*2)+2]
            for subj_data in section_subjects:
                existing_subject = db.query(Subject).filter(
                    Subject.name == subj_data["name"],
                    Subject.section_id == section.id
                ).first()
                
                if not existing_subject:
                    subject = Subject(
                        name=subj_data["name"],
                        code=subj_data["code"],
                        section_id=section.id
                    )
                    db.add(subject)
                    db.flush()
                    all_subjects.append(subject)
                    print(f"    ➕ Created subject: {subject.name} for {section.name}")
                else:
                    all_subjects.append(existing_subject)
                    print(f"    📝 Using existing subject: {existing_subject.name}")
        
        # Create students for each section
        student_names = [
            ("Alice", "Johnson"), ("Bob", "Smith"), ("Charlie", "Brown"),
            ("Diana", "Wilson"), ("Edward", "Davis"), ("Fiona", "Miller"),
            ("George", "Garcia"), ("Hannah", "Martinez"), ("Ian", "Anderson"),
            ("Julia", "Taylor"), ("Kevin", "Thomas"), ("Laura", "Jackson"),
            ("Michael", "White"), ("Nina", "Harris"), ("Oscar", "Martin"),
            ("Paula", "Thompson"), ("Quinn", "Moore"), ("Rachel", "Lee"),
            ("Samuel", "Walker"), ("Tina", "Hall")
        ]
        
        all_students = []
        for section in sections:
            section_students = []
            for i in range(7):  # 7 students per section for testing
                if i < len(student_names):
                    first_name, last_name = student_names[i]
                    email = f"{first_name.lower()}.{last_name.lower()}@student.edu"
                    
                    existing_student = db.query(Student).filter(Student.email == email).first()
                    
                    if not existing_student:
                        student = Student(
                            student_id=f"{section.name[:2]}{i+1:03d}",
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            password_hash=get_password_hash("student123"),
                            roll_number=i+1,
                            section_id=section.id
                        )
                        db.add(student)
                        db.flush()
                        section_students.append(student)
                        all_students.append(student)
                        print(f"      👤 Created student: {student.first_name} {student.last_name}")
                    else:
                        section_students.append(existing_student)
                        all_students.append(existing_student)
        
        # Create grades for students
        print(f"\n📊 Creating grades...")
        grade_count = 0
        
        for section in sections:
            # Get students in this section
            section_students = [s for s in all_students if s.section_id == section.id]
            # Get subjects for this section
            section_subjects = [s for s in all_subjects if s.section_id == section.id]
            
            for student in section_students:
                for subject in section_subjects:
                    # Check if grade already exists
                    existing_grade = db.query(Grade).filter(
                        Grade.student_id == student.id,
                        Grade.subject_id == subject.id
                    ).first()
                    
                    if not existing_grade:
                        # Generate random grade (60-95 range with some failing grades)
                        marks_obtained = random.randint(45, 95)
                        total_marks = 100
                        percentage = marks_obtained
                        
                        grade = Grade(
                            student_id=student.id,
                            subject_id=subject.id,
                            marks_obtained=marks_obtained,
                            total_marks=total_marks,
                            percentage=percentage,
                            assessment_type="Final Exam"
                        )
                        db.add(grade)
                        grade_count += 1
        
        print(f"  ✅ Created {grade_count} grades")
        
        # Commit all changes
        db.commit()
        
        print(f"\n🎉 Test data creation complete!")
        print(f"   📚 Sections: {len(sections)}")
        print(f"   📖 Subjects: {len(all_subjects)}")
        print(f"   👥 Students: {len(all_students)}")
        print(f"   📊 Grades: {grade_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()