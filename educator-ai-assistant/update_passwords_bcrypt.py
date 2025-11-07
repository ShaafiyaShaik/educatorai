import sqlite3
import sys
import os

# Add the app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.auth import get_password_hash

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

print("🔧 Updating password hashes to use bcrypt...")

# Update teacher passwords
teachers = [
    ("ananya.rao@school.com", "Ananya@123"),
    ("kiran.verma@school.com", "Kiran@123"), 
    ("neha.singh@school.com", "Neha@123")
]

for email, password in teachers:
    hashed = get_password_hash(password)
    cursor.execute("UPDATE educators SET hashed_password = ? WHERE email = ?", (hashed, email))
    print(f"  ✅ Updated password for {email}")

# Update student passwords  
cursor.execute("SELECT student_id, email FROM students WHERE student_id LIKE 'S%'")
students = cursor.fetchall()

for student_id, email in students:
    # Use student_id as password (e.g., S101 -> S101@123)
    password = f"{student_id}@123"
    hashed = get_password_hash(password)
    cursor.execute("UPDATE students SET password_hash = ? WHERE email = ?", (hashed, email))
    print(f"  ✅ Updated password for {email} -> {password}")

# Update parent passwords
cursor.execute("SELECT email FROM parents WHERE email LIKE '%.p%@school.com'")
parent_emails = cursor.fetchall()

for (email,) in parent_emails:
    # Extract parent name from email (e.g., arvind.p101@school.com -> Arvind@123)
    parent_name = email.split('.')[0].capitalize()
    password = f"{parent_name}@123"
    hashed = get_password_hash(password)
    cursor.execute("UPDATE parents SET password_hash = ? WHERE email = ?", (hashed, email))
    print(f"  ✅ Updated password for {email} -> {password}")

conn.commit()
conn.close()

print("\n✅ All passwords updated to use bcrypt hashing!")
print("\n🔑 Updated Login Credentials:")
print("👨‍🏫 Teachers:")
print("   ananya.rao@school.com - Password: Ananya@123")
print("   kiran.verma@school.com - Password: Kiran@123") 
print("   neha.singh@school.com - Password: Neha@123")