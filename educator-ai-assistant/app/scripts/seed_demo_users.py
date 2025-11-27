"""
Seed demo educator accounts (idempotent).

This script creates demo educator accounts if they do not already exist.
It should be run only in development or when explicitly enabled in production
by setting the `SEED_DEMO_USERS` environment variable to `true` on startup.
"""
from app.core.database import SessionLocal
from app.core.auth import get_password_hash
from app.models.educator import Educator

DEMO_EDUCATORS = [
    {"email": "ananya.rao@school.com", "first_name": "Ananya", "last_name": "Rao", "password": "Ananya@123", "is_admin": False},
    {"email": "shaafiya07@gmail.com", "first_name": "Shaafiya", "last_name": "Shaik", "password": "password123", "is_admin": True}
]

def seed_demo_educators():
    db = SessionLocal()
    try:
        for ed in DEMO_EDUCATORS:
            existing = db.query(Educator).filter(Educator.email == ed["email"]).first()
            if existing:
                # update password/hash in case it changed
                existing.hashed_password = get_password_hash(ed["password"])
                existing.first_name = ed["first_name"]
                existing.last_name = ed["last_name"]
                existing.is_admin = ed.get("is_admin", False)
                db.add(existing)
            else:
                new = Educator(
                    email=ed["email"],
                    first_name=ed["first_name"],
                    last_name=ed["last_name"],
                    hashed_password=get_password_hash(ed["password"]),
                    is_active=True,
                    is_admin=ed.get("is_admin", False)
                )
                db.add(new)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_educators()
