#!/usr/bin/env python3
"""
Delete sample accounts and create proper teacher, student, and parent accounts
"""

import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables_if_not_exist(cursor):
    """Create tables if they don't exist"""
    print("🏗️ Creating database tables...")
    
    # Create educators table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS educators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            department TEXT,
            subject TEXT,
            hire_date DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create sections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade TEXT,
            subject TEXT,
            educator_id INTEGER,
            capacity INTEGER DEFAULT 30,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (educator_id) REFERENCES educators (id)
        )
    """)
    
    # Create students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            roll_number TEXT,
            section_id INTEGER,
            phone TEXT,
            date_of_birth DATE,
            address TEXT,
            guardian_email TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (section_id) REFERENCES sections (id)
        )
    """)
    
    # Create parents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            student_id INTEGER,
            relationship TEXT DEFAULT 'Parent',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    
    print("✅ Database tables created")

def clean_and_create_accounts():
    """Clean existing sample accounts and create new structured accounts"""
    conn = sqlite3.connect('educator_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # Create tables first
        create_tables_if_not_exist(cursor)
        
        print("🧹 Cleaning up existing sample accounts...")
        
        # Delete sample accounts (keep original accounts)
        cursor.execute("DELETE FROM students WHERE email LIKE 'student%@%'")
        cursor.execute("DELETE FROM parents WHERE email LIKE 'parent%@%'")
        cursor.execute("DELETE FROM sections WHERE id >= 19")  # Remove sections created by sample script
        cursor.execute("DELETE FROM educators WHERE email LIKE 'teacher%@%'")
        
        print("✅ Sample accounts cleaned up")
        
        # Create the 3 teachers
        print("👨‍🏫 Creating teachers...")
        teachers_data = [
            ("ananya.rao@school.com", hash_password("Ananya@123"), "Ananya", "Rao", "Mathematics", "T101", datetime.now(), datetime.now()),
            ("kiran.verma@school.com", hash_password("Kiran@123"), "Kiran", "Verma", "Science", "T102", datetime.now(), datetime.now()),
            ("neha.singh@school.com", hash_password("Neha@123"), "Neha", "Singh", "English", "T103", datetime.now(), datetime.now())
        ]
        
        cursor.executemany("""
            INSERT INTO educators (email, password_hash, first_name, last_name, department, employee_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, teachers_data)
        
        # Get teacher IDs
        cursor.execute("SELECT id, employee_id, first_name, last_name FROM educators WHERE employee_id IN ('T101', 'T102', 'T103')")
        teachers = cursor.fetchall()
        teacher_dict = {row[1]: row[0] for row in teachers}  # {employee_id: educator_id}
        
        print("📚 Creating sections...")
        sections_data = [
            ("Mathematics Section A", teacher_dict["T101"], datetime.now(), datetime.now()),
            ("Mathematics Section B", teacher_dict["T101"], datetime.now(), datetime.now()),
            ("Science Section A", teacher_dict["T102"], datetime.now(), datetime.now()),
            ("Science Section B", teacher_dict["T102"], datetime.now(), datetime.now()),
            ("English Section A", teacher_dict["T103"], datetime.now(), datetime.now()),
            ("English Section B", teacher_dict["T103"], datetime.now(), datetime.now()),
        ]
        
        cursor.executemany("""
            INSERT INTO sections (name, educator_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, sections_data)
        
        # Get section IDs
        cursor.execute("""
            SELECT s.id, s.name, e.employee_id 
            FROM sections s 
            JOIN educators e ON s.educator_id = e.id 
            WHERE e.employee_id IN ('T101', 'T102', 'T103')
            ORDER BY e.employee_id, s.name
        """)
        sections = cursor.fetchall()
        
        # Map sections for easy access
        section_map = {}
        for section_id, section_name, employee_id in sections:
            if "Mathematics Section A" in section_name:
                section_map[("T101", "A")] = section_id
            elif "Mathematics Section B" in section_name:
                section_map[("T101", "B")] = section_id
            elif "Science Section A" in section_name:
                section_map[("T102", "A")] = section_id
            elif "Science Section B" in section_name:
                section_map[("T102", "B")] = section_id
            elif "English Section A" in section_name:
                section_map[("T103", "A")] = section_id
            elif "English Section B" in section_name:
                section_map[("T103", "B")] = section_id
        
        print("👨‍🎓 Creating students...")
        students_data = [
            # T101 - Mathematics - Ms. Ananya Rao
            ("S101", "Rahul", "Sharma", "rahul.s101@school.com", hash_password("Rahul@123"), 101, section_map[("T101", "A")], datetime.now(), datetime.now()),
            ("S102", "Priya", "Mehta", "priya.s102@school.com", hash_password("Priya@123"), 102, section_map[("T101", "A")], datetime.now(), datetime.now()),
            ("S103", "Arjun", "Das", "arjun.s103@school.com", hash_password("Arjun@123"), 103, section_map[("T101", "B")], datetime.now(), datetime.now()),
            ("S104", "Sneha", "Iyer", "sneha.s104@school.com", hash_password("Sneha@123"), 104, section_map[("T101", "B")], datetime.now(), datetime.now()),
            
            # T102 - Science - Mr. Kiran Verma
            ("S201", "Meera", "Nair", "meera.s201@school.com", hash_password("Meera@123"), 201, section_map[("T102", "A")], datetime.now(), datetime.now()),
            ("S202", "Rohan", "Gupta", "rohan.s202@school.com", hash_password("Rohan@123"), 202, section_map[("T102", "A")], datetime.now(), datetime.now()),
            ("S203", "Isha", "Reddy", "isha.s203@school.com", hash_password("Isha@123"), 203, section_map[("T102", "B")], datetime.now(), datetime.now()),
            ("S204", "Dev", "Patel", "dev.s204@school.com", hash_password("Dev@123"), 204, section_map[("T102", "B")], datetime.now(), datetime.now()),
            
            # T103 - English - Mrs. Neha Singh
            ("S301", "Aditya", "Jain", "aditya.s301@school.com", hash_password("Aditya@123"), 301, section_map[("T103", "A")], datetime.now(), datetime.now()),
            ("S302", "Diya", "Rao", "diya.s302@school.com", hash_password("Diya@123"), 302, section_map[("T103", "A")], datetime.now(), datetime.now()),
            ("S303", "Karthik", "Menon", "karthik.s303@school.com", hash_password("Karthik@123"), 303, section_map[("T103", "B")], datetime.now(), datetime.now()),
            ("S304", "Tanya", "Paul", "tanya.s304@school.com", hash_password("Tanya@123"), 304, section_map[("T103", "B")], datetime.now(), datetime.now()),
        ]
        
        cursor.executemany("""
            INSERT INTO students (student_id, first_name, last_name, email, password_hash, roll_number, section_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, students_data)
        
        print("👨‍👩‍👧‍👦 Creating parents...")
        parents_data = [
            # T101 - Mathematics
            ("arvind.p101@school.com", hash_password("Arvind@123"), "Arvind", "Sharma", "9876543210", datetime.now()),
            ("kavita.p102@school.com", hash_password("Kavita@123"), "Kavita", "Mehta", "9876543211", datetime.now()),
            ("rakesh.p103@school.com", hash_password("Rakesh@123"), "Rakesh", "Das", "9876543212", datetime.now()),
            ("revathi.p104@school.com", hash_password("Revathi@123"), "Revathi", "Iyer", "9876543213", datetime.now()),
            
            # T102 - Science
            ("divya.p201@school.com", hash_password("Divya@123"), "Divya", "Nair", "9876543220", datetime.now()),
            ("manish.p202@school.com", hash_password("Manish@123"), "Manish", "Gupta", "9876543221", datetime.now()),
            ("sunitha.p203@school.com", hash_password("Sunitha@123"), "Sunitha", "Reddy", "9876543222", datetime.now()),
            ("hitesh.p204@school.com", hash_password("Hitesh@123"), "Hitesh", "Patel", "9876543223", datetime.now()),
            
            # T103 - English
            ("mohan.p301@school.com", hash_password("Mohan@123"), "Mohan", "Jain", "9876543230", datetime.now()),
            ("anjali.p302@school.com", hash_password("Anjali@123"), "Anjali", "Rao", "9876543231", datetime.now()),
            ("rajesh.p303@school.com", hash_password("Rajesh@123"), "Rajesh", "Menon", "9876543232", datetime.now()),
            ("sneha.p304@school.com", hash_password("Sneha@123"), "Sneha", "Paul", "9876543233", datetime.now()),
        ]
        
        cursor.executemany("""
            INSERT INTO parents (email, password_hash, first_name, last_name, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, parents_data)
        
        print("🔗 Linking parents to students...")
        
        # Get student IDs for linking
        cursor.execute("SELECT id, student_id FROM students WHERE student_id LIKE 'S%'")
        students_dict = {row[1]: row[0] for row in cursor.fetchall()}  # {student_id: id}
        
        # Update parents with their corresponding student_id
        parent_student_links = [
            # T101 - Mathematics  
            ("arvind.p101@school.com", students_dict["S101"]),
            ("kavita.p102@school.com", students_dict["S102"]),
            ("rakesh.p103@school.com", students_dict["S103"]),
            ("revathi.p104@school.com", students_dict["S104"]),
            
            # T102 - Science
            ("divya.p201@school.com", students_dict["S201"]),
            ("manish.p202@school.com", students_dict["S202"]),
            ("sunitha.p203@school.com", students_dict["S203"]),
            ("hitesh.p204@school.com", students_dict["S204"]),
            
            # T103 - English
            ("mohan.p301@school.com", students_dict["S301"]),
            ("anjali.p302@school.com", students_dict["S302"]),
            ("rajesh.p303@school.com", students_dict["S303"]),
            ("sneha.p304@school.com", students_dict["S304"]),
        ]
        
        for parent_email, student_id in parent_student_links:
            cursor.execute("""
                UPDATE parents SET student_id = ? WHERE email = ?
            """, (student_id, parent_email))
        
        conn.commit()
        
        print(f"\n✅ Successfully created structured accounts:")
        print(f"   👨‍🏫 3 Teachers (Mathematics, Science, English)")
        print(f"   📚 6 Sections (2 per teacher)")
        print(f"   👨‍🎓 12 Students (4 per teacher, 2 per section)")
        print(f"   👨‍👩‍👧‍👦 12 Parents (1 per student)")
        print(f"   🔗 12 Parent-student relationships")
        
        print(f"\n🔑 Teacher Login Credentials:")
        print(f"   📧 ananya.rao@school.com - Password: Ananya@123")
        print(f"   📧 kiran.verma@school.com - Password: Kiran@123")
        print(f"   📧 neha.singh@school.com - Password: Neha@123")
        
        print(f"\n🎓 Student accounts created with individual passwords")
        print(f"💑 Parent accounts created with individual passwords")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_and_create_accounts()