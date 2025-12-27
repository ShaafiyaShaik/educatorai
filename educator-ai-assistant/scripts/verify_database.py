"""Verify database state for Ananya's account."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / 'educator_db.sqlite'
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

print("=" * 60)
print("DATABASE STATE VERIFICATION")
print("=" * 60)

# Check educators
print("\n📋 EDUCATORS:")
cur.execute("SELECT id, email, first_name, last_name, is_active FROM educators")
for row in cur.fetchall():
    print(f"  ID: {row[0]}, Email: {row[1]}, Name: {row[2]} {row[3]}, Active: {row[4]}")

# Check sections for Ananya (id=2)
print("\n📚 SECTIONS (Ananya - ID 2):")
cur.execute("SELECT id, name, educator_id, academic_year, semester FROM sections WHERE educator_id=2")
sections = cur.fetchall()
for row in sections:
    print(f"  ID: {row[0]}, Name: {row[1]}, Educator: {row[2]}, Year: {row[3]}, Semester: {row[4]}")

# Check students per section
print("\n👥 STUDENTS PER SECTION:")
for section in sections:
    section_id = section[0]
    section_name = section[1]
    cur.execute("SELECT COUNT(*) FROM students WHERE section_id=?", (section_id,))
    count = cur.fetchone()[0]
    print(f"  Section {section_id} ({section_name}): {count} students")
    
    # Show first 3 students as sample
    cur.execute("SELECT id, first_name, last_name, email FROM students WHERE section_id=? LIMIT 3", (section_id,))
    students = cur.fetchall()
    for s in students:
        print(f"    - {s[1]} {s[2]} ({s[3]})")

# Check subjects
print("\n📖 SUBJECTS:")
cur.execute("""
    SELECT s.id, s.name, s.code, sec.name 
    FROM subjects s 
    JOIN sections sec ON s.section_id = sec.id 
    WHERE sec.educator_id=2
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  ID: {row[0]}, Name: {row[1]}, Code: {row[2]}, Section: {row[3]}")

# Check grades sample
print("\n📊 GRADES (Sample):")
cur.execute("""
    SELECT g.id, st.first_name || ' ' || st.last_name as student, 
           sub.name as subject, g.marks_obtained, g.total_marks, g.percentage
    FROM grades g
    JOIN students st ON g.student_id = st.id
    JOIN subjects sub ON g.subject_id = sub.id
    JOIN sections sec ON st.section_id = sec.id
    WHERE sec.educator_id=2
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  {row[1]}: {row[2]} - {row[3]}/{row[4]} ({row[5]}%)")

print("\n" + "=" * 60)
print("DATABASE VERIFICATION COMPLETE")
print("=" * 60)

conn.close()
