#!/usr/bin/env python3
"""
Migrate existing database to add new performance columns
"""
import sqlite3
from datetime import datetime

def migrate_database():
    """Add new columns to existing tables"""
    
    conn = sqlite3.connect('educator_db.sqlite')
    cursor = conn.cursor()
    
    try:
        print("🔄 Migrating database schema...")
        
        # Add exam_id column to grades table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE grades ADD COLUMN exam_id INTEGER")
            print("✅ Added exam_id column to grades table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️  exam_id column already exists in grades table")
            else:
                print(f"❌ Error adding exam_id column: {e}")
        
        # Check if tables exist and create if needed
        tables_to_create = [
            ("exams", """
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    code VARCHAR(50) NOT NULL,
                    exam_date DATE NOT NULL,
                    term VARCHAR(50) NOT NULL,
                    academic_year VARCHAR(20) NOT NULL,
                    total_marks REAL DEFAULT 100.0,
                    passing_marks REAL DEFAULT 60.0,
                    duration_minutes INTEGER DEFAULT 180,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """),
            ("attendance", """
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    present BOOLEAN DEFAULT 0,
                    subject_id INTEGER,
                    period INTEGER,
                    remarks TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id)
                )
            """),
            ("performance_cache", """
                CREATE TABLE IF NOT EXISTS performance_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_id INTEGER,
                    subject_id INTEGER,
                    exam_id INTEGER,
                    term VARCHAR(50),
                    academic_year VARCHAR(20),
                    total_students INTEGER DEFAULT 0,
                    average_score REAL,
                    median_score REAL,
                    highest_score REAL,
                    lowest_score REAL,
                    standard_deviation REAL,
                    pass_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    pass_percentage REAL,
                    average_attendance REAL,
                    metadata_json TEXT,
                    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (section_id) REFERENCES sections(id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id),
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            """),
            ("student_performance_summary", """
                CREATE TABLE IF NOT EXISTS student_performance_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    term VARCHAR(50) NOT NULL,
                    academic_year VARCHAR(20) NOT NULL,
                    overall_average REAL,
                    overall_grade VARCHAR(5),
                    total_credits INTEGER,
                    earned_credits INTEGER,
                    subject_averages TEXT,
                    total_days INTEGER DEFAULT 0,
                    present_days INTEGER DEFAULT 0,
                    attendance_percentage REAL,
                    is_promoted BOOLEAN DEFAULT 0,
                    needs_attention BOOLEAN DEFAULT 0,
                    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (student_id) REFERENCES students(id)
                )
            """)
        ]
        
        for table_name, create_sql in tables_to_create:
            cursor.execute(create_sql)
            print(f"✅ Table '{table_name}' created/verified")
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_subject_date ON attendance(subject_id, date)", 
            "CREATE INDEX IF NOT EXISTS idx_performance_cache_section_subject ON performance_cache(section_id, subject_id, term)",
            "CREATE INDEX IF NOT EXISTS idx_student_performance_term ON student_performance_summary(student_id, term, academic_year)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("✅ Indexes created")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def verify_schema():
    """Verify the database schema after migration"""
    
    conn = sqlite3.connect('educator_db.sqlite')
    cursor = conn.cursor()
    
    # Check if new tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['exams', 'attendance', 'performance_cache', 'student_performance_summary']
    
    print("\n📊 Database Schema Verification:")
    for table in required_tables:
        if table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"✅ {table}: {len(columns)} columns")
        else:
            print(f"❌ {table}: missing")
    
    # Check if grades table has exam_id column
    cursor.execute("PRAGMA table_info(grades)")
    grade_columns = [col[1] for col in cursor.fetchall()]
    
    if 'exam_id' in grade_columns:
        print("✅ grades table has exam_id column")
    else:
        print("❌ grades table missing exam_id column")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    migrate_database()
    verify_schema()
    print("🎉 Migration completed!")