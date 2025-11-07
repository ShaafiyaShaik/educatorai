#!/usr/bin/env python3

import sqlite3
import os

# Path to the database
db_path = "educator_assistant.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== EDUCATORS TABLE ===")
    try:
        cursor.execute("SELECT email, first_name, last_name, employee_id FROM educators")
        educators = cursor.fetchall()
        if educators:
            for email, first_name, last_name, employee_id in educators:
                print(f"Email: {email}")
                print(f"Name: {first_name} {last_name}")
                print(f"Employee ID: {employee_id}")
                print("---")
        else:
            print("No educators found in database")
    except Exception as e:
        print(f"Error querying educators: {e}")
    
    conn.close()
else:
    print(f"Database file {db_path} does not exist")