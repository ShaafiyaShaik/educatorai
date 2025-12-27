"""
Check educator passwords and test authentication
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models.educator import Educator
from app.core.auth import verify_password

db = SessionLocal()

print("=" * 70)
print("CHECKING EDUCATOR AUTHENTICATION")
print("=" * 70)

educators = db.query(Educator).all()

test_credentials = {
    "ananya.rao@school.com": "Ananya@123",
    "jennifer.educator@school.com": "Jennifer@123",
    "nicole.educator@school.com": "Nicole@123",
    "shaaf@gmail.com": "Shaafiya@123"
}

for edu in educators:
    print(f"\n📝 {edu.first_name} {edu.last_name} ({edu.email})")
    print(f"   Password hash exists: {bool(edu.hashed_password)}")
    print(f"   Is active: {edu.is_active}")
    
    # Try to verify password
    if edu.email in test_credentials:
        password = test_credentials[edu.email]
        result = verify_password(password, edu.hashed_password)
        print(f"   Testing password '{password}': {'✅ OK' if result else '❌ WRONG'}")
    else:
        print(f"   No test password defined for this educator")

db.close()
