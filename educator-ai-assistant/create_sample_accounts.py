#!/usr/bin/env python3
"""
Create sample accounts for teachers, students, and parents
"""

import sqlite3
from datetime import datetime
import hashlib
import os

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_sample_accounts():
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'educator_assistant.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Creating sample accounts...")
    
    # Sample teacher data
    teachers = [
        {
            'first_name': 'John',
            'last_name': 'Smith', 
            'email': 'teacher1@school.edu',
            'password': 'password123',
            'department': 'Mathematics',
            'title': 'Mathematics Teacher',
            'office_location': 'Room 101',
            'phone': '+1-555-0101'
        },
        {
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'email': 'teacher2@school.edu', 
            'password': 'password123',
            'department': 'Science',
            'title': 'Science Teacher',
            'office_location': 'Room 201',
            'phone': '+1-555-0102'
        },
        {
            'first_name': 'Michael',
            'last_name': 'Brown',
            'email': 'teacher3@school.edu',
            'password': 'password123', 
            'department': 'English',
            'title': 'English Teacher',
            'office_location': 'Room 301',
            'phone': '+1-555-0103'
        }
    ]
    
    # Create teachers
    teacher_ids = []
    for i, teacher in enumerate(teachers, 1):
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO educators 
                (first_name, last_name, email, hashed_password, department, title, office_location, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                teacher['first_name'],
                teacher['last_name'], 
                teacher['email'],
                hash_password(teacher['password']),
                teacher['department'],
                teacher['title'],
                teacher['office_location'],
                teacher['phone'],
                datetime.now().isoformat()
            ))
            teacher_id = cursor.lastrowid
            teacher_ids.append(teacher_id)
            print(f"✅ Created teacher: {teacher['first_name']} {teacher['last_name']} (ID: {teacher_id})")
        except Exception as e:
            print(f"❌ Error creating teacher {teacher['email']}: {e}")
    
    # Sample section data for each teacher
    sections_data = [
        # Teacher 1 (John Smith - Math) sections
        [
            {'name': 'Math Grade 9A', 'grade_level': '9', 'subject': 'Mathematics'},
            {'name': 'Math Grade 9B', 'grade_level': '9', 'subject': 'Mathematics'}, 
            {'name': 'Math Grade 10A', 'grade_level': '10', 'subject': 'Mathematics'}
        ],
        # Teacher 2 (Sarah Johnson - Science) sections  
        [
            {'name': 'Science Grade 8A', 'grade_level': '8', 'subject': 'Science'},
            {'name': 'Science Grade 8B', 'grade_level': '8', 'subject': 'Science'},
            {'name': 'Biology Grade 11', 'grade_level': '11', 'subject': 'Biology'}
        ],
        # Teacher 3 (Michael Brown - English) sections
        [
            {'name': 'English Grade 7A', 'grade_level': '7', 'subject': 'English'},
            {'name': 'English Grade 7B', 'grade_level': '7', 'subject': 'English'},
            {'name': 'Literature Grade 12', 'grade_level': '12', 'subject': 'Literature'}
        ]
    ]
    
    # Student names pool
    first_names = [
        'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'Ethan', 'Sophia', 'Mason',
        'Isabella', 'William', 'Mia', 'James', 'Charlotte', 'Benjamin', 'Amelia', 'Lucas',
        'Harper', 'Henry', 'Evelyn', 'Alexander', 'Abigail', 'Sebastian', 'Emily', 'Jackson'
    ]
    
    last_names = [
        'Anderson', 'Garcia', 'Martinez', 'Davis', 'Rodriguez', 'Wilson', 'Moore', 'Taylor',
        'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Lewis', 'Walker',
        'Hall', 'Allen', 'Young', 'King', 'Wright', 'Scott', 'Green', 'Baker'
    ]
    
    # Create sections and students
    student_counter = 1
    parent_counter = 1
    
    for teacher_idx, teacher_id in enumerate(teacher_ids):
        teacher_sections = sections_data[teacher_idx]
        
        for section_data in teacher_sections:
            # Create section
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO sections 
                    (name, educator_id, academic_year, semester, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    section_data['name'],
                    teacher_id,
                    '2024-25',
                    'Fall 2024',
                    datetime.now().isoformat()
                ))
                section_id = cursor.lastrowid
                print(f"  📚 Created section: {section_data['name']} (ID: {section_id})")
                
                # Create 2 students for each section
                for i in range(2):
                    first_name = first_names[(student_counter - 1) % len(first_names)]
                    last_name = last_names[(student_counter - 1) % len(last_names)]
                    
                    student_email = f"student{student_counter:03d}@school.edu"
                    student_id_number = f"STU{student_counter:04d}"
                    
                    # Create student
                    cursor.execute("""
                        INSERT OR REPLACE INTO students
                        (student_id, first_name, last_name, email, password_hash, roll_number, section_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        student_id_number,
                        first_name,
                        last_name,
                        student_email,
                        hash_password('student123'),
                        student_counter,  # roll_number
                        section_id,
                        datetime.now().isoformat()
                    ))
                    db_student_id = cursor.lastrowid
                    print(f"    👨‍🎓 Created student: {first_name} {last_name} ({student_id_number})")
                    
                    # Create parent accounts for this student
                    parent_emails = [
                        f"parent{parent_counter:03d}a@email.com",  # Parent 1
                        f"parent{parent_counter:03d}b@email.com"   # Parent 2  
                    ]
                    
                    parent_names = [
                        (f"Parent1_{first_name}", last_name),
                        (f"Parent2_{first_name}", last_name)
                    ]
                    
                    for j, (parent_first, parent_last) in enumerate(parent_names):
                        try:
                            cursor.execute("""
                                INSERT OR REPLACE INTO parents
                                (first_name, last_name, email, password_hash, phone, student_id, relationship, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                parent_first,
                                parent_last,
                                parent_emails[j],
                                hash_password('parent123'),
                                f'+1-555-{(parent_counter*10 + j):04d}',
                                db_student_id,
                                'Parent' if j == 0 else 'Guardian',
                                datetime.now().isoformat()
                            ))
                            print(f"      👨‍👩‍👧‍👦 Created parent: {parent_first} {parent_last} ({parent_emails[j]})")
                        except Exception as e:
                            print(f"      ❌ Error creating parent: {e}")
                    
                    student_counter += 1
                    parent_counter += 1
                    
            except Exception as e:
                print(f"  ❌ Error creating section {section_data['name']}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT COUNT(*) FROM educators WHERE email LIKE 'teacher%@school.edu'")
    teacher_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sections WHERE educator_id IN (SELECT id FROM educators WHERE email LIKE 'teacher%@school.edu')")  
    section_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE email LIKE 'student%@school.edu'")
    student_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parents WHERE email LIKE 'parent%@email.com'")
    parent_count = cursor.fetchone()[0]
    
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    print(f"👨‍🏫 Teachers created: {teacher_count}")
    print(f"📚 Sections created: {section_count}")  
    print(f"👨‍🎓 Students created: {student_count}")
    print(f"👨‍👩‍👧‍👦 Parents created: {parent_count}")
    print("="*50)
    
    print("\n🔑 LOGIN CREDENTIALS:")
    print("Teachers:")
    for teacher in teachers:
        print(f"  📧 {teacher['email']} / password123")
    
    print("\nStudents (sample):")
    cursor.execute("SELECT email FROM students WHERE email LIKE 'student%@school.edu' LIMIT 5")
    for row in cursor.fetchall():
        print(f"  📧 {row[0]} / student123")
        
    print("\nParents (sample):")
    cursor.execute("SELECT email FROM parents WHERE email LIKE 'parent%@email.com' LIMIT 5") 
    for row in cursor.fetchall():
        print(f"  📧 {row[0]} / parent123")
    
    conn.close()
    print("\n✅ Sample accounts created successfully!")

if __name__ == "__main__":
    # Check if parents table exists, create if not
    db_path = os.path.join(os.path.dirname(__file__), 'educator_assistant.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create parents table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            student_id INTEGER,
            relationship TEXT DEFAULT 'Parent',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    create_sample_accounts()