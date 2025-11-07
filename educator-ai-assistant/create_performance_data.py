import sqlite3
import random
from datetime import datetime

def create_performance_data():
    """Create sample performance data directly in the database"""
    
    conn = sqlite3.connect("educator_assistant.db")
    cursor = conn.cursor()
    
    print("🔧 Creating sample performance data...")
    
    # Get existing educator (we know test@test.com exists)
    cursor.execute("SELECT id FROM educators WHERE email = ?", ("test@test.com",))
    educator_result = cursor.fetchone()
    
    if not educator_result:
        print("❌ No test educator found. Creating one...")
        # Create educator if not exists
        cursor.execute("""
            INSERT INTO educators (email, first_name, last_name, hashed_password, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, ("test@test.com", "Test", "Teacher", "$2b$12$dummy_hash", 1))
        educator_id = cursor.lastrowid
    else:
        educator_id = educator_result[0]
    
    print(f"✅ Using educator ID: {educator_id}")
    
    # Get section IDs first to create subjects (subjects need section_id)
    cursor.execute("SELECT id FROM sections WHERE educator_id = ?", (educator_id,))
    existing_sections = cursor.fetchall()
    
    if not existing_sections:
        # Create sections first
        sections_data = [
            ("Section A", "2024-25", "Fall"),
            ("Section B", "2024-25", "Fall"),
            ("Section C", "2024-25", "Fall")
        ]
        
        section_ids = []
        for name, year, semester in sections_data:
            cursor.execute("""
                INSERT INTO sections (name, educator_id, academic_year, semester)
                VALUES (?, ?, ?, ?)
            """, (name, educator_id, year, semester))
            section_ids.append(cursor.lastrowid)
    else:
        section_ids = [row[0] for row in existing_sections]
    
    print(f"✅ Using sections: {section_ids}")
    
    # Create subjects (subjects need section_id according to schema)
    subjects = [
        ("MATH101", "Mathematics"),
        ("ENG101", "English"),
        ("SCI101", "Science"),
        ("HIST101", "History"),
        ("PHYS101", "Physics")
    ]
    
    subject_ids = []
    for code, name in subjects:
        cursor.execute("SELECT id FROM subjects WHERE code = ?", (code,))
        existing = cursor.fetchone()
        
        if existing:
            subject_ids.append(existing[0])
        else:
            # Use first section for subject creation
            cursor.execute("""
                INSERT INTO subjects (code, name, section_id, credits)
                VALUES (?, ?, ?, ?)
            """, (code, name, section_ids[0], 3))
            subject_ids.append(cursor.lastrowid)
    
    print(f"✅ Created/found {len(subjects)} subjects")
    
    # Create students
    student_names = [
        "John Smith", "Emma Johnson", "Michael Brown", "Sarah Davis", "David Wilson",
        "Lisa Garcia", "James Martinez", "Anna Rodriguez", "Robert Taylor", "Maria Lopez",
        "Christopher Lee", "Jessica White", "Daniel Harris", "Ashley Clark", "Matthew Lewis",
        "Amanda Walker", "Joshua Hall", "Stephanie Young", "Andrew King", "Michelle Wright",
        "Justin Green", "Melissa Adams", "Ryan Baker", "Nicole Nelson", "Brandon Hill",
        "Samantha Carter", "Tyler Moore", "Rachel Torres", "Jacob Phillips", "Lauren Evans"
    ]
    
    all_students = []
    student_counter = 1
    
    for section_id in section_ids:
        # Create 10 students per section
        section_students = []
        for i in range(10):
            if student_counter <= len(student_names):
                name_parts = student_names[student_counter - 1].split()
                first_name = name_parts[0]
                last_name = name_parts[1]
                
                student_id = f"STU{student_counter:03d}"
                email = f"student{student_counter}@test.edu"
                
                cursor.execute("SELECT id FROM students WHERE student_id = ?", (student_id,))
                existing = cursor.fetchone()
                
                if existing:
                    db_student_id = existing[0]
                else:
                    cursor.execute("""
                        INSERT INTO students (
                            student_id, first_name, last_name, email, 
                            password_hash, roll_number, section_id, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (student_id, first_name, last_name, email, "$2b$12$dummy", student_counter, section_id, 1))
                    db_student_id = cursor.lastrowid
                
                section_students.append(db_student_id)
                all_students.append(db_student_id)
                student_counter += 1
    
    print(f"✅ Created/found {len(all_students)} students")
    
    # Create grades for students
    grade_count = 0
    for student_id in all_students:
        for subject_id in subject_ids:
            # Generate realistic grade data
            base_score = random.randint(45, 95)  # Base performance
            total_marks = 100
            marks_obtained = min(total_marks, base_score + random.randint(-10, 15))
            percentage = (marks_obtained / total_marks) * 100
            
            # Determine grade letter
            if percentage >= 90:
                grade_letter = 'A+'
            elif percentage >= 85:
                grade_letter = 'A'
            elif percentage >= 80:
                grade_letter = 'B+'
            elif percentage >= 75:
                grade_letter = 'B'
            elif percentage >= 70:
                grade_letter = 'C+'
            elif percentage >= 65:
                grade_letter = 'C'
            elif percentage >= 60:
                grade_letter = 'D'
            else:
                grade_letter = 'F'
            
            is_passed = percentage >= 60
            
            # Check if grade already exists
            cursor.execute("SELECT id FROM grades WHERE student_id = ? AND subject_id = ?", 
                         (student_id, subject_id))
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO grades (
                        student_id, subject_id, marks_obtained, total_marks, 
                        percentage, grade_letter, is_passed, assessment_type, assessment_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_id, subject_id, marks_obtained, total_marks,
                    percentage, grade_letter, is_passed, "Final", datetime.now()
                ))
                grade_count += 1
    
    print(f"✅ Created {grade_count} grade records")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Performance data creation completed!")
    print("📊 Summary:")
    print(f"   - {len(subjects)} subjects")
    print(f"   - {len(sections_data)} sections") 
    print(f"   - {len(all_students)} students")
    print(f"   - {grade_count} grade records")
    print("\n✅ You can now login and view performance analytics!")

if __name__ == "__main__":
    create_performance_data()