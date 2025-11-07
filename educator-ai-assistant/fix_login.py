import sqlite3
import bcrypt

def check_and_fix_user():
    """Check the test user and fix password if needed"""
    
    conn = sqlite3.connect("educator_assistant.db")
    cursor = conn.cursor()
    
    print("🔍 Checking test user...")
    
    # Check if test user exists
    cursor.execute("SELECT id, email, first_name, last_name, hashed_password FROM educators WHERE email = ?", 
                   ("test@test.com",))
    user = cursor.fetchone()
    
    if user:
        print(f"✅ User found: {user[1]} ({user[2]} {user[3]})")
        print(f"🔑 Current hash: {user[4][:50]}...")
        
        # Test the current password
        try:
            stored_hash = user[4].encode('utf-8')
            test_password = "test123".encode('utf-8')
            
            if bcrypt.checkpw(test_password, stored_hash):
                print("✅ Password 'test123' works correctly!")
                return True
            else:
                print("❌ Password 'test123' doesn't match. Fixing...")
                
        except Exception as e:
            print(f"❌ Error checking password: {e}. Creating new hash...")
        
        # Create new password hash
        new_hash = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute("UPDATE educators SET hashed_password = ? WHERE email = ?", 
                      (new_hash.decode('utf-8'), "test@test.com"))
        conn.commit()
        
        print("✅ Password updated to 'test123'")
        
    else:
        print("❌ Test user not found. Creating...")
        
        # Create new user
        password_hash = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute("""
            INSERT INTO educators (
                email, first_name, last_name, hashed_password, 
                is_active, is_admin, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            "test@test.com",
            "Test", 
            "Teacher",
            password_hash.decode('utf-8'),
            1,
            0
        ))
        
        conn.commit()
        print("✅ Test user created!")
    
    conn.close()
    
    # Also check other users and reset their passwords
    print("\n🔄 Resetting passwords for other users...")
    
    conn = sqlite3.connect("educator_assistant.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email FROM educators WHERE email != ?", ("test@test.com",))
    other_users = cursor.fetchall()
    
    password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
    
    for user_id, email in other_users:
        cursor.execute("UPDATE educators SET hashed_password = ? WHERE id = ?", 
                      (password_hash.decode('utf-8'), user_id))
        print(f"  ✅ Reset password for {email} to 'password123'")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("✅ FIXED! Try these credentials:")
    print("📧 Email: test@test.com") 
    print("🔑 Password: test123")
    print("")
    print("Alternative users (password: password123):")
    for _, email in other_users:
        print(f"📧 {email}")

if __name__ == "__main__":
    check_and_fix_user()