"""Seed educators and students into Supabase PostgreSQL."""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade
from passlib.context import CryptContext
from datetime import datetime
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

try:
    # Create educator
    hashed_pw = pwd_context.hash("SecurePass@123")
    educator = Educator(
        email="ananya.rao@university.edu",
        first_name="Ananya",
        last_name="Rao",
        hashed_password=hashed_pw,
        is_active=True,
        is_admin=False,
        department="Mathematics",
        title="Assistant Professor",
    )
    db.add(educator)
    db.commit()
    print(f"✅ Created educator: {educator.email} (ID: {educator.id})")

    # Create sections for educator
    sections_data = [
        ("Mathematics Section A", "2024-2025", "Fall"),
        ("Mathematics Section B", "2024-2025", "Fall"),
        ("Mathematics Section C", "2024-2025", "Fall"),
    ]
    
    sections = []
    for name, year, semester in sections_data:
        section = Section(
            name=name,
            educator_id=educator.id,
            academic_year=year,
            semester=semester,
        )
        db.add(section)
        sections.append(section)
    db.commit()
    print(f"✅ Created {len(sections)} sections")

    # Create subjects for each section
    SUBJECTS = [
        ("Mathematics", "MATH101", 3),
        ("Science", "SCI101", 3),
        ("English", "ENG101", 2),
    ]

    for section in sections:
        for name, code, credits in SUBJECTS:
            subject = Subject(
                name=name,
                code=code,
                section_id=section.id,
                credits=credits,
                passing_grade=60.0,
            )
            db.add(subject)
    db.commit()
    print(f"✅ Created {len(sections) * len(SUBJECTS)} subjects")

    # Create students (2 Indian students per section)
    MARKS_DISTRIBUTIONS = {
        "Mathematics": (55, 95),
        "Science": (50, 92),
        "English": (60, 96),
    }

    student_names = [
        ("Aarav", "Sharma"),
        ("Diya", "Verma"),
    ]

    total_students = 0
    total_grades = 0

    for section_idx, section in enumerate(sections, 1):
        for std_idx, (first, last) in enumerate(student_names, 1):
            student = Student(
                student_id=f"STU{section_idx:02d}{std_idx:02d}",
                first_name=first,
                last_name=last,
                email=f"{first.lower()}.{last.lower()}.s{section_idx}@student.edu",
                password_hash=pwd_context.hash("Student@123"),
                roll_number=std_idx,
                section_id=section.id,
                is_active=True,
            )
            db.add(student)
            total_students += 1

    db.commit()
    print(f"✅ Created {total_students} students")

    # Create grades for each student
    subjects_dict = {section.id: db.query(Subject).filter(Subject.section_id == section.id).all() for section in sections}
    students_list = db.query(Student).all()

    for student in students_list:
        subjects = subjects_dict[student.section_id]
        for subject in subjects:
            rng = MARKS_DISTRIBUTIONS.get(subject.name, (55, 95))
            marks = random.randint(rng[0], rng[1])
            
            grade = Grade(
                student_id=student.id,
                subject_id=subject.id,
                marks_obtained=float(marks),
                total_marks=100.0,
                assessment_type="Term Exam",
                assessment_date=datetime.utcnow(),
            )
            grade.calculate_percentage()
            grade.calculate_grade_letter()
            grade.is_passed = grade.percentage >= subject.passing_grade
            
            db.add(grade)
            total_grades += 1

    db.commit()
    print(f"✅ Created {total_grades} grades")

    print("\n🎉 Seeding complete!")
    print(f"   - 1 educator: ananya.rao@university.edu / SecurePass@123")
    print(f"   - 3 sections")
    print(f"   - {total_students} students (password: Student@123)")
    print(f"   - {total_grades} grades")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
