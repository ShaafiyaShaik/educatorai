#!/usr/bin/env python3
"""
Create new performance tracking tables in the database
"""

from sqlalchemy import create_engine, MetaData
from app.core.database import engine
from app.models.performance import Exam, Attendance, PerformanceCache, StudentPerformanceSummary
from app.core.database import Base
import sqlite3
from datetime import datetime, date

def create_performance_tables():
    """Create the new performance tracking tables"""
    try:
        print("Creating new performance tracking tables...")
        
        # Create all tables (this will only create tables that don't exist)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Performance tables created successfully!")
        
        # Add some sample exam data
        create_sample_exam_data()
        
        print("✅ Sample exam data added!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

def create_sample_exam_data():
    """Create sample exam and attendance data for testing"""
    
    # Connect directly to SQLite to add sample data
    conn = sqlite3.connect('educator_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # Add sample exams
        exams_data = [
            ("Midterm Exam 2025", "MT2025", "2025-03-15", "Spring 2025", "2024-2025", 100.0, 60.0, 180),
            ("Final Exam 2025", "FE2025", "2025-06-15", "Spring 2025", "2024-2025", 100.0, 60.0, 180),
            ("Unit Test 1", "UT1-2025", "2025-02-15", "Spring 2025", "2024-2025", 50.0, 30.0, 90),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO exams 
            (name, code, exam_date, term, academic_year, total_marks, passing_marks, duration_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(exam[0], exam[1], exam[2], exam[3], exam[4], exam[5], exam[6], exam[7], 
               datetime.now().isoformat()) for exam in exams_data])
        
        # Add sample attendance data for all students (assuming student IDs 1-12)
        # Generate attendance for the last 30 days
        from datetime import timedelta
        
        base_date = datetime.now().date() - timedelta(days=30)
        
        for student_id in range(1, 13):  # Students 1-12
            for day_offset in range(30):
                attendance_date = base_date + timedelta(days=day_offset)
                # Simulate 85-95% attendance with some randomness
                import random
                present = random.random() < 0.9  # 90% attendance rate
                
                cursor.execute("""
                    INSERT OR IGNORE INTO attendance 
                    (student_id, date, present, created_at)
                    VALUES (?, ?, ?, ?)
                """, (student_id, attendance_date.isoformat(), present, datetime.now().isoformat()))
        
        # Link existing grades to exams (update grades table)
        cursor.execute("SELECT id FROM exams WHERE code = 'MT2025' LIMIT 1")
        midterm_exam_id = cursor.fetchone()
        if midterm_exam_id:
            midterm_exam_id = midterm_exam_id[0]
            
            # Update some existing grades to link to the midterm exam
            cursor.execute("""
                UPDATE grades 
                SET exam_id = ?
                WHERE exam_id IS NULL 
                LIMIT 10
            """, (midterm_exam_id,))
        
        conn.commit()
        print(f"📊 Added sample attendance data for 30 days")
        print(f"📝 Added {len(exams_data)} sample exams")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def verify_tables():
    """Verify that the new tables were created"""
    
    conn = sqlite3.connect('educator_db.sqlite')
    cursor = conn.cursor()
    
    tables_to_check = ['exams', 'attendance', 'performance_cache', 'student_performance_summary']
    
    for table in tables_to_check:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        result = cursor.fetchone()
        if result:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Table '{table}' exists with {count} records")
        else:
            print(f"❌ Table '{table}' not found")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Setting up enhanced performance tracking...")
    create_performance_tables()
    verify_tables()
    print("🎉 Performance tracking setup completed!")