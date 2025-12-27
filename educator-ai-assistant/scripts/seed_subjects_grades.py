"""Seed standard subjects and sample grades for Ananya Rao's sections.

- Creates subjects per section if missing: Mathematics, Science, English
- Assigns grades for each student in each subject with realistic marks
- Works with PostgreSQL configured via app.core.config.Settings

Usage:
  - Windows PowerShell:
      cd educator-ai-assistant; python scripts/seed_subjects_grades.py

Optional environment variables:
  - TARGET_EDUCATOR_EMAIL: set to educator email (default 'ananya.rao@university.edu')
  - SUBJECTS: comma-separated subject names (default 'Mathematics,Science,English')

"""
import os
import sys
import random
from datetime import datetime

from pathlib import Path
# Ensure project root is on sys.path so `app.*` imports work when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models.educator import Educator
from app.models.student import Section, Student, Subject, Grade

DEFAULT_SUBJECTS = [
    ("Mathematics", "MATH101", 3),
    ("Science", "SCI101", 3),
    ("English", "ENG101", 2),
]

TARGET_EMAIL = os.getenv("TARGET_EDUCATOR_EMAIL", "ananya.rao@university.edu")

# Marks distributions per subject (min, max)
MARKS_DISTRIBUTIONS = {
    "Mathematics": (55, 95),
    "Science": (50, 92),
    "English": (60, 96),
}


def seed_subjects_and_grades():
    db = SessionLocal()
    try:
        educator = (
            db.query(Educator)
            .filter(Educator.email == TARGET_EMAIL)
            .first()
        )
        if not educator:
            educator = (
                db.query(Educator)
                .filter(Educator.first_name.ilike("ananya"))
                .first()
            )
        if not educator:
            print("❌ Educator 'Ananya' not found. Set TARGET_EDUCATOR_EMAIL.")
            return

        sections = db.query(Section).filter(Section.educator_id == educator.id).all()
        if not sections:
            print(f"❌ No sections found for educator {educator.full_name} (id={educator.id}).")
            return

        total_subjects_created = 0
        total_grades_created = 0

        for section in sections:
            print(f"\n📚 Section {section.id} - {section.name}")
            # Ensure subjects exist
            existing_subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
            if not existing_subjects:
                for name, code, credits in DEFAULT_SUBJECTS:
                    s = Subject(name=name, code=code, section_id=section.id, credits=credits, passing_grade=60.0)
                    db.add(s)
                    total_subjects_created += 1
                db.commit()
                existing_subjects = db.query(Subject).filter(Subject.section_id == section.id).all()
                print(f"   + Created {len(existing_subjects)} subjects")
            else:
                print(f"   = Found {len(existing_subjects)} subjects")

            # Assign grades for each student per subject if none exist
            students = db.query(Student).filter(Student.section_id == section.id).all()
            print(f"   = Students: {len(students)}")

            for student in students:
                for subject in existing_subjects:
                    # Check if a grade exists already
                    existing_grade = (
                        db.query(Grade)
                        .filter(Grade.student_id == student.id, Grade.subject_id == subject.id)
                        .first()
                    )
                    if existing_grade:
                        continue

                    # Generate marks
                    rng = MARKS_DISTRIBUTIONS.get(subject.name, (55, 95))
                    marks = random.randint(rng[0], rng[1])
                    total = 100

                    grade = Grade(
                        student_id=student.id,
                        subject_id=subject.id,
                        marks_obtained=float(marks),
                        total_marks=float(total),
                        assessment_type="Term Exam",
                        assessment_date=datetime.utcnow(),
                    )
                    grade.calculate_percentage()
                    grade.calculate_grade_letter()
                    grade.is_passed = grade.percentage >= subject.passing_grade

                    db.add(grade)
                    total_grades_created += 1

            db.commit()
            print(f"   + Grades added where missing")

        print(f"\n✅ Seeding complete. Subjects created: {total_subjects_created}, Grades created: {total_grades_created}.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_subjects_and_grades()
