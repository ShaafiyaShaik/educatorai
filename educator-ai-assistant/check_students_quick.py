import sqlite3

# Connect to the database
conn = sqlite3.connect('educator_assistant.db')
cursor = conn.cursor()

# Check students
try:
    cursor.execute("SELECT COUNT(*) FROM students;")
    count = cursor.fetchone()[0]
    print(f"Total students in database: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, email, first_name, last_name, section_id FROM students LIMIT 10;")
        students = cursor.fetchall()
        print(f"\nFirst 10 students:")
        for student in students:
            print(f"  ID: {student[0]}, Email: {student[1]}, Name: {student[2]} {student[3]}, Section: {student[4]}")
            
        # Check grades
        cursor.execute("SELECT COUNT(*) FROM grades;")
        grade_count = cursor.fetchone()[0]
        print(f"\nTotal grades in database: {grade_count}")
        
        if grade_count > 0:
            cursor.execute("""
                SELECT s.email, s.first_name, s.last_name, sub.name, g.marks_obtained 
                FROM students s 
                JOIN grades g ON s.id = g.student_id 
                JOIN subjects sub ON g.subject_id = sub.id 
                LIMIT 10
            """)
            grades = cursor.fetchall()
            print(f"\nFirst 10 grades:")
            for grade in grades:
                print(f"  {grade[1]} {grade[2]} ({grade[0]}) - {grade[3]}: {grade[4]}")
    
except Exception as e:
    print("Error querying students table:", e)

conn.close()