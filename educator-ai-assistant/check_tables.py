import sqlite3

conn = sqlite3.connect("educator_assistant.db")
cursor = conn.cursor()

print("🔍 Checking table structures...")

tables = ["subjects", "sections", "students", "grades"]

for table in tables:
    print(f"\n📋 {table.upper()} table:")
    cursor.execute(f"PRAGMA table_info({table});")
    columns = cursor.fetchall()
    
    if columns:
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
    else:
        print(f"  ❌ Table {table} does not exist")

conn.close()