import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔧 Creating subjects and grades for students...")

# First, let's see what sections and students we have
cursor.execute("SELECT id, name FROM sections WHERE educator_id = 1")
sections = cursor.fetchall()
print(f"Sections: {sections}")

cursor.execute("SELECT id, first_name, last_name, section_id FROM students WHERE section_id IN (1, 2)")
students = cursor.fetchall()
print(f"Students: {students}")

# Create subjects for each section
subjects_data = [
    (1, 'Mathematics', 'MATH101', 4, 60.0),  # section 1
    (1, 'Algebra', 'ALG101', 3, 50.0),       # section 1  
    (2, 'Mathematics', 'MATH102', 4, 60.0),  # section 2
    (2, 'Geometry', 'GEO101', 3, 50.0),      # section 2
]

print("\n📚 Creating subjects...")
for section_id, name, code, credits, passing_grade in subjects_data:
    cursor.execute("""
        INSERT INTO subjects (name, code, section_id, credits, passing_grade, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, code, section_id, credits, passing_grade, datetime.now()))
    print(f"  ✅ Created: {name} ({code}) for Section {section_id}")

# Get the created subject IDs
cursor.execute("SELECT id, name, section_id FROM subjects")
subjects = cursor.fetchall()
print(f"\nCreated subjects: {subjects}")

# Create sample grades for each student in each subject of their section
import random

print(f"\n📊 Creating grades...")
grade_count = 0

for student_id, first_name, last_name, section_id in students:
    # Get subjects for this student's section
    section_subjects = [s for s in subjects if s[2] == section_id]
    
    for subject_id, subject_name, _ in section_subjects:
        # Generate random marks (60-95 for variety)
        total_marks = 100
        marks_obtained = random.randint(45, 95)  # Some failing, some passing
        percentage = (marks_obtained / total_marks) * 100
        
        # Determine grade letter and pass status
        if percentage >= 90:
            grade_letter = 'A'
        elif percentage >= 80:
            grade_letter = 'B'
        elif percentage >= 70:
            grade_letter = 'C'
        elif percentage >= 60:
            grade_letter = 'D'
        else:
            grade_letter = 'F'
            
        is_passed = percentage >= 60.0  # Assuming 60% is passing
        
        cursor.execute("""
            INSERT INTO grades (student_id, subject_id, marks_obtained, total_marks, 
                              percentage, grade_letter, is_passed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, subject_id, marks_obtained, total_marks, percentage, 
              grade_letter, is_passed, datetime.now(), datetime.now()))
        
        grade_count += 1
        print(f"  ✅ {first_name} {last_name}: {subject_name} = {marks_obtained}/{total_marks} ({grade_letter})")

print(f"\n✅ Created {grade_count} grade records!")

# Verify the data
cursor.execute("""
    SELECT s.first_name, s.last_name, sub.name, g.marks_obtained, g.total_marks, g.grade_letter
    FROM students s
    JOIN grades g ON s.id = g.student_id  
    JOIN subjects sub ON g.subject_id = sub.id
    ORDER BY s.section_id, s.last_name, sub.name
""")
results = cursor.fetchall()

print(f"\n📊 Grade Summary:")
for result in results:
    print(f"  {result[0]} {result[1]}: {result[2]} = {result[3]}/{result[4]} ({result[5]})")

conn.commit()
conn.close()

print(f"\n✅ Sample data creation completed!")