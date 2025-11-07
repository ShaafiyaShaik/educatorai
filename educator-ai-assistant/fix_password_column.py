import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔧 Fixing password column name...")

# Rename password_hash to hashed_password to match SQLAlchemy model
cursor.execute("ALTER TABLE educators RENAME COLUMN password_hash TO hashed_password")

print("✅ Column renamed successfully")

# Verify the change
cursor.execute("PRAGMA table_info(educators)")
columns = cursor.fetchall()
print("\nEducators table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()