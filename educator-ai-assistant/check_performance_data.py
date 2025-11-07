import sqlite3

# Connect to the database
conn = sqlite3.connect("educator_assistant.db")
cursor = conn.cursor()

print("🔍 Checking database for performance data...")

# Check students
cursor.execute("SELECT COUNT(*) FROM students")
student_count = cursor.fetchone()[0]
print(f"📚 Total students: {student_count}")

# Check sections  
cursor.execute("SELECT COUNT(*) FROM sections")
section_count = cursor.fetchone()[0]
print(f"📂 Total sections: {section_count}")

# Check grades
cursor.execute("SELECT COUNT(*) FROM grades")
grade_count = cursor.fetchone()[0]
print(f"📊 Total grades: {grade_count}")

# Check subjects
cursor.execute("SELECT COUNT(*) FROM subjects")
subject_count = cursor.fetchone()[0]
print(f"📖 Total subjects: {subject_count}")

if grade_count > 0:
    print(f"\n📋 Sample grades data:")
    cursor.execute("""
        SELECT s.first_name || ' ' || s.last_name, sub.name, g.marks_obtained, g.total_marks, g.percentage
        FROM grades g
        JOIN students s ON g.student_id = s.id
        JOIN subjects sub ON g.subject_id = sub.id
        LIMIT 5
    """)
    grades = cursor.fetchall()
    
    for grade in grades:
        print(f"  {grade[0]} - {grade[1]}: {grade[2]}/{grade[3]} ({grade[4]:.1f}%)")

# Check which educator has students
print(f"\n👥 Students per educator:")
cursor.execute("""
    SELECT e.first_name || ' ' || e.last_name as educator_name, 
           COUNT(DISTINCT s.id) as student_count,
           e.id as educator_id
    FROM educators e
    LEFT JOIN sections sec ON e.id = sec.educator_id
    LEFT JOIN students s ON sec.id = s.section_id
    GROUP BY e.id, educator_name
""")

educators = cursor.fetchall()
for edu in educators:
    print(f"  {edu[0]} (ID: {edu[2]}): {edu[1]} students")

conn.close()