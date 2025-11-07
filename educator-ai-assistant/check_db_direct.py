#!/usr/bin/env python3
"""
Simple database check without stopping server
"""

import sys
sys.path.append('.')
import sqlite3

def check_db():
    print("🗄️ CHECKING DATABASE DIRECTLY")
    print("=" * 40)
    
    # Connect directly to SQLite
    conn = sqlite3.connect('educator_assistant.db')
    cursor = conn.cursor()
    
    # Get all tasks
    cursor.execute("""
        SELECT id, title, description, start_datetime, end_datetime, location, event_type
        FROM schedules 
        WHERE event_type = 'task' 
        ORDER BY start_datetime
    """)
    
    tasks = cursor.fetchall()
    print(f"Found {len(tasks)} tasks:")
    
    for task in tasks:
        print(f"\nTask ID: {task[0]}")
        print(f"Title: {task[1]}")
        print(f"Description: {task[2]}")
        print(f"Start DateTime: {task[3]}")
        print(f"End DateTime: {task[4]}")
        print(f"Location: {task[5]}")
        
        # Parse the datetime to see what date it represents
        start_str = task[3]
        if start_str:
            # Extract just the date part
            date_part = start_str.split('T')[0] if 'T' in start_str else start_str.split(' ')[0]
            print(f"Date Part: {date_part}")
    
    conn.close()

if __name__ == "__main__":
    check_db()