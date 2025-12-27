"""
Update educator passwords in PostgreSQL
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models.educator import Educator
from app.core.auth import get_password_hash

db = SessionLocal()

print("=" * 70)
print("UPDATING EDUCATOR PASSWORDS")
print("=" * 70)

educators_to_update = {
    "jennifer.educator@school.com": "Jennifer@123",
    "nicole.educator@school.com": "Nicole@123",
    "shaaf@gmail.com": "Shaafiya@123"
}

for email, password in educators_to_update.items():
    educator = db.query(Educator).filter(Educator.email == email).first()
    if educator:
        educator.hashed_password = get_password_hash(password)
        db.commit()
        print(f"✅ Updated {educator.first_name} {educator.last_name} ({email})")
        print(f"   New password: {password}")
    else:
        print(f"❌ Educator not found: {email}")

db.close()

print("\n" + "=" * 70)
print("✅ PASSWORD UPDATES COMPLETE")
print("=" * 70)
