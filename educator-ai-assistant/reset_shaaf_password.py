"""
Reset password for shaafiya07@gmail.com user
"""
import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.educator import Educator
from app.core.auth import get_password_hash

def reset_shaaf_password():
    """Reset the password for shaafiya07@gmail.com"""
    
    db = next(get_db())
    
    # Find the user
    educator = db.query(Educator).filter(Educator.email == "shaafiya07@gmail.com").first()
    
    if educator:
        print(f"Found educator: {educator.full_name} ({educator.email})")
        
        # Set new password to "password123"
        new_password = "password123"
        hashed_password = get_password_hash(new_password)
        
        educator.hashed_password = hashed_password
        db.commit()
        
        print(f"✅ Password reset to: {new_password}")
        print("You can now login with:")
        print(f"  Email: {educator.email}")
        print(f"  Password: {new_password}")
        
    else:
        print("❌ Educator not found!")
    
    db.close()

if __name__ == "__main__":
    reset_shaaf_password()