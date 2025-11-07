#!/usr/bin/env python3
"""
Direct Database Initialization Script
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 Initializing database...")
from app.core.database import init_db
init_db()
print("✅ Database initialized!")

# Check what tables were created
import sqlite3
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables created: {tables}")

if 'parents' in tables:
    print("\nParents table structure:")
    cursor.execute("PRAGMA table_info(parents)")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[2]})")

conn.close()