import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔧 Adding missing columns to sections table...")

# Check current sections table structure
cursor.execute("PRAGMA table_info(sections)")
existing_columns = [col[1] for col in cursor.fetchall()]
print(f"Current sections columns: {existing_columns}")

# Add missing columns for sections
missing_section_columns = []

if 'academic_year' not in existing_columns:
    missing_section_columns.append(("academic_year", "TEXT"))
if 'semester' not in existing_columns:
    missing_section_columns.append(("semester", "TEXT"))
if 'grade' not in existing_columns:
    missing_section_columns.append(("grade", "TEXT"))
if 'subject' not in existing_columns:
    missing_section_columns.append(("subject", "TEXT"))
if 'capacity' not in existing_columns:
    missing_section_columns.append(("capacity", "INTEGER DEFAULT 30"))

for column_name, column_type in missing_section_columns:
    try:
        cursor.execute(f"ALTER TABLE sections ADD COLUMN {column_name} {column_type}")
        print(f"  ✅ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"  ⚠️ Column {column_name} already exists")
        else:
            print(f"  ❌ Error adding {column_name}: {e}")

conn.commit()

# Verify the sections table structure
cursor.execute("PRAGMA table_info(sections)")
sections_columns = cursor.fetchall()
print(f"\n📊 Updated sections table has {len(sections_columns)} columns:")
for col in sections_columns:
    print(f"  {col[1]} ({col[2]})")

# Also need to update students table for missing columns
cursor.execute("PRAGMA table_info(students)")
existing_student_columns = [col[1] for col in cursor.fetchall()]
print(f"\nCurrent students columns: {existing_student_columns}")

missing_student_columns = []
if 'grade_level' not in existing_student_columns:
    missing_student_columns.append(("grade_level", "TEXT"))
if 'enrollment_date' not in existing_student_columns:
    missing_student_columns.append(("enrollment_date", "DATE"))

for column_name, column_type in missing_student_columns:
    try:
        cursor.execute(f"ALTER TABLE students ADD COLUMN {column_name} {column_type}")
        print(f"  ✅ Added student column: {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"  ⚠️ Column {column_name} already exists")
        else:
            print(f"  ❌ Error adding {column_name}: {e}")

conn.commit()
conn.close()
print("\n✅ Database schema fully updated!")