import sqlite3
import sys
import os

# Add the app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.auth import verify_password, get_password_hash

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

# Check if the educator exists
email = "ananya.rao@school.com"
password = "Ananya@123"

cursor.execute("SELECT email, hashed_password, first_name, last_name, is_active FROM educators WHERE email = ?", (email,))
result = cursor.fetchone()

if result:
    print(f"✅ Found educator: {result[2]} {result[3]}")
    print(f"   Email: {result[0]}")
    print(f"   Is Active: {result[4]}")
    print(f"   Stored Hash: {result[1][:50]}...")
    
    # Test password verification
    is_valid = verify_password(password, result[1])
    print(f"   Password verification: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    # Generate new hash for comparison
    new_hash = get_password_hash(password)
    print(f"   New hash would be: {new_hash[:50]}...")
    
    # Test new hash
    is_new_valid = verify_password(password, new_hash)
    print(f"   New hash verification: {'✅ VALID' if is_new_valid else '❌ INVALID'}")
    
else:
    print(f"❌ Educator not found with email: {email}")

conn.close()