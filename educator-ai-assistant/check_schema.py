#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('educator_assistant.db')
cursor = conn.cursor()

# Get the schema for educators table
cursor.execute("PRAGMA table_info(educators)")
columns = cursor.fetchall()
print("Educators table schema:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()