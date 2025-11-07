#!/usr/bin/env python3
"""
Add sample performance data to test the system
"""
import sqlite3
from datetime import datetime, date, timedelta
import random

def add_sample_data():
    """Add sample exams, attendance, and performance data"""
    
    conn = sqlite3.connect('educator_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # Add sample exams
        exams_data = [
            ("Midterm Exam 2025", "MT2025", "2025-03-15", "Spring 2025", "2024-2025", 100.0, 60.0, 180),
            ("Final Exam 2025", "FE2025", "2025-06-15", "Spring 2025", "2024-2025", 100.0, 60.0, 180),
            ("Unit Test 1", "UT1-2025", "2025-02-15", "Spring 2025", "2024-2025", 50.0, 30.0, 90),
        ]
        
        for exam in exams_data:
            cursor.execute("""
                INSERT OR IGNORE INTO exams 
                (name, code, exam_date, term, academic_year, total_marks, passing_marks, duration_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*exam, datetime.now().isoformat()))
        
        print(f"📝 Added {len(exams_data)} sample exams")
        
        # Check how many students we have
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        print(f"👥 Found {student_count} students in database")
        
        if student_count > 0:
            # Add attendance data for the last 30 days
            base_date = datetime.now().date() - timedelta(days=30)
            attendance_added = 0
            
            cursor.execute("SELECT id FROM students")
            student_ids = [row[0] for row in cursor.fetchall()]
            
            for student_id in student_ids:
                for day_offset in range(30):
                    attendance_date = base_date + timedelta(days=day_offset)
                    # Simulate realistic attendance (85-95% attendance)
                    present = random.random() < 0.9
                    
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO attendance 
                            (student_id, date, present, created_at)
                            VALUES (?, ?, ?, ?)
                        """, (student_id, attendance_date.isoformat(), present, datetime.now().isoformat()))
                        attendance_added += 1
                    except sqlite3.IntegrityError:
                        # Record already exists, skip
                        pass
            
            print(f"📊 Added {attendance_added} attendance records")
            
            # Update some existing grades to link to exams
            cursor.execute("SELECT id FROM exams WHERE code = 'MT2025'")
            exam_result = cursor.fetchone()
            if exam_result:
                exam_id = exam_result[0]
                
                # Update grades that don't have an exam_id
                cursor.execute("""
                    UPDATE grades 
                    SET exam_id = ?
                    WHERE exam_id IS NULL
                """, (exam_id,))
                updated_grades = cursor.rowcount
                print(f"🔗 Linked {updated_grades} grades to exams")
        
        conn.commit()
        print("✅ Sample data added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def verify_data():
    """Verify the sample data was added"""
    
    conn = sqlite3.connect('educator_db.sqlite')
    cursor = conn.cursor()
    
    # Check exams
    cursor.execute("SELECT COUNT(*) FROM exams")
    exam_count = cursor.fetchone()[0]
    print(f"📝 Exams in database: {exam_count}")
    
    # Check attendance
    cursor.execute("SELECT COUNT(*) FROM attendance")
    attendance_count = cursor.fetchone()[0]
    print(f"📊 Attendance records: {attendance_count}")
    
    # Check grades with exam links
    cursor.execute("SELECT COUNT(*) FROM grades WHERE exam_id IS NOT NULL")
    linked_grades = cursor.fetchone()[0]
    print(f"🔗 Grades linked to exams: {linked_grades}")
    
    # Show sample data
    cursor.execute("""
        SELECT e.name, COUNT(g.id) as grade_count
        FROM exams e
        LEFT JOIN grades g ON e.id = g.exam_id
        GROUP BY e.id, e.name
    """)
    
    print("\n📋 Exam Summary:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} grades")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Adding sample performance data...")
    add_sample_data()
    verify_data()
    print("🎉 Sample data setup completed!")