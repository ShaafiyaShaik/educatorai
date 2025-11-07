import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔧 Fixing user profile data for Ananya...")

# Update Ananya's profile with proper title and subject
cursor.execute("""
    UPDATE educators 
    SET title = 'Senior Mathematics Teacher',
        subject = 'Mathematics'
    WHERE email = 'ananya.rao@school.com'
""")

rows_updated = cursor.rowcount
print(f"✅ Updated {rows_updated} educator profile(s)")

# Verify the update
cursor.execute("""
    SELECT id, email, first_name, last_name, title, subject 
    FROM educators WHERE email = 'ananya.rao@school.com'
""")
educator = cursor.fetchone()

print(f"\n✅ Updated profile:")
print(f"  Name: {educator[2]} {educator[3]}")
print(f"  Email: {educator[1]}")
print(f"  Title: {educator[4]}")
print(f"  Subject: {educator[5]}")

conn.commit()
conn.close()

print("\n✅ Profile update completed!")