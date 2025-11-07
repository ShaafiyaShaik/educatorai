#!/usr/bin/env python3
"""Check grades table structure specifically"""

import sqlite3
from pathlib import Path

def check_grades_table():
    """Check grades table structure"""
    
    # Database path  
    db_path = Path(__file__).parent / "educator_ai.db"
    
    print(f"🗄️ Checking grades table in: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check grades table structure
        print("\n📊 Grades table structure:")
        cursor.execute("PRAGMA table_info(grades)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   • {col[1]} ({col[2]})")
            
        # Check sample data
        print("\n📈 Sample grades data:")
        cursor.execute("SELECT * FROM grades LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(f"   • {row}")
            
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM grades")
        count = cursor.fetchone()[0]
        print(f"\n📋 Total grades: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Check failed: {e}")

if __name__ == "__main__":
    print("🔍 Grades Table Check")
    print("="*25)
    check_grades_table()