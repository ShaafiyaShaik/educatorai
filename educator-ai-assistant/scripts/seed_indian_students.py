"""
Seed two Indian student accounts per section owned by Ananya Rao.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.core.auth import get_password_hash
from app.models.student import Student, Section
from app.models.educator import Educator

STUDENT_PASSWORD = "Student@123"

NAMES = [
    ("Aarav", "Sharma"),
    ("Diya", "Verma"),
    ("Vivaan", "Iyer"),
    ("Anika", "Menon"),
    ("Rohan", "Patel"),
    ("Isha", "Kapoor"),
]

def ensure_students_for_section(db, section, names, created_emails: set):
    created = 0
    # Create two students per section
    for idx, (first, last) in enumerate(names[:2], start=1):
        # Make email unique per section
        email = f"{first.lower()}.{last.lower()}.s{section.id}@student.edu"
        if email in created_emails:
            continue
        existing = db.query(Student).filter(Student.email == email).first()
        if existing:
            continue
        s = Student(
            student_id=f"S{section.id:02d}{idx:02d}",
            first_name=first,
            last_name=last,
            email=email,
            password_hash=get_password_hash(STUDENT_PASSWORD),
            roll_number=idx,
            section_id=section.id,
            phone="+91-98765-43210",
            guardian_email=f"guardian.{first.lower()}@example.com",
            is_active=True,
        )
        db.add(s)
        created_emails.add(email)
        created += 1
    return created

if __name__ == "__main__":
    db = SessionLocal()
    try:
        ananya = db.query(Educator).filter(Educator.email == "ananya.rao@school.com").first()
        if not ananya:
            print("❌ Ananya educator account not found")
            sys.exit(1)
        sections = db.query(Section).filter(Section.educator_id == ananya.id).all()
        print(f"Found {len(sections)} sections for Ananya")
        total_created = 0
        created_emails: set[str] = set()
        for sec in sections:
            created = ensure_students_for_section(db, sec, NAMES, created_emails)
            print(f"Section '{sec.name}' -> created {created} students")
            total_created += created
        db.commit()
        print(f"✅ Seeding complete. Created {total_created} students.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()
