import sqlite3
import bcrypt

def create_fresh_test_user():
    """Create a completely fresh test user"""
    
    conn = sqlite3.connect("educator_assistant.db")
    cursor = conn.cursor()
    
    # Delete existing test user if any
    cursor.execute("DELETE FROM educators WHERE email = ?", ("testuser@test.com",))
    
    # Create completely new user with fresh hash
    password = "testpass"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    cursor.execute("""
        INSERT INTO educators (
            email, first_name, last_name, hashed_password, 
            is_active, is_admin, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        "testuser@test.com",
        "Fresh",
        "User",
        password_hash.decode('utf-8'),
        1,  # is_active = True
        0   # is_admin = False
    ))
    
    conn.commit()
    conn.close()
    
    print("✅ Created fresh user:")
    print("📧 Email: testuser@test.com")
    print("🔑 Password: testpass")
    
    return "testuser@test.com", "testpass"

# Also test existing users with different passwords
def test_multiple_logins():
    """Test multiple login combinations"""
    
    import requests
    
    # Test combinations
    test_users = [
        ("testuser@test.com", "testpass"),
        ("test@test.com", "test123"), 
        ("shaaf@gmail.com", "password123"),
        ("teacher1@example.com", "password123")
    ]
    
    BASE_URL = "http://localhost:8001"
    
    for email, password in test_users:
        print(f"\n🔐 Testing: {email} / {password}")
        
        login_data = {
            "username": email,
            "password": password
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/educators/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! Use {email} / {password}")
                return email, password
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None, None

if __name__ == "__main__":
    print("🔧 Creating fresh test user...")
    create_fresh_test_user()
    
    print("\n🧪 Testing login combinations...")
    working_email, working_pass = test_multiple_logins()
    
    if working_email:
        print(f"\n🎉 WORKING CREDENTIALS FOUND:")
        print(f"📧 Email: {working_email}")
        print(f"🔑 Password: {working_pass}")
    else:
        print(f"\n❌ None of the test combinations worked.")
        print("💡 There might be an issue with the authentication system.")