import sqlite3
import sys
import os

# Add the app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.auth import verify_password, get_password_hash

# Connect to database
conn = sqlite3.connect('educator_db.sqlite')
cursor = conn.cursor()

# Test with the exact password that should work
email = "ananya.rao@school.com"
test_password = "Ananya@123"

# Get the educator
cursor.execute("SELECT email, hashed_password, first_name, last_name, is_active FROM educators WHERE email = ?", (email,))
result = cursor.fetchone()

if result:
    stored_email, stored_hash, first_name, last_name, is_active = result
    
    print(f"Testing login for: {first_name} {last_name}")
    print(f"Email: {stored_email}")
    print(f"Is Active: {is_active}")
    print(f"Password being tested: '{test_password}'")
    print(f"Stored hash starts with: {stored_hash[:20]}...")
    
    # Test the password verification function directly
    print("\nTesting password verification...")
    is_valid = verify_password(test_password, stored_hash)
    print(f"✅ Password valid: {is_valid}")
    
    # Test with wrong password
    is_wrong = verify_password("WrongPassword", stored_hash)
    print(f"❌ Wrong password: {is_wrong}")
    
    # Let's also create a fresh hash and test it
    print(f"\nTesting fresh hash generation...")
    fresh_hash = get_password_hash(test_password)
    is_fresh_valid = verify_password(test_password, fresh_hash)
    print(f"✅ Fresh hash valid: {is_fresh_valid}")
    
    # Compare hashes
    print(f"\nHash comparison:")
    print(f"Stored:  {stored_hash[:60]}...")
    print(f"Fresh:   {fresh_hash[:60]}...")
    
else:
    print(f"❌ No educator found with email: {email}")

conn.close()