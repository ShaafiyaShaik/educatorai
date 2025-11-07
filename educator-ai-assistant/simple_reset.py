import sqlite3
import bcrypt
import sys

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def reset_user_password(email: str, new_password: str = "password123"):
    """Reset password for a user directly in the database"""
    
    try:
        # Connect to database
        conn = sqlite3.connect("educator_assistant.db")
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, email, first_name, last_name FROM educators WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User with email {email} not found")
            available_users = cursor.execute("SELECT email FROM educators LIMIT 5").fetchall()
            print("Available users:")
            for u in available_users:
                print(f"  - {u[0]}")
            return False
        
        # Hash the new password
        hashed_password = hash_password(new_password)
        
        # Update password
        cursor.execute(
            "UPDATE educators SET hashed_password = ? WHERE email = ?",
            (hashed_password, email)
        )
        
        conn.commit()
        print(f"✅ Password reset for {user[1]} ({user[2]} {user[3]})")
        print(f"🔑 New password: {new_password}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_simple_test_user():
    """Create a simple test user"""
    
    try:
        conn = sqlite3.connect("educator_assistant.db")
        cursor = conn.cursor()
        
        # Check if test user exists
        cursor.execute("SELECT id FROM educators WHERE email = ?", ("test@test.com",))
        if cursor.fetchone():
            print("✅ Test user already exists: test@test.com")
            reset_user_password("test@test.com", "test123")
            return
            
        # Create new user
        hashed_password = hash_password("test123")
        
        cursor.execute("""
            INSERT INTO educators (
                email, first_name, last_name, hashed_password, 
                is_active, is_admin, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            "test@test.com",
            "Test",
            "User", 
            hashed_password,
            1,  # is_active
            0   # is_admin
        ))
        
        conn.commit()
        print("✅ Test user created!")
        print("📧 Email: test@test.com")
        print("🔑 Password: test123")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")

if __name__ == "__main__":
    print("🔧 Simple Password Reset Tool")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset" and len(sys.argv) > 2:
            email = sys.argv[2]
            password = sys.argv[3] if len(sys.argv) > 3 else "password123"
            reset_user_password(email, password)
        elif sys.argv[1] == "create":
            create_simple_test_user()
        else:
            print("Usage:")
            print("  python simple_reset.py create")
            print("  python simple_reset.py reset <email> [password]")
    else:
        # Default action: reset password for first user and create test user
        print("🔄 Resetting password for existing users...")
        
        # Get list of users
        try:
            conn = sqlite3.connect("educator_assistant.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM educators LIMIT 3")
            users = cursor.fetchall()
            conn.close()
            
            for user_row in users:
                email = user_row[0]
                reset_user_password(email, "password123")
                print()
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*40)
        print("🆕 Creating test user...")
        create_simple_test_user()
        
        print("\n" + "="*40)
        print("✅ READY TO LOGIN!")
        print("Use any of these credentials:")
        print("  📧 Email: test@test.com")
        print("  🔑 Password: test123")
        print("  OR any existing user with password: password123")