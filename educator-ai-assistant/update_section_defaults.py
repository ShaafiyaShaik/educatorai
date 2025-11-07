import sqlite3

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔧 Setting default values for academic_year and semester...")

# Update all sections to have default values
cursor.execute("""
    UPDATE sections 
    SET academic_year = '2024-25', semester = 'Fall 2024'
    WHERE academic_year IS NULL OR semester IS NULL
""")

rows_updated = cursor.rowcount
print(f"✅ Updated {rows_updated} sections with default values")

# Verify the update
cursor.execute("SELECT id, name, academic_year, semester FROM sections")
sections = cursor.fetchall()

print(f"\n📊 Sections after update:")
for section in sections:
    print(f"  ID: {section[0]} - {section[1]} - {section[2]} - {section[3]}")

conn.commit()
conn.close()

print("\n✅ Section data updated successfully!")