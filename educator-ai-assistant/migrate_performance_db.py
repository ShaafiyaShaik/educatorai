#!/usr/bin/env python3
"""Migrate database to add missing columns for performance tracking"""

import sqlite3
from pathlib import Path

def migrate_database():
    """Add missing columns to existing tables"""
    
    # Database path
    db_path = Path(__file__).parent / "educator_ai.db"
    
    print(f"🗄️ Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current grades table structure
        cursor.execute("PRAGMA table_info(grades)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Current grades columns: {columns}")
        
        # Add exam_id column if it doesn't exist
        if 'exam_id' not in columns:
            print("➕ Adding exam_id column to grades table...")
            cursor.execute("ALTER TABLE grades ADD COLUMN exam_id INTEGER")
            
            # Set default exam_id for existing records  
            cursor.execute("UPDATE grades SET exam_id = 1 WHERE exam_id IS NULL")
            print("✅ exam_id column added!")
        else:
            print("✅ exam_id column already exists!")
            
        # Create exams table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exams'")
        if not cursor.fetchone():
            print("📝 Creating exams table...")
            cursor.execute("""
                CREATE TABLE exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    subject_id INTEGER NOT NULL,
                    section_id INTEGER NOT NULL,
                    exam_date DATE NOT NULL,
                    total_marks INTEGER NOT NULL,
                    exam_type VARCHAR(50) DEFAULT 'regular',
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES subjects (id),
                    FOREIGN KEY (section_id) REFERENCES sections (id)
                )
            """)
            
            # Insert sample exams
            cursor.execute("""
                INSERT INTO exams (name, subject_id, section_id, exam_date, total_marks, exam_type, description)
                VALUES 
                    ('Mid-term Mathematics', 1, 1, '2024-01-15', 100, 'midterm', 'First semester midterm examination'),
                    ('Final Science Exam', 2, 1, '2024-02-20', 100, 'final', 'Second semester final examination'),
                    ('Quiz - English', 3, 1, '2024-01-30', 50, 'quiz', 'Weekly English quiz')
            """)
            print("✅ Exams table created with sample data!")
        else:
            print("✅ Exams table already exists!")
            
        # Create attendance table if it doesn't exist  
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'")
        if not cursor.fetchone():
            print("📅 Creating attendance table...")
            cursor.execute("""
                CREATE TABLE attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    section_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    attendance_date DATE NOT NULL,
                    is_present BOOLEAN NOT NULL DEFAULT TRUE,
                    remarks TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (section_id) REFERENCES sections (id),
                    FOREIGN KEY (subject_id) REFERENCES subjects (id)
                )
            """)
            print("✅ Attendance table created!")
        else:
            print("✅ Attendance table already exists!")
            
        # Create performance_cache table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='performance_cache'")
        if not cursor.fetchone():
            print("📊 Creating performance_cache table...")
            cursor.execute("""
                CREATE TABLE performance_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    cache_data TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Performance cache table created!")
        else:
            print("✅ Performance cache table already exists!")
            
        conn.commit()
        conn.close()
        
        print("\n🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Database Migration")
    print("="*20)
    migrate_database()