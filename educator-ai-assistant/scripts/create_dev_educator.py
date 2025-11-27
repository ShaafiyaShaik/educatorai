"""Utility to create or update a local educator account and print a Bearer token.

Usage (from project root):
  python scripts/create_dev_educator.py

This script is intended for local development only. It will initialize the
database (create tables), create or update an educator with a known email and
password, and print a JWT access token you can use with Authorization: Bearer <token>.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import app` works when running this
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db, SessionLocal
from app.core.auth import get_password_hash, create_access_token
from app.models.educator import Educator


def main():
    init_db()
    db = SessionLocal()

    email = "you@example.com"
    password = "StrongPassword123!"

    educator = db.query(Educator).filter(Educator.email == email).first()
    if educator:
        print(f"Found existing educator {email} (id={educator.id}), updating password.")
        educator.hashed_password = get_password_hash(password)
        db.add(educator)
        db.commit()
    else:
        educator = Educator(
            email=email,
            first_name="Your",
            last_name="Name",
            # Some DB schemas require employee_id to be non-null; set a dev id.
            employee_id="DEV-001",
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db.add(educator)
        db.commit()
        db.refresh(educator)
        print(f"Created educator {email} with id={educator.id}")

    token = create_access_token({"sub": educator.email})
    print("\nUse this token in requests as: Authorization: Bearer <token>\n")
    print(token)


if __name__ == "__main__":
    main()
