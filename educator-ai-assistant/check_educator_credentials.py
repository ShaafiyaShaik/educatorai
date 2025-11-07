"""
Check educator credentials and test login
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.educator import Educator
from app.core.auth import verify_password

def check_educators():
    """Check what educators exist and test passwords"""
    db = next(get_db())
    
    try:
        print("👥 CHECKING EDUCATORS")
        print("=" * 40)
        
        educators = db.query(Educator).all()
        
        if not educators:
            print("❌ No educators found!")
            return
        
        for i, educator in enumerate(educators):
            print(f"\n{i+1}. {educator.first_name} {educator.last_name}")
            print(f"   Email: {educator.email}")
            print(f"   Active: {educator.is_active}")
            print(f"   Has password hash: {'Yes' if educator.hashed_password else 'No'}")
            
            # Test common passwords
            common_passwords = [
                f"{educator.first_name.lower()}123",
                f"{educator.first_name.lower()}{educator.last_name.lower()}",
                "password123",
                "admin123",
                "123456"
            ]
            
            for password in common_passwords:
                try:
                    if verify_password(password, educator.hashed_password):
                        print(f"   ✅ Password found: {password}")
                        return educator.email, password
                except:
                    pass
            
            print("   ❌ No common password worked")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    return None, None

if __name__ == "__main__":
    email, password = check_educators()
    if email and password:
        print(f"\n🎯 Try login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
    else:
        print("\n❌ No working credentials found")