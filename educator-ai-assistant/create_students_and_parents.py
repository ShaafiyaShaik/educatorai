#!/usr/bin/env python3
"""
Create students and parent accounts for the new teacher sections
"""

import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_students_and_parents():
    """Create students and parents for each section"""
    conn = sqlite3.connect('educator_assistant.db')
    cursor = conn.cursor()
    
    try:
        # Get the new teacher sections (IDs 19-27)
        new_sections = [
            (19, "Math Grade 9A", "John Smith"),
            (20, "Math Grade 9B", "John Smith"),
            (21, "Math Grade 10A", "John Smith"),
            (22, "Science Grade 8A", "Sarah Johnson"),
            (23, "Science Grade 8B", "Sarah Johnson"),
            (24, "Biology Grade 11", "Sarah Johnson"),
            (25, "English Grade 7A", "Michael Brown"),
            (26, "English Grade 7B", "Michael Brown"),
            (27, "Literature Grade 12", "Michael Brown")
        ]
        
        # Student and parent data template
        students_data = []
        parents_data = []
        
        roll_number_counter = 1001  # Start from 1001 to avoid conflicts
        
        for section_id, section_name, teacher_name in new_sections:
            print(f"Creating students for {section_name} (Teacher: {teacher_name})")
            
            # Create 2 students per section as requested
            for i in range(1, 3):  # Student 1 and Student 2
                # Student data
                student_email = f"student{section_id}_{i}@school.edu"
                student_first_name = f"Student{section_id}_{i}"
                student_last_name = "Doe"
                student_roll_number = f"ROLL{roll_number_counter}"
                roll_number_counter += 1
                
                # Parent data
                parent_email = f"parent{section_id}_{i}@school.edu"
                parent_first_name = f"Parent{section_id}_{i}"
                parent_last_name = "Doe"
                
                students_data.append((
                    student_email,
                    hash_password("student123"),  # Default password
                    student_first_name,
                    student_last_name,
                    student_roll_number,
                    section_id,
                    datetime.now(),
                    datetime.now()
                ))
                
                parents_data.append((
                    parent_email,
                    hash_password("parent123"),  # Default password
                    parent_first_name,
                    parent_last_name,
                    datetime.now(),
                    datetime.now()
                ))
        
        # Insert students
        print(f"Inserting {len(students_data)} students...")
        cursor.executemany("""
            INSERT INTO students (email, password_hash, first_name, last_name, roll_number, section_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, students_data)
        
        # Insert parents
        print(f"Inserting {len(parents_data)} parents...")
        cursor.executemany("""
            INSERT INTO parents (email, password_hash, first_name, last_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, parents_data)
        
        # Create parent-student relationships
        print("Creating parent-student relationships...")
        
        # Get the student IDs we just created
        cursor.execute("SELECT id, email, section_id FROM students WHERE email LIKE 'student%@school.edu'")
        new_students = cursor.fetchall()
        
        # Get parent IDs
        cursor.execute("SELECT id, email FROM parents WHERE email LIKE 'parent%@school.edu'")
        new_parents = cursor.fetchall()
        
        # Create relationships based on matching section and number
        parent_student_relations = []
        for student_id, student_email, section_id in new_students:
            # Extract section and student number from email
            section_part = student_email.split('_')[0].replace('student', '')
            student_number = student_email.split('_')[1].split('@')[0]
            
            # Find matching parent
            expected_parent_email = f"parent{section_part}_{student_number}@school.edu"
            
            for parent_id, parent_email in new_parents:
                if parent_email == expected_parent_email:
                    parent_student_relations.append((parent_id, student_id, datetime.now(), datetime.now()))
                    break
        
        cursor.executemany("""
            INSERT INTO parent_student_relationships (parent_id, student_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, parent_student_relations)
        
        conn.commit()
        print(f"\n✅ Successfully created:")
        print(f"   - {len(students_data)} students")
        print(f"   - {len(parents_data)} parents") 
        print(f"   - {len(parent_student_relations)} parent-student relationships")
        
        print(f"\n🔑 Login credentials:")
        print(f"   - Students: password 'student123'")
        print(f"   - Parents: password 'parent123'")
        
    except Exception as e:
        print(f"❌ Error creating accounts: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_students_and_parents()