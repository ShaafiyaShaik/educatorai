from app.core.database import get_db
from app.models.educator import Educator
from app.core.auth import get_password_hash
from sqlalchemy.orm import Session
import sys

def create_test_educator():
    """Create a test educator with known credentials"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if test user already exists
        existing = db.query(Educator).filter(Educator.email == "test@educator.com").first()
        if existing:
            print("✅ Test user already exists!")
            print("📧 Email: test@educator.com")
            print("🔑 Password: testpass123")
            return
        
        # Create new test educator
        hashed_password = get_password_hash("testpass123")
        
        test_educator = Educator(
            email="test@educator.com",
            first_name="Test",
            last_name="Educator",
            employee_id="TEST001",
            department="Computer Science",
            title="Test Teacher",
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False
        )
        
        db.add(test_educator)
        db.commit()
        
        print("✅ Test educator created successfully!")
        print("📧 Email: test@educator.com")
        print("🔑 Password: testpass123")
        print("💡 Use these credentials to login")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test educator: {e}")
    finally:
        db.close()

def reset_existing_user_password(email: str, new_password: str = "password123"):
    """Reset password for an existing user"""
    
    db = next(get_db())
    
    try:
        educator = db.query(Educator).filter(Educator.email == email).first()
        if not educator:
            print(f"❌ User with email {email} not found")
            return False
            
        # Update password
        educator.hashed_password = get_password_hash(new_password)
        db.commit()
        
        print(f"✅ Password reset for {email}")
        print(f"🔑 New password: {new_password}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting password: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 User Management Tool")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "reset" and len(sys.argv) > 2:
            email = sys.argv[2]
            password = sys.argv[3] if len(sys.argv) > 3 else "password123"
            reset_existing_user_password(email, password)
        elif action == "create":
            create_test_educator()
        else:
            print("Usage:")
            print("  python manage_users.py create")
            print("  python manage_users.py reset <email> [password]")
    else:
        # Default: create test user
        create_test_educator()
        
        # Also reset password for the first user found
        db = next(get_db())
        first_user = db.query(Educator).first()
        if first_user:
            print(f"\n🔄 Also resetting password for {first_user.email}")
            reset_existing_user_password(first_user.email, "password123")
        db.close()