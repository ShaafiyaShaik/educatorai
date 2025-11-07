#!/usr/bin/env python3
"""
Check if Ananya has students in her sections
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3

def check_ananya_students():
    """Check Ananya's sections and students directly from database"""
    print("🔍 Checking Ananya's Students in Database")
    print("=" * 50)
    
    try:
        # Connect to the database
        db_path = "educator_db.sqlite"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find Ananya's ID and sections
        cursor.execute("SELECT id, first_name, last_name, email FROM educators WHERE email = ?", ("ananya.rao@school.com",))
        ananya = cursor.fetchone()
        
        if not ananya:
            print("❌ Ananya not found!")
            return
            
        educator_id, first_name, last_name, email = ananya
        print(f"👩‍🏫 Found Educator: {first_name} {last_name} (ID: {educator_id})")
        print(f"   Email: {email}")
        
        # Get Ananya's sections
        cursor.execute("SELECT id, name FROM sections WHERE educator_id = ?", (educator_id,))
        sections = cursor.fetchall()
        
        print(f"\n📚 Ananya's Sections: {len(sections)}")
        
        total_students = 0
        for section_id, section_name in sections:
            print(f"\n   Section: {section_name} (ID: {section_id})")
            
            # Get students in this section
            cursor.execute("""
                SELECT id, student_id, first_name, last_name, email 
                FROM students 
                WHERE section_id = ?
            """, (section_id,))
            students = cursor.fetchall()
            
            print(f"     Actual students found: {len(students)}")
            total_students += len(students)
            
            if students:
                for student_id, student_code, fname, lname, email in students:
                    print(f"       - {student_code}: {fname} {lname} ({email})")
            else:
                print("       ❌ No students found in this section!")
                
        print(f"\n🎯 TOTAL STUDENTS FOR ANANYA: {total_students}")
        
        # Check if there are any students at all
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students_all = cursor.fetchone()[0]
        print(f"📊 Total students in database: {total_students_all}")
        
        # Check section assignments
        cursor.execute("""
            SELECT s.student_id, s.first_name, s.last_name, s.section_id, sec.name, sec.educator_id
            FROM students s
            LEFT JOIN sections sec ON s.section_id = sec.id
            LIMIT 10
        """)
        sample_students = cursor.fetchall()
        
        print(f"\n📋 Sample student-section assignments:")
        for student_id, fname, lname, section_id, section_name, edu_id in sample_students:
            print(f"   {student_id}: {fname} {lname} → Section {section_id} ({section_name}) → Educator {edu_id}")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_ananya_students()