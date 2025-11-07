import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔧 Adding missing columns to educators table...")

# Add missing columns
missing_columns = [
    ("title", "TEXT"),
    ("office_location", "TEXT"),
    ("is_admin", "BOOLEAN DEFAULT 0"),
    ("notification_preferences", "TEXT"),
    ("timezone", "TEXT DEFAULT 'UTC'"),
    ("communication_preferences", "TEXT"),
    ("last_login", "TIMESTAMP")
]

for column_name, column_type in missing_columns:
    try:
        cursor.execute(f"ALTER TABLE educators ADD COLUMN {column_name} {column_type}")
        print(f"  ✅ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"  ⚠️ Column {column_name} already exists")
        else:
            print(f"  ❌ Error adding {column_name}: {e}")

conn.commit()

# Verify the table structure
cursor.execute("PRAGMA table_info(educators)")
columns = cursor.fetchall()
print(f"\n📊 Updated educators table has {len(columns)} columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
print("\n✅ Database schema updated!")