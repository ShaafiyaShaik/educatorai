"""
Check what's currently in PostgreSQL
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models.educator import Educator
from app.models.student import Section, Student

db = SessionLocal()

print("=" * 70)
print("CHECKING POSTGRESQL CONTENT")
print("=" * 70)

# Check educators
print("\n📊 EDUCATORS:")
educators = db.query(Educator).all()
print(f"  Total: {len(educators)}")
for edu in educators:
    print(f"    - {edu.first_name} {edu.last_name} ({edu.email})")

# Check sections
print("\n📊 SECTIONS:")
sections = db.query(Section).all()
print(f"  Total: {len(sections)}")
for sec in sections:
    print(f"    - {sec.name} (ID: {sec.id}, Educator: {sec.educator_id})")

# Check students
print("\n📊 STUDENTS:")
students = db.query(Student).all()
print(f"  Total: {len(students)}")

# Count by section
for sec in sections:
    count = db.query(Student).filter(Student.section_id == sec.id).count()
    print(f"    - {sec.name}: {count} students")

db.close()

print("\n" + "=" * 70)
if len(educators) > 0 and len(sections) > 0 and len(students) > 0:
    print("✅ PostgreSQL has all necessary data!")
else:
    print("⚠️ PostgreSQL is missing some data")
