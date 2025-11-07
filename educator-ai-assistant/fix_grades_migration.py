#!/usr/bin/env python3
"""Add exam_id column to grades table"""

import sqlite3
import os
from pathlib import Path

def add_exam_id_column():
    """Add exam_id column to grades table"""
    
    # Database path
    db_path = Path(__file__).parent / "educator_ai.db"
    
    print(f"🗄️ Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if exam_id column exists
        cursor.execute("PRAGMA table_info(grades)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'exam_id' not in columns:
            print("➕ Adding exam_id column to grades table...")
            cursor.execute("ALTER TABLE grades ADD COLUMN exam_id INTEGER")
            
            # Set default values for existing records
            cursor.execute("""
                UPDATE grades 
                SET exam_id = 1 
                WHERE exam_id IS NULL
            """)
            
            conn.commit()
            print("✅ exam_id column added successfully!")
        else:
            print("✅ exam_id column already exists!")
            
        # Verify the change
        cursor.execute("PRAGMA table_info(grades)")
        columns = cursor.fetchall()
        print("\n📋 Current grades table structure:")
        for col in columns:
            print(f"   • {col[1]} ({col[2]})")
            
        conn.close()
        print("\n🎉 Database migration completed!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("🔧 Database Migration: Adding exam_id to grades table")
    print("="*50)
    add_exam_id_column()