import sqlite3
import os

# Connect to the database
db_path = "D:/Projects/agenticai(3)/educator-ai-assistant/educator_assistant.db"

if not os.path.exists(db_path):
    print("❌ Database file not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 Checking database contents...")

# Check if educators table exists and has data
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='educators';")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("✅ Educators table exists")
        
        # Check educators
        cursor.execute("SELECT id, username, email, full_name FROM educators LIMIT 5;")
        educators = cursor.fetchall()
        
        print(f"\n📊 Found {len(educators)} educators:")
        for edu in educators:
            print(f"  ID: {edu[0]}, Username: {edu[1]}, Email: {edu[2]}, Name: {edu[3]}")
            
        if len(educators) == 0:
            print("❌ No educators found in database!")
        else:
            print("\n✅ Educators exist - login should work")
            
    else:
        print("❌ Educators table not found!")
        
except Exception as e:
    print(f"❌ Database error: {e}")

# Check if there are students
try:
    cursor.execute("SELECT COUNT(*) FROM students;")
    student_count = cursor.fetchone()[0]
    print(f"\n📚 Students in database: {student_count}")
    
    cursor.execute("SELECT COUNT(*) FROM sections;")  
    section_count = cursor.fetchone()[0]
    print(f"📂 Sections in database: {section_count}")
    
except Exception as e:
    print(f"❌ Error checking students/sections: {e}")

conn.close()
print("\n" + "="*50)
print("💡 If no educators exist, you may need to create test users.")
print("💡 If educators exist but login fails, check password hashing.")