import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("📊 Checking educator emails in database:")
print("=====================================")

# Check all educators
cursor.execute("SELECT email, first_name, last_name, employee_id, is_active FROM educators")
educators = cursor.fetchall()

if educators:
    print(f"Found {len(educators)} educators:")
    for educator in educators:
        print(f"  📧 {educator[0]} - {educator[1]} {educator[2]} ({educator[3]}) - Active: {educator[4]}")
else:
    print("❌ No educators found in database!")

print("\n🔍 Specifically checking for ananya.rao@school.com:")
cursor.execute("SELECT * FROM educators WHERE email = ?", ("ananya.rao@school.com",))
result = cursor.fetchone()

if result:
    print("✅ Found!")
    print(f"   ID: {result[0]}")
    print(f"   Email: {result[4]}")
    print(f"   Name: {result[2]} {result[3]}")
else:
    print("❌ Not found!")

conn.close()