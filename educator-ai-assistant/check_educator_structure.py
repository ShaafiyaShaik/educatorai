import sqlite3

# Connect to the database
conn = sqlite3.connect("educator_assistant.db")
cursor = conn.cursor()

print("🔍 Checking educators table structure...")

# Check table structure
cursor.execute("PRAGMA table_info(educators);")
columns = cursor.fetchall()

print("📋 Educators table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")

print("\n🔍 Checking existing educators...")

# Check educators data
cursor.execute("SELECT * FROM educators LIMIT 5;")
educators = cursor.fetchall()

print(f"\n📊 Found {len(educators)} educators:")
for edu in educators:
    print(f"  Educator: {edu}")

# Check if there's a specific user we can test with
cursor.execute("SELECT id, email, full_name FROM educators WHERE email LIKE '%@%' LIMIT 3;")
test_users = cursor.fetchall()

print(f"\n👤 Test users available:")
for user in test_users:
    print(f"  ID: {user[0]}, Email: {user[1]}, Name: {user[2]}")
    
conn.close()