"""Restore educator accounts with correct passwords."""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal, init_db
from app.core.auth import get_password_hash
from app.models.educator import Educator

def restore_educators():
    """Restore Ananya, Jennifer, and Nicole with correct passwords."""
    init_db()
    db = SessionLocal()
    
    educators = [
        {
            "email": "ananya.rao@school.com",
            "first_name": "Ananya",
            "last_name": "Rao",
            "password": "Ananya@123"
        },
        {
            "email": "jennifer.educator@school.com",
            "first_name": "Jennifer",
            "last_name": "Smith",
            "password": "Jennifer@123"
        },
        {
            "email": "nicole.educator@school.com",
            "first_name": "Nicole",
            "last_name": "Brown",
            "password": "Nicole@123"
        }
    ]
    
    try:
        for ed_data in educators:
            email = ed_data["email"]
            educator = db.query(Educator).filter(Educator.email == email).first()
            
            if educator:
                print(f"Found existing educator {email} (id={educator.id}), updating password.")
                educator.hashed_password = get_password_hash(ed_data["password"])
                educator.is_active = True
                db.add(educator)
            else:
                print(f"Creating new educator {email}")
                educator = Educator(
                    email=email,
                    first_name=ed_data["first_name"],
                    last_name=ed_data["last_name"],
                    hashed_password=get_password_hash(ed_data["password"]),
                    is_active=True
                )
                db.add(educator)
            
            db.commit()
            db.refresh(educator)
            print(f"✓ Educator {email} ready (id={educator.id})")
    
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✓ All educator accounts restored!")
    print("\nYou can now login with:")
    for ed in educators:
        print(f"  Email: {ed['email']}, Password: {ed['password']}")

if __name__ == "__main__":
    restore_educators()
