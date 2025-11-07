"""
Comprehensive login test and user verification
"""
import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.core.auth import verify_password, get_password_hash

def verify_user_and_fix():
    """Verify the user exists and fix password if needed"""
    
    db = next(get_db())
    
    # Check all educators
    educators = db.query(Educator).all()
    print("=== ALL EDUCATORS ===")
    for edu in educators:
        print(f"ID: {edu.id}, Email: {edu.email}, Name: {edu.full_name}")
        
        # Test password
        if edu.email == "shaafiya07@gmail.com":
            print(f"\n=== TESTING shaafiya07@gmail.com ===")
            print(f"Stored hash: {edu.hashed_password[:50]}...")
            
            # Test common passwords
            passwords = ["password123", "shaaf123", "admin", "123456"]
            for pwd in passwords:
                try:
                    if verify_password(pwd, edu.hashed_password):
                        print(f"✅ Password '{pwd}' WORKS!")
                        db.close()
                        return pwd
                    else:
                        print(f"❌ Password '{pwd}' failed")
                except Exception as e:
                    print(f"❌ Error testing '{pwd}': {e}")
            
            # If no password works, reset it
            print(f"\n🔧 Resetting password to 'password123'...")
            new_hash = get_password_hash("password123")
            edu.hashed_password = new_hash
            db.commit()
            print(f"✅ Password reset complete!")
            
            db.close()
            return "password123"
    
    print("❌ shaafiya07@gmail.com not found!")
    db.close()
    return None

if __name__ == "__main__":
    result = verify_user_and_fix()
    if result:
        print(f"\n🎉 LOGIN CREDENTIALS:")
        print(f"Email: shaafiya07@gmail.com")
        print(f"Password: {result}")
    else:
        print("❌ Unable to set up login credentials")