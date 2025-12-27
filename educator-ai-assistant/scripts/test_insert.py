#!/usr/bin/env python
import sqlite3

c = sqlite3.connect('educator_db.sqlite')
cur = c.cursor()

# Test manual insert
try:
    cur.execute('''
        INSERT INTO students (id, student_id, first_name, last_name, email, section_id, is_active, created_at, updated_at)
        VALUES (999, 'STU999', 'Test', 'Student', 'test@test.com', 1, 1, '2024-01-01', '2024-01-01')
    ''')
    c.commit()
    print("Manual insert successful")
except Exception as e:
    print(f"Manual insert failed: {e}")

# Check count
cur.execute('SELECT COUNT(*) FROM students')
print(f"Total students after insert: {cur.fetchone()[0]}")

c.close()
