import sqlite3
import json

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔍 Investigating database structure and data...\n")

# Check sections table structure
print("📋 SECTIONS TABLE STRUCTURE:")
cursor.execute("PRAGMA table_info(sections)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check students table structure  
print("\n📋 STUDENTS TABLE STRUCTURE:")
cursor.execute("PRAGMA table_info(students)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check if student_sections table exists
print("\n📋 STUDENT_SECTIONS TABLE:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_sections'")
table_exists = cursor.fetchone()
if table_exists:
    cursor.execute("PRAGMA table_info(student_sections)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
else:
    print("  ❌ Table does not exist!")

# Check educator profile data
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

# Check sections for Ananya
print(f"\n📚 SECTIONS FOR ANANYA:")
cursor.execute("SELECT * FROM sections WHERE educator_id = ?", (educator[0] if educator else 1,))
sections = cursor.fetchall()
for section in sections:
    print(f"  Section: {section}")

# Check students count
print(f"\n👨‍🎓 STUDENTS DATA:")
cursor.execute("SELECT COUNT(*) FROM students")
student_count = cursor.fetchone()[0]
print(f"  Total students in database: {student_count}")

if student_count > 0:
    print(f"\n  Sample students:")
    cursor.execute("SELECT * FROM students LIMIT 3")
    students = cursor.fetchall()
    for student in students:
        print(f"    Student: {student}")

print(f"\n🔗 STUDENT-SECTION RELATIONSHIPS:")
if table_exists:
    cursor.execute("SELECT COUNT(*) FROM student_sections")
    count = cursor.fetchone()[0]
    print(f"    Total relationships: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM student_sections LIMIT 5")
        relationships = cursor.fetchall()
        for rel in relationships:
            print(f"    Relationship: {rel}")
else:
    print("    ❌ student_sections table missing!")

conn.close()