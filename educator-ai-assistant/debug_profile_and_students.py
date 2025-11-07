import sqlite3
import json

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔍 Investigating user profile and student data issues...\n")

# First check educator table structure
print("📋 EDUCATOR TABLE STRUCTURE:")
cursor.execute("PRAGMA table_info(educators)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check educators table for profile info
print("\n👤 EDUCATOR PROFILE DATA:")
cursor.execute("""
    SELECT id, email, first_name, last_name, title, subject 
    FROM educators WHERE email = 'ananya.rao@school.com'
""")
educator = cursor.fetchone()
if educator:
    print(f"  ID: {educator[0]}")
    print(f"  Email: {educator[1]}")
    print(f"  First Name: {educator[2]}")
    print(f"  Last Name: {educator[3]}")
    print(f"  Title: {educator[4]}")
    print(f"  Subject: {educator[5]}")
    full_name = f"{educator[2] or ''} {educator[3] or ''}".strip()
    print(f"  Full Name: {full_name}")
else:
    print("  ❌ No educator found!")

print("\n📚 SECTIONS FOR ANANYA:")
cursor.execute("""
    SELECT id, name, grade_level, subject, academic_year, semester
    FROM sections WHERE educator_id = ?
""", (educator[0] if educator else 1,))
sections = cursor.fetchall()
for section in sections:
    print(f"  Section {section[0]}: {section[1]} - {section[2]} {section[3]} ({section[4]} {section[5]})")

print(f"\n👨‍🎓 STUDENTS DATA:")
cursor.execute("SELECT COUNT(*) FROM students")
student_count = cursor.fetchone()[0]
print(f"  Total students in database: {student_count}")

if student_count > 0:
    print(f"\n  Sample students:")
    cursor.execute("""
        SELECT id, first_name, last_name, email, grade_level, enrollment_date
        FROM students LIMIT 5
    """)
    students = cursor.fetchall()
    for student in students:
        print(f"    Student {student[0]}: {student[1]} {student[2]} ({student[3]}) - Grade {student[4]}")

print(f"\n🔗 STUDENT-SECTION RELATIONSHIPS:")
cursor.execute("""
    SELECT ss.student_id, ss.section_id, s.first_name, s.last_name, sec.name
    FROM student_sections ss
    JOIN students s ON ss.student_id = s.id
    JOIN sections sec ON ss.section_id = sec.id
    ORDER BY ss.section_id, s.last_name
""")
relationships = cursor.fetchall()
if relationships:
    for rel in relationships:
        print(f"    Student {rel[0]} ({rel[2]} {rel[3]}) -> Section {rel[1]} ({rel[4]})")
else:
    print("    ❌ No student-section relationships found!")

# Check if student_sections table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_sections'")
table_exists = cursor.fetchone()
if not table_exists:
    print("    ❌ student_sections table does not exist!")
else:
    cursor.execute("SELECT COUNT(*) FROM student_sections")
    count = cursor.fetchone()[0]
    print(f"    Total relationships: {count}")

conn.close()