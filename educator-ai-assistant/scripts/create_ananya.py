from app.core.database import engine, SessionLocal
from app.models.educator import Educator
from app.core.auth import get_password_hash

SessionLocal = SessionLocal

def create_ananya():
    db = SessionLocal()
    try:
        existing = db.query(Educator).filter(Educator.email == 'ananya.rao@school.com').first()
        if existing:
            print('ananya already exists', existing.id)
            return
        user = Educator(
            email='ananya.rao@school.com',
            first_name='Ananya',
            last_name='Rao',
            hashed_password=get_password_hash('Ananya@123')
        )
        db.add(user)
        db.commit()
        print('Created ananya.rao@school.com')
    except Exception as e:
        print('Error creating ananya:', e)
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_ananya()
