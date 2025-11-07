import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("📊 Database Summary:")
print("==================")

# Check teachers
cursor.execute("SELECT COUNT(*) FROM educators WHERE employee_id LIKE 'T%'")
teacher_count = cursor.fetchone()[0]
print(f"👨‍🏫 Teachers: {teacher_count}")

cursor.execute("SELECT employee_id, first_name, last_name, email, department FROM educators WHERE employee_id LIKE 'T%'")
teachers = cursor.fetchall()
for teacher in teachers:
    print(f"   • {teacher[0]}: {teacher[1]} {teacher[2]} ({teacher[4]}) - {teacher[3]}")

# Check sections
cursor.execute("SELECT COUNT(*) FROM sections")
sections_count = cursor.fetchone()[0]
print(f"\n📚 Sections: {sections_count}")

cursor.execute("""
    SELECT s.name, e.first_name, e.last_name 
    FROM sections s 
    JOIN educators e ON s.educator_id = e.id 
    ORDER BY s.name
""")
sections = cursor.fetchall()
for section in sections:
    print(f"   • {section[0]} - Teacher: {section[1]} {section[2]}")

# Check students
cursor.execute("SELECT COUNT(*) FROM students WHERE student_id LIKE 'S%'")
students_count = cursor.fetchone()[0]
print(f"\n👨‍🎓 Students: {students_count}")

cursor.execute("""
    SELECT st.student_id, st.first_name, st.last_name, s.name 
    FROM students st 
    JOIN sections s ON st.section_id = s.id 
    WHERE st.student_id LIKE 'S%'
    ORDER BY st.student_id
""")
students = cursor.fetchall()
for student in students:
    print(f"   • {student[0]}: {student[1]} {student[2]} - Section: {student[3]}")

# Check parents
cursor.execute("SELECT COUNT(*) FROM parents WHERE email LIKE '%.p%@school.com'")
parents_count = cursor.fetchone()[0]
print(f"\n👨‍👩‍👧‍👦 Parents: {parents_count}")

cursor.execute("""
    SELECT p.first_name, p.last_name, p.email, st.first_name as student_first, st.last_name as student_last
    FROM parents p 
    JOIN students st ON p.student_id = st.id 
    WHERE p.email LIKE '%.p%@school.com'
    ORDER BY p.email
""")
parents = cursor.fetchall()
for parent in parents:
    print(f"   • {parent[0]} {parent[1]} ({parent[2]}) - Child: {parent[3]} {parent[4]}")

conn.close()