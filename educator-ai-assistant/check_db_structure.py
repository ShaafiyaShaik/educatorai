import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("Tables:", tables)

# Check parents table structure if it exists
if 'parents' in tables:
    print("\nParents table structure:")
    cursor.execute("PRAGMA table_info(parents)")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[2]})")
else:
    print("Parents table does not exist")

conn.close()